from collections.abc import Sequence

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import (
    SSEConnection,
    StreamableHttpConnection,
    WebsocketConnection,
)
from pydantic import BaseModel


class MCP(BaseModel):
    url: str
    transport: str = "streamable_http"
    name: str | None = None
    api_key: str | None = None


def _get_connection(
    transport: str,
    url: str,
    api_key: str | None = None,
    session_kwargs: dict | None = None,
):
    if transport == "sse":
        return SSEConnection(
            transport="sse",
            url=url,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
        )
    elif transport == "streamable_http":
        return StreamableHttpConnection(
            transport="streamable_http",
            url=url,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
        )
    elif transport == "websocket":
        return WebsocketConnection(
            transport="websocket",
            url=url,
            session_kwargs=session_kwargs,
        )
    raise ValueError("unsupport transport: {}", transport)


async def get_mcp_server_info(
    name: str, url: str, transport: str, api_key: str | None = None
):
    client = MultiServerMCPClient(
        connections={name: _get_connection(transport, url, api_key=api_key)}
    )
    return await client.get_server_info()


async def get_tools(mcps: Sequence[MCP]):
    client = MultiServerMCPClient(
        {
            mcp.name or mcp.url: _get_connection(
                mcp.transport, mcp.url, api_key=mcp.api_key
            )
            for mcp in mcps
        }
    )
    return await client.get_tools()
