import asyncio
import functools
from pathlib import Path
from unittest.mock import patch

import pytest
from langchain_core.messages.tool import ToolMessage
from pydantic import SecretStr

from pystonic.agents.deepagent.agent import Agent
from pystonic.agents.deepagent.exceptions import AllModelsFailed, ModelsIsEmpty
from pystonic.agents.deepagent.objects import RuntimeContext
from pystonic.agents.deepagent.tools import builtin
from pystonic.agents.deepagent.utils import get_checkpointer_saver
from pystonic.common import context
from pystonic.common.conf import CONF, LLMProviderConfig
from pystonic.orm.database import create_all_tables
from pystonic.utils.funcutil import async_cmd

pytestmark = pytest.mark.skipif(
    not CONF.agent.providers, reason="agent providers is empty, skip"
)

fake_provider1 = LLMProviderConfig(
    base_url="http://foo", api_key=SecretStr("foo"), models=[]
)
fake_provider2 = LLMProviderConfig(
    base_url="http://foo", api_key=SecretStr("foo"), models=["foo"]
)


@pytest.fixture(scope="module", autouse=True)
def _init():
    create_all_tables()


@async_cmd
async def test_agent_get_agent():
    with patch("pystonic.agents.deepagent.agent.create_deep_agent") as mock_create:
        async with get_checkpointer_saver() as saver:
            Agent(saver).get_agent()
            assert "backend" in mock_create.call_args[1]
            assert str(mock_create.call_args[1]["backend"].cwd) == str(
                Path(CONF.agent.workspace).resolve()
            )


@async_cmd
async def test_agent_get_agent_with_user():
    context.set_account("foo")
    with patch("pystonic.agents.deepagent.agent.create_deep_agent") as mock_create:
        async with get_checkpointer_saver() as saver:
            Agent(saver).get_agent()
            assert "backend" in mock_create.call_args[1]
            assert str(mock_create.call_args[1]["backend"].cwd) == str(
                Path(CONF.agent.workspace).joinpath("foo").resolve()
            )

    context.set_account("bar")
    with patch("pystonic.agents.deepagent.agent.create_deep_agent") as mock_create:
        async with get_checkpointer_saver() as saver:
            Agent(saver).get_agent()
            assert "backend" in mock_create.call_args[1]
            assert str(mock_create.call_args[1]["backend"].cwd) == str(
                Path(CONF.agent.workspace).joinpath("bar").resolve()
            )


@async_cmd
async def test_astream_without_tools():
    ctx = RuntimeContext(
        providers=CONF.agent.providers,
        system_prompt="你是一个智能助手.",
    )

    response_content = ""
    async with get_checkpointer_saver() as saver:
        agent = Agent(saver)
        session = agent.get_or_create_session(title="hello")
        async for event in agent.astream(ctx, "hello", session=session):
            if event.content:
                response_content += str(event.content)

        assert response_content != ""
        messages = await agent.list_messages(session)
        assert len(messages) == 2
        assert messages[0].type == "human"
        assert messages[0].content == "hello"
        assert messages[1].type == "ai"
        assert messages[1].content == response_content

        assert len(agent.list_session()) == 1
        assert agent.get_session(session.uuid)

        await agent.delete_session(session.uuid)
        assert not agent.list_session()


@async_cmd
async def test_astream_with_tools():
    ctx = RuntimeContext(
        providers=CONF.agent.providers,
        system_prompt="你是一个智能助手.",
        tools=builtin.WorkToolkit().get_tools(),
    )
    async with get_checkpointer_saver() as saver:
        agent = Agent(saver)

        got_events = set()
        async for event in agent.astream(ctx, "当前时间"):
            got_events.add(type(event))
        assert ToolMessage in got_events


@async_cmd
async def test_astream_with_provider_empty():
    ctx = RuntimeContext(
        providers={},
        system_prompt="你是一个智能助手.",
    )
    async with get_checkpointer_saver() as saver:
        agent = Agent(saver)
        with pytest.raises(ModelsIsEmpty):
            async for _ in agent.astream(ctx, "hello"):
                pass


@async_cmd
async def test_astream_with_models_empty():
    ctx = RuntimeContext(
        providers={"test": fake_provider1},
        system_prompt="你是一个智能助手.",
    )
    async with get_checkpointer_saver() as saver:
        agent = Agent(saver)
        with pytest.raises(ModelsIsEmpty):
            async for _ in agent.astream(ctx, "hello"):
                pass


@async_cmd
async def test_astream_with_all_models_failed():
    ctx = RuntimeContext(
        providers={"test": fake_provider2},
        system_prompt="你是一个智能助手.",
    )

    async with get_checkpointer_saver() as saver:
        agent = Agent(saver)
        with pytest.raises(AllModelsFailed):
            async for _ in agent.astream(ctx, "hello"):
                pass
