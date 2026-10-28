import contextlib
from pathlib import Path
from typing import Sequence, Type

from langchain.agents import create_agent
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessageChunk
from langchain_core.runnables.config import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain.agents.middleware.types import AgentMiddleware
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.mysql.asyncmy import AsyncMySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from loguru import logger

from pydantic import BaseModel, SecretStr
from pystonic.agent.langchain_agent.objects import Message, RuntimeContext
from pystonic.common import context
from pystonic.common.conf import CONF
from pystonic.orm.database import engine_name


@contextlib.asynccontextmanager
async def get_checkpointer_saver():
    if CONF.agent.checkpoint_driver in ["auto", "mysql"] and engine_name() == "mysql":
        logger.info("use mysql checkpoint saver")
        async with AsyncMySaver.from_conn_string(CONF.db.url) as saver:
            logger.debug("setup saver: {}", saver)
            await saver.setup()
            yield saver
        return

    if CONF.agent.checkpoint_driver == "mysql":
        raise RuntimeError('checkpoint driver is "mysql" but db config is not mysql ')

    logger.info("use sqlite checkpoint saver")
    saver_path = Path(CONF.store, "checkpoint.sqlite")
    saver_path.parent.mkdir(parents=True, exist_ok=True)
    async with AsyncSqliteSaver.from_conn_string(str(saver_path)) as saver:
        yield saver


class AsyncAgent:
    def __init__(
        self,
        saver: BaseCheckpointSaver | None = None,
        context_schema: Type[RuntimeContext] | None = None,
        middleware: Sequence[AgentMiddleware] | None = None,
        tools: list | None = None,
    ):
        self._saver = saver
        self._agent = create_agent(
            ChatOpenAI(model="gpt", base_url="...", api_key=SecretStr("...")),
            checkpointer=saver,
            context_schema=context_schema,
            middleware=middleware or [],
            tools=tools or [],
        )

    async def chat(
        self,
        ctx: BaseModel,
        query: str,
        callbacks: Sequence[BaseCallbackHandler] | None = None,
    ):
        stream = self._agent.astream(
            {"messages": [{"role": "user", "content": query}]},
            stream_mode="messages",
            config={
                "configurable": {"thread_id": ctx.session_uuid},
                "metadata": {
                    "user": context.getvar("account"),
                    "agent": ctx.agent_uuid,
                },
                "callbacks": callbacks or [],
            },
            # version="v3"
            context=ctx,
        )

        async for event in stream:
            if isinstance(event, tuple) and isinstance(event[0], AIMessageChunk):
                yield event[0]
                continue
            logger.warning("unknowd event: {}", event)

    async def list_messages(self, thread_id: str):
        config = RunnableConfig(configurable={"thread_id": thread_id})
        item = await self._saver.aget_tuple(config)
        if not item:
            return []

        return [
            Message(
                id=msg.id,
                type=msg.type,
                content=msg.content,
                thinking=msg.additional_kwargs.get("reasoning_content"),
            )
            for msg in item.checkpoint.get("channel_values", {}).get("messages", [])
            if msg.type in ["human", "ai"]
        ]
