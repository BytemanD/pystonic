from typing import Optional
import uuid

from fastmcp import FastMCP

mcp_server = FastMCP(
    name='nacos-mcp-python',
    instructions="this is nacos mcp server demo",
)

@mcp_server.tool()
def make_trace_id(prefix: Optional[str]='') -> str:
    """生成Trace id
    
    Args:
        prefix: 前缀

    Returns:
        str: Trace id.
    """
    return f'{prefix}{uuid.uuid4()}'


if __name__ == "__main__":
    mcp_server.run(transport="streamable-http", host="localhost") 
