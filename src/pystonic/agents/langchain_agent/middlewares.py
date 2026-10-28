from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware import (
    AgentMiddleware,
    AgentState,
    ModelRequest,
    ModelResponse,
    ToolCallRequest,
)
from langchain_core.exceptions import ModelRateLimitError
from langchain_core.messages import AIMessageChunk, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from loguru import logger

from pystonic.agents.langchain_agent.exceptions import AllModelsFailed, ModelsIsEmpty
from pystonic.agents.langchain_agent.objects import RuntimeContext


class ReasoningChatOpenAI(ChatOpenAI):
    """保留 reasoning_content 字段的 ChatOpenAI 包装器"""

    def _convert_chunk_to_generation_chunk(
        self, chunk, default_chunk_class, base_generation_info
    ):
        generation_chunk = super()._convert_chunk_to_generation_chunk(
            chunk, default_chunk_class, base_generation_info
        )
        if generation_chunk is None:
            return None

        # 从原始 delta 中提取 reasoning_content
        choices = chunk.get("choices", [])
        if choices:
            delta = choices[0].get("delta", {})
            reasoning = delta.get("reasoning_content") or delta.get("reasoning")
            if reasoning and isinstance(generation_chunk.message, AIMessageChunk):
                # breakpoint()
                prev = generation_chunk.message.additional_kwargs.get(
                    "reasoning_content", ""
                )
                generation_chunk.message.additional_kwargs["reasoning_content"] = (
                    prev + reasoning
                )
        return generation_chunk


class RuntimeAgentMiddleware(AgentMiddleware[AgentState, RuntimeContext]):
    @staticmethod
    def is_quota_error(e):
        return isinstance(e, ModelRateLimitError) or (
            hasattr(e, "status_code") and e.status_code in (402, 429, 403)
        )

    def _get_runtime_model(
        self, ctx: RuntimeContext, base_url: str, api_key: str, model: str
    ) -> ChatOpenAI:
        return ReasoningChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=ctx.temperature,
            stream_usage=True,
            model_kwargs={"stream_options": {"include_usage": True}},
            # use_responses_api=True,
            # reasoning_effort="medium",
            # use_responses_api=False,
        )

    async def awrap_model_call(  # type: ignore
        self,
        request: ModelRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ModelResponse]],
    ):
        ctx: RuntimeContext = request.runtime.context  # type: ignore
        logger.trace("runtime context: {}", ctx)
        errors: list[str] = []
        for name, provider in ctx.providers.items():
            if not provider.models:
                logger.warning("provider({}) models is empty", name)
                continue
            for model_name in provider.models:
                try:
                    ctx.selected_model = f"{name}/{provider.models}"
                    runtime_model = self._get_runtime_model(
                        ctx,
                        provider.base_url,
                        provider.api_key.get_secret_value(),
                        model_name,
                    )
                    logger.debug(
                        "runtime llm: base_url={}, model_name={}",
                        runtime_model.openai_api_base,
                        runtime_model.model_name,
                    )

                    return await handler(
                        request.override(
                            model=runtime_model,
                            tools=ctx.tools,  # type: ignore
                            system_message=SystemMessage(content=ctx.system_prompt),
                        )
                    )
                except Exception as e:
                    errors.append(f"model {model_name}: {e}")
                    continue

        if errors:
            ctx.selected_model = ""
            raise AllModelsFailed(errors)
        else:
            raise ModelsIsEmpty()

    def _override_tools(self, request: ToolCallRequest):
        ctx: RuntimeContext = request.runtime.context  # type: ignore
        tool_map = {t.name: t for t in ctx.tools}
        tool_name = request.tool_call["name"]
        if tool_name in tool_map:
            # 用 request.override 替换为真实的工具实例
            return request.override(tool=tool_map[tool_name])
        return request

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ):
        return handler(self._override_tools(request))

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ):
        return await handler(self._override_tools(request))
