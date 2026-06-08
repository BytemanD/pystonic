
import asyncio

from pystonic.conf import McpConfig, McpProxyConfig, NacosConfig
from pystonic.mcp.proxy import NacosMCPProxy


def main():
    mcp = NacosMCPProxy(
        McpConfig(
            proxy=McpProxyConfig(
                target='http://localhost:8000/mcp'
            ),
            nacos=NacosConfig(
                server_addr='localhost:8848',
                log_level='debug',
                retry_interval=5,
            ),
        )
    )
    asyncio.run(mcp.async_run())


main()
