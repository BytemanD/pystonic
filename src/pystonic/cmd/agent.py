import asyncio
import contextlib

import click
from openai import APIConnectionError
from rich.console import Console
from rich.prompt import Prompt
from rich.rule import Rule
from rich.text import Text

from pystonic.agents.langchain_agent.agent import AsyncAgent, get_checkpointer_saver
from pystonic.agents.langchain_agent.objects import RuntimeContext

# from pystonic.agents.langchain_agent.tools import sqlite
# from pystonic.agents.langchain_agent.tools import builtin
from pystonic.agents.langchain_agent.tools import builtin
from pystonic.common.conf import CONF
from pystonic.orm import database
from pystonic.pretty import output
from pystonic.utils.dateutil import utcnow


@contextlib.asynccontextmanager
async def get_agent():
    async with get_checkpointer_saver() as saver:
        yield AsyncAgent(saver)


@click.group("agent")
def root():
    database.create_all_tables()


@root.group()
def session():
    """agent sessions"""


async def _list_sessions():
    async with get_agent() as agent:
        sessions = agent.list_session()
        output.print_models(sessions, fields=["created_at", "uuid", "title"])


async def _delete_session(session_ids: list[str]):
    async with get_agent() as agent:
        for session_id in session_ids:
            agent.delete_session(session_id)


@session.command("list")
def list_sesions():
    """List agent sessions."""
    asyncio.run(_list_sessions())


@session.command("delete")
@click.argument("sessions", required=False, nargs=-1)
def delete_session(sessions: list[str]):
    """List agent sessions."""
    asyncio.run(_delete_session(sessions))


async def _agent_astream(agent: AsyncAgent, intput: str, session_id: str):
    ctx = RuntimeContext(
        providers=CONF.agent.providers,
        thread_id=session_id,
        tools=builtin.WorkToolkit().get_tools(),
    )
    reasoning = False
    async for event in agent.astream(ctx, intput):
        reasoning_content = event.additional_kwargs.get("reasoning_content")
        if reasoning_content:
            reasoning = True
            click.secho(reasoning_content, fg="black", nl=False)
            continue
        if reasoning:
            click.secho()
        click.secho(event.content, nl=False)
        reasoning = False
    click.secho()


async def _do_run(input: str, session_id: str | None = None, last: bool = False):
    async with get_agent() as agent:
        session = agent.get_or_create_session(
            session_id=session_id, last=last, title=input
        )
        await _agent_astream(agent, input, session_id=session.uuid)


@root.command()
@click.argument("intput")
@click.option("--session", "-s", default=None, help="Session to use for the agent")
@click.option(
    "--continue",
    "-c",
    "last",
    is_flag=True,
    default=False,
    help="Continue last session",
)
def run(intput: str, session: str | None = None, last: bool = False):
    """Chat with the agent."""
    try:
        asyncio.run(_do_run(intput, session_id=session, last=last))
    except APIConnectionError:
        click.secho("api connection error", fg="red")


async def _do_chat(session_id: str | None = None, last=False):
    console = Console()
    async with get_agent() as agent:
        session = agent.get_or_create_session(session_id=session_id, last=last)
        console.print(Rule(utcnow().isoformat(sep=" "), style="cyan"))
        while True:
            user_input = Prompt.ask(Text("请输入您的意图", style="white on cyan"))
            if not user_input:
                break
            if user_input in ["exit", "quit", "q"]:
                break
            try:
                await _agent_astream(agent, user_input, session_id=session.uuid)
            except APIConnectionError:
                click.secho("api connection error", fg="red")
            click.echo()
            if not session.title:
                agent.update_session(session, user_input)


@root.command()
@click.option("--session", "-s", default=None, help="Session to use for the agent")
@click.option("--continue", "-c", "last", is_flag=True, help="Continue last session")
def chat(session: str | None = None, last: bool = False):
    """交互模式"""
    asyncio.run(_do_chat(session_id=session, last=last))
