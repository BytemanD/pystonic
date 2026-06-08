from typing import Optional
import uuid

from nacos_mcp_wrapper.server.nacos_settings import NacosSettings
from nacos_mcp_wrapper.server.nacos_mcp import NacosMCP
from fastmcp import FastMCP
from pystonic.mcp import server

from pystonic.conf import McpConfig

mcp_server = server.McpServer(
    McpConfig(
        name='nacos-mcp-python2',
        instructions="this is nacos mcp server demo",
        transport="streamable-http",
        enable_nacos=True
    )
)

@mcp_server.tool()
def make_trace_id(prefix: Optional[str]='') -> str:
    """生成Trace id
    
    Args:
        prefix (Optional[str], optional): 前缀. Defaults to ''.

    Returns:
        str: Trace id.
    """
    return f'{prefix}{uuid.uuid4()}'


if __name__ == "__main__":
    mcp_server.run() 
