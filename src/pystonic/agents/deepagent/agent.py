import asyncio
import json
from collections.abc import Sequence
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langchain.agents import AgentState
from langchain.agents.middleware.types import AgentMiddleware
from langchain.messages import AIMessage, HumanMessage
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseToolkit
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from loguru import logger
from pydantic import SecretStr
from sqlmodel import col

from pystonic.agents.db.models import AgentSession
from pystonic.agents.deepagent.exceptions import SessionNotFound
from pystonic.agents.deepagent.middlewares import RuntimeAgentMiddleware
from pystonic.agents.deepagent.objects import Message, RuntimeContext
from pystonic.common import context
from pystonic.common.conf import CONF


def per_user_backend(runtime):
    # 从 runtime 中获取当前用户标识，具体字段取决于你的接入方式
    user_id = runtime.context.user_id  # 示例，需替换为实际获取方式
    return FilesystemBackend(
        root_dir=f"/data/{user_id}",
        virtual_mode=True,  # 必须开启，否则 root_dir 不提供安全隔离
    )


class Agent:
    """用户隔离的Agent"""

    def __init__(
        self,
        saver: BaseCheckpointSaver,
        context_schema: type[RuntimeContext] = RuntimeContext,
        middleware: Sequence[AgentMiddleware[AgentState, RuntimeContext]] | None = None,
        workspace: str | None = None,
        toolkits: Sequence[BaseToolkit] | None = None,
    ) -> None:
        self._saver = saver
        self._workspace = Path(workspace or CONF.agent.workspace).resolve()
        self._context_schema = context_schema
        self._middleware = [RuntimeAgentMiddleware(), *(middleware or [])]
        self._tools = [
            x for row in [t.get_tools() for t in (toolkits or [])] for x in row
        ]
        self._default_agent = create_deep_agent(
            model=ChatOpenAI(model="gpt", base_url="...", api_key=SecretStr("...")),
            checkpointer=saver,
            backend=FilesystemBackend(root_dir=self._workspace),
            context_schema=context_schema,
            middleware=self._middleware,
            tools=[x for row in [t.get_tools() for t in (toolkits or [])] for x in row],
        )
        self._agents = {"": self._default_agent}

        self._lock_agents = asyncio.Lock()

    def get_agent(self):
        user = context.account()
        if not user:
            return self._default_agent
        if user not in self._agents:
            self._agents[user] = create_deep_agent(
                model=ChatOpenAI(model="gpt", base_url="...", api_key=SecretStr("...")),
                checkpointer=self._saver,
                backend=FilesystemBackend(root_dir=self._workspace.joinpath(user)),
                context_schema=self._context_schema,
                middleware=self._middleware,
                tools=self._tools,
            )
        return self._agents[user]

    async def astream(
        self,
        ctx: RuntimeContext,
        query: str,
        session: AgentSession | None = None,
        callbacks: list[BaseCallbackHandler] | None = None,
        event_types: tuple[type[AIMessage]] | None = None,
        max_concurrency: int | None = None,
        recursion_limit: int = 25,
    ):
        async with self._lock_agents:
            agent = self.get_agent()
        session = session or self.get_or_create_session(title=query)
        stream = agent.astream(
            {"messages": [{"role": "user", "content": query}]},
            stream_mode="messages",
            context=ctx,
            # version="v3"
            config=RunnableConfig(
                configurable={"thread_id": session.uuid},
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

    async def list_messages(self, session: AgentSession):
        agent = self.get_agent()
        state = await agent.aget_state(
            RunnableConfig(configurable={"thread_id": session.uuid})
        )
        return [
            Message(
                id=msg.id,
                type=msg.type,
                content=(
                    msg.content
                    if isinstance(msg.content, str)
                    else json.dumps(msg.content, ensure_ascii=False)
                ),
                thinking=msg.additional_kwargs.get("reasoning_content"),
                response_metadata=msg.response_metadata,
                usage_metadata=dict(msg.usage_metadata)
                if isinstance(msg, AIMessage) and msg.usage_metadata
                else None,
            )
            for msg in state.values["messages"]
            if (isinstance(msg, (HumanMessage, AIMessage)) and msg.id)
        ]

    @classmethod
    def create_session(cls, title: str, agent: str = ""):
        session = AgentSession(
            user=context.account(),
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
    def list_session(cls, agent: str = "", desc=False):
        return AgentSession.query(
            AgentSession.user == context.account(),
            AgentSession.agent == agent,
            _order_by=col(AgentSession.id),
            _desc=desc,
        )

    async def delete_session(self, session_id: str):
        await self._saver.adelete_thread(session_id)
        AgentSession.delete_by_uuid(session_id)

    @classmethod
    def get_session(cls, session_id: str, agent: str = ""):
        item = AgentSession.get_first(
            AgentSession.uuid == session_id,
            AgentSession.user == context.account(),
            AgentSession.agent == agent,
        )
        if not item:
            raise SessionNotFound(session_id)
        return item

    @classmethod
    def get_last_session(cls, agent: str = ""):
        return AgentSession.get_last(
            AgentSession.user == context.account(), AgentSession.agent == agent
        )

    @classmethod
    def get_or_create_session(
        cls,
        session_id: str | None = None,
        last: bool = False,
        agent: str = "",
        title: str = "",
    ):
        session = None
        if session_id:
            return cls.get_session(session_id, agent=agent)
        if last:
            session = cls.get_last_session(agent=agent)
        if not session:
            session = cls.create_session(title, agent=agent)
        return session
