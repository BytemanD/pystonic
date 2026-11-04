from pathlib import Path
from typing import Literal

from langchain_core.tools import BaseTool
from pydantic import BaseModel

from pystonic.common.conf import CONF, LLMProviderConfig
from pystonic.utils.system import home_path


class Message(BaseModel):
    id: str
    type: Literal["human", "ai"]
    content: str | None = None
    thinking: str | None = None
    response_metadata: dict | None = None
    usage_metadata: dict | None = None


class RuntimeContext(BaseModel):
    providers: dict[str, LLMProviderConfig]
    temperature: float | None = None

    system_prompt: str = CONF.agent.system_prompt
    tools: list[BaseTool] = []

    # 记录每轮会话选择的模型
    selected_model: str = ""

    workspace: Path = home_path()
    # permission
    allow_outside_workspace: bool = False
