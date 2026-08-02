import asyncio
from typing import List

from agents import (
    AgentUpdatedStreamEvent,
    RunItemStreamEvent,
    Tool,
    ToolCallItem,
)
import click
from loguru import logger
from openai.types.responses import (
    ResponseCreatedEvent,
    ResponseInProgressEvent,
    ResponseErrorEvent,
    ResponseOutputItemAddedEvent,
    ResponseReasoningSummaryTextDeltaEvent,
    ResponseTextDeltaEvent,
)

from pystonic.agent.openai import OpenaiAgent
from pystonic.agent.tools import common, shell, sqlite, web


@click.group("agent")
def root():
    pass


async def _do_chat(intput: str):
    agent = OpenaiAgent("智能助手")
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
    async for event in agent.stream(intput, tools=tools):
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
def chat(intput: str):
    """Chat with the agent."""
    asyncio.run(_do_chat(intput))
