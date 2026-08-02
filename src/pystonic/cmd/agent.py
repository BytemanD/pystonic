import asyncio
import textwrap

from agents import (
    AgentUpdatedStreamEvent,
    RunItemStreamEvent,
    ToolCallItem,
    ToolOutputText,
    stream_events,
)
import click
from loguru import logger
from openai.types.responses import (
    ResponseCreatedEvent,
    ResponseFailedEvent,
    ResponseInProgressEvent,
    ResponseErrorEvent,
    ResponseOutputItemAddedEvent,
    ResponseOutputItemDoneEvent,
    ResponseReasoningSummaryPartAddedEvent,
    ResponseReasoningSummaryTextDeltaEvent,
    ResponseTextDeltaEvent,
    ResponseReasoningTextDeltaEvent,
)
from rich.markdown import Markdown

from pystonic.agent.openai import OpenaiAgent
from pystonic.log import setup_logger


@click.group("agent")
def root():
    pass


async def _do_chat(intput: str):
    agent = OpenaiAgent("智能助手")
    async for event in agent.stream(intput):
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
        logger.debug("other event: {}", event)


@root.command()
@click.argument("intput")
def chat(intput: str):
    """Chat with the agent."""
    asyncio.run(_do_chat(intput))
