import uuid
from typing import Optional

from pystonic.common.conf import McpConfig
from pystonic.mcp import server

mcp_server = server.McpServer(
    McpConfig(
        name="nacos-mcp-python2",
        instructions="this is nacos mcp server demo",
        transport="streamable-http",
        enable_nacos=True,
    )
)


@mcp_server.tool()
def make_trace_id(prefix: Optional[str] = "") -> str:
    """生成Trace id

    Args:
        prefix (Optional[str], optional): 前缀. Defaults to ''.

    Returns:
        str: Trace id.
    """
    return f"{prefix}{uuid.uuid4()}"


if __name__ == "__main__":
    mcp_server.run()
