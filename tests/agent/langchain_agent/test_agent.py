from pydantic import SecretStr
import pytest

import pytest_asyncio

from pystonic.agents.langchain_agent.agent import AsyncAgent, get_checkpointer_saver
from pystonic.agents.langchain_agent.exceptions import AllModelsFailed, ModelsIsEmpty
from pystonic.agents.langchain_agent.objects import RuntimeContext
from pystonic.agents.langchain_agent.tools import builtin
from pystonic.common.conf import CONF, LLMProviderConfig
from langchain_core.messages.tool import ToolMessage

pytestmark = pytest.mark.skipif(
    not CONF.agent.providers, reason="env TEST_LLM_BASE_URL is missing, skip"
)

fake_provider1 = LLMProviderConfig(
    base_url="http://foo", api_key=SecretStr("foo"), models=[]
)
fake_provider2 = LLMProviderConfig(
    base_url="http://foo", api_key=SecretStr("foo"), models=["foo"]
)


@pytest_asyncio.fixture(scope="module", loop_scope="module", autouse=True)
async def agent():
    async with get_checkpointer_saver(sqlite_memory=True) as saver:
        yield AsyncAgent(saver)


@pytest.mark.asyncio
async def test_astream(agent: AsyncAgent):
    ctx = RuntimeContext(
        providers=CONF.agent.providers,
        thread_id="11111111111",
        system_prompt="你是一个智能助手.",
    )

    response_content = ""
    async for event in agent.astream(ctx, "hello"):
        if event.content:
            response_content += event.content

    assert response_content != ""
    messages = await agent.list_messages(ctx.thread_id)
    assert len(messages) == 2
    assert messages[0].type == "human"
    assert messages[0].content == "hello"
    assert messages[1].type == "ai"
    assert messages[1].content == response_content


@pytest.mark.asyncio
async def test_astream_with_tools(agent: AsyncAgent):
    ctx = RuntimeContext(
        providers=CONF.agent.providers,
        thread_id="11111111111",
        system_prompt="你是一个智能助手.",
        tools=builtin.WorkToolkit(
            enable_read=False,
            enable_write=False,
            enable_execute_shell=False,
            enable_web_get=False,
            enable_get_platform_info=False,
        ).get_tools()
    )

    got_events = set()
    async for event in agent.astream(ctx, "当前时间"):
        got_events.add(type(event))
    assert ToolMessage in got_events

@pytest.mark.asyncio
async def test_astream_with_provider_empty(agent: AsyncAgent):
    ctx = RuntimeContext(
        providers={},
        thread_id="11111111111",
        system_prompt="你是一个智能助手.",
    )

    with pytest.raises(ModelsIsEmpty):
        async for _ in agent.astream(ctx, "hello"):
            pass


@pytest.mark.asyncio
async def test_astream_with_models_empty(agent: AsyncAgent):
    ctx = RuntimeContext(
        providers={"test": fake_provider1},
        thread_id="11111111111",
        system_prompt="你是一个智能助手.",
    )

    with pytest.raises(ModelsIsEmpty):
        async for _ in agent.astream(ctx, "hello"):
            pass


@pytest.mark.asyncio
async def test_astream_with_all_models_failed(agent: AsyncAgent):
    ctx = RuntimeContext(
        providers={"test": fake_provider2},
        thread_id="11111111111",
        system_prompt="你是一个智能助手.",
    )

    with pytest.raises(AllModelsFailed):
        async for _ in agent.astream(ctx, "hello"):
            pass
