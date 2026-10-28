from collections.abc import Sequence

from langchain_mcp_adapters.client import MultiServerMCPClient
from pydantic import BaseModel


class MCP(BaseModel):
    url: str
    transport: str = "streamable_http"
    name: str | None = None
    api_key: str | None = None


async def get_mcp_server_info(
    name: str, url: str, transport: str, api_key: str | None = None
):
    client = MultiServerMCPClient(
        {
            name: {
                "url": url,
                "transport": transport,
                "headers": {"Authorization": f"Bearer {api_key}"} if api_key else {},
            }
        }
    )
    return await client.get_server_info()


async def get_tools(mcps: Sequence[MCP]):
    client = MultiServerMCPClient(
        {
            # 用 uuid 而非 name 作 key：不同 MCP 可能重名（测试库里就有两个
            # 叫 Math 的），用 name 会互相覆盖导致工具静默丢失。
            # key 只作连接标识，工具名来自 MCP server，不受影响。
            mcp.uuid: {
                "url": mcp.url,
                "transport": mcp.transport,
                "headers": {"Authorization": f"Bearer {mcp.api_key}"}
                if mcp.api_key
                else {},
            }
            for mcp in mcps
        }
    )
    return await client.get_tools()
