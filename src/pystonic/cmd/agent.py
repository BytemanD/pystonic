import asyncio
import contextlib

import click
import toml
from openai import APIConnectionError
from rich.console import Console
from rich.table import Table

from pystonic.agents.langchain_agent.agent import AsyncAgent, get_checkpointer_saver
from pystonic.cmd.console_agent.app import ConsoleAgentApp
from pystonic.common.conf import CONF
from pystonic.common.log import setup_logger
from pystonic.orm import database
from pystonic.pretty import output


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


@click.group()
def provider():
    """模型提供商管理"""


@provider.command()
@click.option("--detail", is_flag=True, help="显示详细配置")
def list(detail: bool):
    """查看提供商"""

    console = Console()
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

        table.add_row(
            name,
            content.strip(),
            # style="cyan" if provider.name == CONF.ai_shell.use_provider else None,
        )

    console.print(table)


async def _do_run(input: str, session_id: str | None = None, last: bool = False):
    async with get_agent() as agent:
        await ConsoleAgentApp(agent).call_once(input, session_id=session_id, last=last)


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
def console(session: str | None = None, last: bool = False):
    """交互模式"""
    setup_logger(remove=True, disable_console_log=True)
    asyncio.run(_do_chat(session_id=session, last=last))
