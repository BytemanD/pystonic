import functools
from typing import List, Optional, Tuple

from agents import (
    Agent,
    MultiProvider,
    RawResponsesStreamEvent,
    RunConfig,
    Runner,
    Tool,
    set_tracing_disabled,
)
from loguru import logger
from openai.types.responses import (
    ResponseCompletedEvent,
)

from pystonic.agent.session import SessionHisotry
from pystonic.agent.tools import common, shell, sqlite, web
from pystonic.conf import CONF

# from openai.types.
from pystonic.shell import Shell

SYSTEM_PROMPT_NOTICE = """
当前系统：

{info}

"""


def fix_message_roles(messages):
    for msg in messages:
        if msg.get("role") == "tool":
            msg["role"] = "assistant"
    return messages


class OpenaiAgent:
    def __init__(
        self,
        name: str,
        instructions: Optional[str] = None,
    ):
        self.name = name
        self.instructions = instructions
        self.providers = CONF.agent.providers
        self.default_provider = CONF.agent.get_provider()

        self.shell = Shell()
        self.actions = {}

        self.session_history = SessionHisotry()

        # set_default_openai_client(self.openai, use_for_tracing=False)
        set_tracing_disabled(True)
        instructions = CONF.agent.system_prompt.strip() + SYSTEM_PROMPT_NOTICE.format(
            info=self.system_info()
        )
        logger.debug("instructions: {}", instructions)

    def system_info(self):
        return (
            f"系  统: {self.shell.platform} {self.shell.version}\n"
            f"终  端: {self.shell.terminal.value}"
        )

    @functools.lru_cache
    def list_models(self):
        return [
            f"{name}/{model}"
            for name, p in self.providers.items()
            for model in p.models
        ]

    def _get_agent(self, model: Optional[str] = None, tools: List[Tool] = []) -> Agent:
        if not model:
            models = self.list_models()
            if models:
                model = models[0]

        return Agent(
            name=self.name,
            instructions=self.instructions,
            model=model,
            tools=tools,
        )

    def _get_model_provider(
        self, model: Optional[str] = None
    ) -> Tuple[str, MultiProvider]:
        provider_name, model_name = (model or CONF.agent.default_provider).split("/")

        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found in configuration")
        if model_name not in self.providers[provider_name].models:
            raise ValueError(f"model '{model_name}' not found in configuration")

        provider = self.providers[provider_name]
        return model_name, MultiProvider(
            openai_base_url=str(provider.base_url),
            openai_api_key=provider.api_key,
            openai_use_responses=provider.openai_use_responses,
        )

    async def stream(
        self,
        input: str,
        model: Optional[str] = None,
        session_id: Optional[str] = None,
        tools: List[Tool] = [],
    ):
        model_name, provider = self._get_model_provider(model=model)
        resp = Runner.run_streamed(
            self._get_agent(model=model_name, tools=tools),
            input,
            session=self.session_history.get_session(session_id=session_id),
            max_turns=CONF.agent.max_turns,
            run_config=RunConfig(model=model, model_provider=provider),
        )
        async for event in resp.stream_events():
            logger.trace("Event: {}", event)
            yield event
            if isinstance(event, RawResponsesStreamEvent) and (
                isinstance(event.data, ResponseCompletedEvent)
            ):
                logger.success(
                    "response completed\n    usage: {}\n    summary: {}",
                    event.data.response.usage,
                    event.data.response.output,
                )

    def get_agent_sessions(self):
        """获取会话列表"""
        return self.session_history.get_agent_sessions()

    async def delete_agent_session(self, session_id: str):
        await self.session_history.delete_agent_session(session_id)

    async def clear_session(self, session_id: Optional[str] = None):
        session_store = self.session_history.get_session(session_id=session_id)
        await session_store.clear_session()
