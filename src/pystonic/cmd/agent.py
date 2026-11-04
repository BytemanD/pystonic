import asyncio
import contextlib

import click
import toml
from langchain.messages import ToolMessage
from loguru import logger
from openai import APIConnectionError
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from pystonic.agents.deepagent.agent import Agent
from pystonic.agents.deepagent.objects import RuntimeContext
from pystonic.agents.deepagent.utils import get_checkpointer_saver
from pystonic.cmd.console_agent.app import ConsoleAgentApp
from pystonic.common.conf import CONF
from pystonic.common.log import setup_logger
from pystonic.orm import database
from pystonic.pretty import output
from pystonic.utils.funcutil import async_cmd

console = Console()


@contextlib.asynccontextmanager
async def get_agent():
    async with get_checkpointer_saver() as saver:
        logger.debug("setup saver: {}", saver)
        await saver.setup()
        yield Agent(saver)


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
            await agent.delete_session(session_id)


async def _get_agent_messages(session_id: str):
    async with get_agent() as agent:
        await agent.list_messages(agent.get_session(session_id))


@session.command("list")
@async_cmd
async def list_sesions():
    """List agent sessions."""
    async with get_agent() as agent:
        sessions = agent.list_session()
        output.print_models(sessions, fields=["created_at", "uuid", "title"])


@session.command("delete")
@click.argument("sessions", required=False, nargs=-1)
def delete_session(sessions: list[str]):
    """List agent sessions."""
    asyncio.run(_delete_session(sessions))


@session.command("messages")
@click.argument("session_id")
@async_cmd
async def get_messages(session_id: str):
    """List agent sessions."""
    async with get_agent() as agent:
        messages = await agent.list_messages(agent.get_session(session_id))
    for message in messages:
        if message.type == "human":
            console.print(Panel(message.content or "", border_style="cyan"))
        elif message.type == "ai":
            console.print(Markdown(message.content or ""))


@click.group()
def provider():
    """模型提供商管理"""


@provider.command()
@click.option("--detail", is_flag=True, help="显示详细配置")
def list(detail: bool):
    """查看提供商"""

    table = Table(header_style="bold")
    table.add_column("Name")
    table.add_column("Config" if detail else "URL")
    for name, provider in CONF.agent.providers.items():
        if detail:
            content = toml.dumps(
                provider.model_dump(mode="json", exclude_none=True, exclude={"name"})
            )
        else:
            content = str(provider.base_url)

        table.add_row(name, content.strip())

    console.print(table)


async def _do_run(input: str, session_id: str | None = None, last: bool = False):
    reasoning = False

    ctx = RuntimeContext(providers=CONF.agent.providers)
    async with get_agent() as agent:
        async for event in agent.astream(
            ctx,
            input,
            session=agent.get_or_create_session(
                session_id=session_id, last=last, title=input
            ),
        ):
            if isinstance(event, ToolMessage):
                console.print(f"调用工具: {event.name}", style="magenta")
                continue
            reasoning_content = event.additional_kwargs.get("reasoning_content")
            if reasoning_content:
                reasoning = True
                console.print(reasoning_content, style="black", end="")
                continue
            if reasoning:
                console.print()
            console.print(event.content, end="")
            reasoning = False
        console.print()


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
    async with get_agent() as agent:
        await ConsoleAgentApp(agent).run_async()


@root.command()
def chat(session: str | None = None, last: bool = False):
    """交互模式"""
    setup_logger(remove=True, disable_console_log=True)
    asyncio.run(_do_chat(session_id=session, last=last))
