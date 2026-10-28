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
from pydantic import SecretStr

from pystonic.agent.langchain_agent.objects import RuntimeContext


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

    def _get_runtime_model(self, ctx: RuntimeContext, model_name: str) -> ChatOpenAI:
        return ReasoningChatOpenAI(
            model=model_name,
            api_key=SecretStr(ctx.model_api_key),
            base_url=ctx.model_base_url,
            temperature=ctx.agent_config.temperature,
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
        logger.info(
            "runtime tools: {}, knowledge bases: {}",
            [x.name for x in ctx.tools or []],
            [x.name for x in ctx.knowledge_bases],
        )
        if ctx.model:
            ctx.selected_model = ctx.model
            return await handler(
                request.override(
                    model=self._get_runtime_model(ctx, ctx.model),
                    tools=ctx.tools,  # type: ignore
                    system_message=SystemMessage(content=ctx.system_prompt),
                )
            )
        else:
            last_error = None
            for model_name in ctx.models:
                try:
                    ctx.selected_model = model_name
                    return await handler(
                        request.override(
                            model=self._get_runtime_model(ctx, model_name),
                            tools=ctx.tools,  # type: ignore
                            system_message=SystemMessage(content=ctx.system_prompt),
                        )
                    )
                except Exception as e:
                    if self.is_quota_error(e):  # 自己判断 429/402
                        last_error = e
                        continue
                    raise
            if last_error:
                ctx.selected_model = ""
                raise last_error

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
