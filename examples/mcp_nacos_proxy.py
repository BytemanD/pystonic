from typing import Optional
import uuid

from fastmcp.server import create_proxy
from pystonic.mcp import server

from pystonic.conf import McpConfig
from pystonic.mcp.proxy302 import NacosMCPProxy


conf = McpConfig(
    name='nacos-mcp-python2',
    instructions="this is nacos mcp server demo",
    transport="streamable-http",
    enable_nacos=True,
    prroxy='http://localhost:18000/mcp',
    port=18001,
)
mcp_server = server.McpServer(conf)


if __name__ == "__main__":
    mcp_server.run() 
