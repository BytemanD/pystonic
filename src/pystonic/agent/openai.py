import asyncio
import atexit
import textwrap
from datetime import datetime
from importlib import metadata
from typing import Optional

import openai
from agents import (
    Agent,
    MultiProvider,
    RunConfig,
    Runner,
    set_default_openai_client,
    set_tracing_disabled,
    stream_events,
)
from agents.exceptions import AgentsException
from loguru import logger
from openai import AsyncOpenAI
from openai.types.responses import (
    ResponseCreatedEvent,
    ResponseFailedEvent,
    ResponseInProgressEvent,
)
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.text import Text

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


class ShellAgent:
    def __init__(
        self,
        yes=False,
        session_id: Optional[str] = None,
        last_session: bool = False,
        save_session: bool = True,
    ):
        self.yes = yes
        self.save_session = save_session
        self.providers = CONF.agent.providers

        self.default_provider = CONF.agent.get_provider()

        self.shell = Shell()
        self.console = Console()
        self.actions = {}

        if not self.default_provider.api_key:
            raise ValueError(
                f'api_key of provider "{self.default_provider.name}" is missing'
            )
        self.openai = AsyncOpenAI(
            api_key=self.default_provider.api_key,
            base_url=str(self.default_provider.base_url),
            timeout=CONF.agent.openai_timeout,
        )
        self.response_id = None
        self.session_history = SessionHisotry()
        self.session_store = self.session_history.get_session_store(
            session_id=session_id,
            last_session=last_session,
            save_session=self.save_session,
        )
        logger.info("session id: {}", self.session_store.session_id)

        set_default_openai_client(self.openai, use_for_tracing=False)
        set_tracing_disabled(True)
        instructions = CONF.agent.system_prompt.strip() + SYSTEM_PROMPT_NOTICE.format(
            info=self.system_info()
        )
        logger.debug("instructions: {}", instructions)
        self.agent = Agent(
            name="AI-Shell",
            instructions=instructions,
            model=self.model,
            tools=[
                common.change_dir,
                common.list_dir,
                common.read_file,
                common.write_file,
                shell.execute_command,
                sqlite.connect_db,
                sqlite.execute_sql,
                web.web_get,
            ],
        )
        atexit.register(self.close)

    def close(self):
        logger.info("close shell agent")

    def provider_info(self):
        return f"提供商: {self.provider.name}\n模  型: {self.model}"

    def system_info(self):
        return (
            f"系  统: {self.shell.platform} {self.shell.version}\n"
            f"终  端: {self.shell.terminal}"
        )

    async def list_model(self):
        return [x.id for x in (await self.openai.models.list()).data]

    async def _call_llm(self, user_input: str):
        logger.debug("输入: {}", user_input)
        if not CONF.agent.stream:
            with self.console.status("正在思考...", speed=0.5):
                result = await Runner.run(
                    self.agent,
                    user_input,
                    session=self.session_store,
                    max_turns=CONF.agent.max_turns,
                    run_config=RunConfig(
                        model=self.model,
                        model_provider=MultiProvider(
                            openai_use_responses=self.provider.openai_use_responses,
                        ),
                    ),
                    # NOTE: 使用了本地本地会话持久化后不能使用以下参数
                    # auto_previous_response_id=True,
                    # previous_response_id=self.response_id,
                )
            return result.new_items[-1].raw_item.content[-1].text
        result = Runner.run_streamed(
            self.agent,
            user_input,
            session=self.session_store,
            max_turns=CONF.agent.max_turns,
            run_config=RunConfig(
                model=self.model,
                model_provider=MultiProvider(
                    openai_use_responses=self.provider.openai_use_responses,
                ),
            ),
            # NOTE: 使用了本地本地会话持久化后不能使用以下参数
            # auto_previous_response_id=True,
            # previous_response_id=self.response_id,
        )
        async for event in result.stream_events():
            if isinstance(event, stream_events.AgentUpdatedStreamEvent):
                self.console.print(
                    f"[切换Agent]: {event.new_agent.name}", style="grey0"
                )
                continue
                # 通知用户 Agent 正在切换
            elif isinstance(event, stream_events.RawResponsesStreamEvent):
                if hasattr(event.data, "delta"):
                    # print(event.data.delta, flush=True, end='')
                    pass
                elif isinstance(
                    event.data, (ResponseInProgressEvent, ResponseCreatedEvent)
                ):
                    self.console.print(
                        f"[状态] {event.data.response.status}", style="grey0"
                    )
                elif isinstance(event.data, ResponseFailedEvent):
                    logger.debug(
                        "received response failed event: {}", event.data.response.error
                    )
                    if CONF.ai_shell.show_failed_event:
                        self.console.print(
                            Panel(
                                event.data.response.error.model_dump_json(),
                                title="收到错误事件",
                                border_style="red",
                            ),
                        )
                else:
                    pass
                continue
            elif event.name == "tool_called":
                # 向用户展示工具调用状态
                self.console.print(
                    f"[选择工具] {event.item.raw_item.name}, 参数： {event.item.raw_item.arguments}",
                    style="grey0",
                )
                logger.info(
                    "选择工具: {}, 参数: {}",
                    event.item.raw_item.name,
                    event.item.raw_item.arguments,
                )
                continue
            elif event.name == "tool_output":
                logger.info("工具输出: {}", event.item.output)
                continue
            elif isinstance(event, stream_events.RunItemStreamEvent):
                logger.debug("RunItemStreamEvent raw_item: {}", event.item.raw_item)
                if event.item.raw_item.content:
                    for content in event.item.raw_item.content:
                        if not content.text:
                            continue
                        self.console.print(
                            Panel(
                                Markdown(content.text), title="AI", border_style="cyan"
                            )
                        )
                elif event.item.raw_item.summary:
                    for sumary in event.item.raw_item.summary:
                        self.console.print(
                            textwrap.indent(sumary.text.rstrip(), "> "), style="grey0"
                        )
                continue
            else:
                logger.debug("other event: {}", event)

        for response in result.raw_responses:
            if response.usage:
                print("===== {} ===", response.request_id)
                print(f"输入 Tokens: {response.usage.input_tokens}")
                print(f"输出 Tokens: {response.usage.output_tokens}")
                print(f"总计 Tokens: {response.usage.total_tokens}")
                # 如果有缓存命中，还可以看到缓存相关数据
                if hasattr(response.usage, "input_tokens_details"):
                    print(
                        f"缓存命中 Tokens: {response.usage.input_tokens_details.cached_tokens}"
                    )

    async def run(self, user_input: str):
        if user_input in self.actions:
            self.actions[user_input](self)
            return
        answer = ""
        try:
            answer = await self._call_llm(user_input)
        except (openai.RateLimitError, AgentsException) as e:
            logger.error("模型调用异常: {}", e)
            return
        if answer:
            self.console.print(Panel(Markdown(answer), border_style="cyan"))

    async def chat(self):
        self.console.print(
            Panel(
                f"{self.system_info()}\n{self.provider_info()}",
                title=f"AI-Shell {metadata.version('ai-shell')}",
            ),
            Text(f"Session: {self.session_store.session_id}"),
        )

        while True:
            self.console.print(Rule(datetime.now().isoformat(sep=" "), style="cyan"))
            while True:
                user_input = Prompt.ask(
                    Text(CONF.ai_shell.input_prompt, style="white on cyan")
                )
                if user_input:
                    break
            if user_input in CONF.ai_shell.exit_keys:
                break
            await self.run(user_input)

    def get_agent_sessions(self):
        """获取会话列表"""
        return self.session_history.get_agent_sessions()

    async def delete_agent_session(self, session_id: str):
        await self.session_history.delete_agent_session(session_id)

    def clear_session(self, session_id: Optional[str]):
        session_store = self.session_history.get_session_store(
            session_id=session_id, last_session=True, raise_if_not_found=True
        )
        asyncio.run(session_store.clear_session())
        return session_store.session_id
