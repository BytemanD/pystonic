import contextlib
from pathlib import Path
from typing import Sequence, Tuple, Type

from langchain.agents import AgentState, create_agent
from langchain.messages import AIMessage
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.runnables.config import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain.agents.middleware.types import AgentMiddleware
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.mysql.asyncmy import AsyncMySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from loguru import logger

from pydantic import SecretStr
from pystonic.agents.db.models import AgentSession
from pystonic.agents.langchain_agent.exceptions import SessionNotFount
from pystonic.agents.langchain_agent.middlewares import RuntimeAgentMiddleware
from pystonic.agents.langchain_agent.objects import Message, RuntimeContext
from pystonic.common.conf import CONF


@contextlib.asynccontextmanager
async def get_checkpointer_saver():
    if CONF.agent.checkpoint_connection == "db_config":
        conn_string = CONF.db.url
    else:
        conn_string = CONF.agent.checkpoint_connection

    if conn_string.startswith(("mysql:", "mysql+pymysql:")):
        logger.info("use mysql checkpoint saver")
        async with AsyncMySaver.from_conn_string(CONF.db.url) as saver:
            logger.debug("setup saver: {}", saver)
            await saver.setup()
            yield saver
        return
    elif conn_string.startswith("sqlite:"):
        sqlite_path = conn_string.removeprefix("sqlite:///")
        logger.info("use sqlite checkpoint saver")
        logger.debug("sqlite path: {}", sqlite_path)
        if sqlite_path != ":memory:":
            Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        async with AsyncSqliteSaver.from_conn_string(sqlite_path) as saver:
            yield saver
        return
    raise RuntimeError("checkpoint connection is inavlid")


class AsyncAgent:
    def __init__(
        self,
        saver: BaseCheckpointSaver,
        context_schema: Type[RuntimeContext] = RuntimeContext,
        middleware: Sequence[AgentMiddleware[AgentState, RuntimeContext]] | None = None,
        tools: list | None = None,
    ):
        self._saver = saver
        self._agent = create_agent(
            ChatOpenAI(model="gpt", base_url="...", api_key=SecretStr("...")),
            checkpointer=saver,
            context_schema=context_schema,
            middleware=[RuntimeAgentMiddleware(), *(middleware or [])],
            tools=tools or [],
        )

    async def astream(
        self,
        ctx: RuntimeContext,
        query: str,
        callbacks: list[BaseCallbackHandler] | None = None,
        # config: dict | None = None,
        event_types: Tuple[Type[AIMessage]] | None = None,
        max_concurrency: int | None = None,
        recursion_limit: int = 25,
    ):
        stream = self._agent.astream(
            {"messages": [{"role": "user", "content": query}]},
            stream_mode="messages",
            context=ctx,
            # version="v3"
            config=RunnableConfig(
                configurable={"thread_id": ctx.thread_id},
                callbacks=callbacks or [],
                max_concurrency=max_concurrency,
                recursion_limit=recursion_limit,
            ),
        )

        async for event in stream:
            if not isinstance(event, tuple):
                continue
            if not event_types or isinstance(event[0], event_types):
                yield event[0]
                continue
            logger.debug("skip event: {}", event)

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

    @classmethod
    def create_session(cls, title: str, user: str = "", agent: str = ""):
        session = AgentSession(
            user=user,
            agent=agent,
            title=title[:20],
        )
        session.create()
        logger.trace("create session: {}", session)
        return session

    @classmethod
    def update_session(cls, session: AgentSession, title: str):
        session.title = title[:20]
        session.save()

    @classmethod
    def list_session(cls, user: str = "", agent: str = ""):
        return AgentSession.query(
            AgentSession.user == user, AgentSession.agent == agent
        )

    @classmethod
    def delete_session(cls, session_id: str):
        return AgentSession.delete_by_uuid(session_id)

    @classmethod
    def get_session(cls, session_id: str, user: str = "", agent: str = ""):
        return AgentSession.get_first(
            AgentSession.uuid == session_id,
            AgentSession.user == user,
            AgentSession.agent == agent,
        )

    @classmethod
    def get_last_session(cls, user: str = "", agent: str = ""):
        return AgentSession.get_last(
            AgentSession.user == user, AgentSession.agent == agent
        )

    @classmethod
    def get_or_create_session(
        cls,
        session_id: str | None = None,
        last: bool = False,
        user: str = "",
        agent: str = "",
        title: str = "",
    ):
        session = None
        if session_id:
            session = cls.get_session(session_id, user=user, agent=agent)
            if not session:
                raise SessionNotFount(session_id)
            return session
        if last:
            session = cls.get_last_session()
        if not session:
            session = cls.create_session(title, user=user, agent=agent)
        return session
