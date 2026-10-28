from langchain_core.tools import BaseTool
from pydantic import BaseModel


class Message(BaseModel):
    id: str
    type: str
    content: str | None = None
    thinking: str | None = None


class RuntimeContext(BaseModel):
    models: list[str]
    model_base_url: str
    model_api_key: str

    agent_uuid: str
    session_uuid: str
    username: str

    model: str | None = None
    system_prompt: str = ""
    tools: list[BaseTool] = []
    attachments: list[str] = []

    tool_args: dict = {}

    selected_model: str = ""
