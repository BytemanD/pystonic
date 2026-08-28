import asyncio
from datetime import datetime
from typing import List, Optional
import uuid

from agents import (
    AgentUpdatedStreamEvent,
    RunItemStreamEvent,
    Tool,
    ToolCallItem,
)
import click
from loguru import logger
from openai import APIConnectionError
from openai.types.responses import (
    ResponseCreatedEvent,
    ResponseInProgressEvent,
    ResponseErrorEvent,
    ResponseOutputItemAddedEvent,
    ResponseReasoningSummaryTextDeltaEvent,
    ResponseTextDeltaEvent,
)
from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text
from rich.rule import Rule

from pystonic.agent.openai import OpenaiAgent
from pystonic.agent.tools import common, shell, sqlite, web
from pystonic.pretty import output

console = Console()


def get_agent():
    return OpenaiAgent("智能助手")


@click.group("agent")
def root():
    pass


@root.group()
def session():
    """agent sessions"""
    pass


@session.command("list")
def list_sesions():
    """List agent sessions."""
    sessions = get_agent().get_agent_sessions()
    output.print_models(sessions)


@session.command("delete")
@click.argument("sessions", required=False, nargs=-1)
def delete_session(sessions: List[str]):
    """List agent sessions."""
    if not sessions:
        raise click.ClickException("session is required")

    for x in sessions:
        asyncio.run(get_agent().delete_agent_session(x))
        click.secho(f"delete {x} success", fg="green")


@root.group()
def model():
    """agent models"""
    pass


@model.command("list")
def list_models():
    """List models."""
    for m in get_agent().list_models():
        click.echo(m)


async def _do_chat(
    intput: str, session_id: Optional[str] = None, model: Optional[str] = None
):
    tools: List[Tool] = [
        common.change_dir,
        common.list_dir,
        common.read_file,
        common.write_file,
        shell.execute_command,
        sqlite.connect_db,
        sqlite.execute_sql,
        web.web_get,
    ]
    agent = get_agent()
    async for event in agent.stream(
        intput, session_id=session_id, model=model, tools=tools
    ):
        if isinstance(event, AgentUpdatedStreamEvent):
            click.secho(f"[切换Agent]: {event.new_agent.name}", fg="black")
            continue
        if isinstance(event, RunItemStreamEvent):
            if isinstance(event.item, ToolCallItem):
                click.secho(f"[选择工具] {event.item.tool_name}", fg="black")
            else:
                logger.debug("RunItemStreamEvent item: {}", event.item)
            continue
        if isinstance(event.data, (ResponseInProgressEvent, ResponseCreatedEvent)):
            click.secho(f"[状态] {event.data.response.status}", fg="black")
            continue
        if isinstance(event.data, ResponseErrorEvent):
            click.secho(f"[错误] {event.data.message}", fg="red")
            continue
        if isinstance(event.data, ResponseOutputItemAddedEvent):
            click.echo("")
            # click.echo("\n")
            continue
        if isinstance(event.data, ResponseReasoningSummaryTextDeltaEvent):
            click.secho(event.data.delta, fg="black", nl=False)
            continue
        if isinstance(event.data, ResponseTextDeltaEvent):
            click.secho(event.data.delta, fg="cyan", nl=False)
            continue

        # elif isinstance(event, stream_events.RunItemStreamEvent):
        #     logger.debug("RunItemStreamEvent raw_item: {}", event.item.raw_item)
        #     if event.item.raw_item.content:
        #         for content in event.item.raw_item.content:
        #             if not content.text:
        #                 continue
        #             click.secho(content.text, fg="cyan")
        #     elif event.item.raw_item.summary:
        #         for sumary in event.item.raw_item.summary:
        #             click.secho(textwrap.indent(sumary.text.rstrip(), "> "), fg="blue")
        #     continue
        # else:


@root.command()
@click.argument("intput")
@click.option("--model", "-m", default=None, help="Model to use for the agent")
@click.option("--session", "-c", default=None, help="Session to use for the agent")
def run(intput: str, session: Optional[str] = None, model: Optional[str] = None):
    """Chat with the agent."""
    try:
        asyncio.run(_do_chat(intput, session_id=session, model=model))
    except APIConnectionError:
        click.secho("api connection error", fg="red")


@root.command()
@click.option("--model", "-m", default=None, help="Model to use for the agent")
@click.option("--session", "-s", default=None, help="Session to use for the agent")
def chat(session: Optional[str] = None, model: Optional[str] = None):
    """交互模式"""
    session = session or uuid.uuid4().hex
    while True:
        console.print(Rule(datetime.now().isoformat(sep=" "), style="cyan"))
        while True:
            user_input = Prompt.ask(Text("请输入您的意图", style="white on cyan"))
            if user_input:
                break
        if user_input in ["exit", "quit", "q"]:
            break
        try:
            asyncio.run(_do_chat(user_input, session_id=session, model=model))
        except APIConnectionError:
            click.secho("api connection error", fg="red")
        click.echo()
