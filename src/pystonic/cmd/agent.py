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
from pystonic.utils.dateutil import utcnow


@contextlib.asynccontextmanager
async def get_agent():
    async with get_checkpointer_saver(sqlite_memory=True) as saver:
        yield AsyncAgent(saver)


@click.group("agent")
def root():
    pass


@root.group()
def session():
    """agent sessions"""


# @session.command("list")
# def list_sesions():
#     """List agent sessions."""
#     sessions = get_agent().get_agent_sessions()
#     output.print_models(sessions)


@session.command("delete")
@click.argument("sessions", required=False, nargs=-1)
def delete_session(sessions: list[str]):
    """List agent sessions."""
    if not sessions:
        raise click.ClickException("session is required")

    for x in sessions:
        asyncio.run(get_agent().delete_agent_session(x))
        click.secho(f"delete {x} success", fg="green")


@root.group()
def model():
    """agent models"""


@model.command("list")
def list_models():
    """List models."""
    for m in get_agent().list_models():
        click.echo(m)


async def _agent_astream(agent: AsyncAgent, intput: str, session_id: str | None = None):
    ctx = RuntimeContext(
        providers=CONF.agent.providers, thread_id=session_id or "default",
        tools=builtin.WorkToolkit().get_tools()
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


async def _do_run(intput: str, session_id: str | None = None):
    async with get_agent() as agent:
        await _agent_astream(agent, intput, session_id=session_id)


@root.command()
@click.argument("intput")
@click.option("--session", "-c", default=None, help="Session to use for the agent")
def run(intput: str, session: str | None = None):
    """Chat with the agent."""
    try:
        asyncio.run(_do_run(intput, session_id=session))
    except APIConnectionError:
        click.secho("api connection error", fg="red")


async def _do_chat(session: str | None = None):
    console = Console()
    async with get_agent() as agent:
        console.print(Rule(utcnow().isoformat(sep=" "), style="cyan"))
        while True:
            user_input = Prompt.ask(Text("请输入您的意图", style="white on cyan"))
            if not user_input:
                break
            if user_input in ["exit", "quit", "q"]:
                break
            try:
                await _agent_astream(agent, user_input, session_id=session)
            except APIConnectionError:
                click.secho("api connection error", fg="red")
            click.echo()


@root.command()
@click.option("--session", "-s", default=None, help="Session to use for the agent")
def chat(session: str | None = None):
    """交互模式"""
    asyncio.run(_do_chat(session=session))
