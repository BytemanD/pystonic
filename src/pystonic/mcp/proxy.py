from fastmcp.server import create_proxy
from loguru import logger

from pystonic.conf import McpConfig
from pystonic.core.system import get_first_non_loopback_ip
from pystonic.mcp.nacos_manager import NacosMcpManager

TRANSPORT_MAP = {
    "stdio": "stdio",
    "sse": "mcp-sse",
    "streamable-http": "mcp-streamable",
}


class NacosMCPProxy:
    def __init__(self, conf: McpConfig):
        self.conf = conf
        if not self.conf.proxy:
            raise ValueError("proxy url is required")
        self.backend = create_proxy(
            self.conf.proxy.target,
            name=self.conf.name,
            version=conf.version,
            client_log_level=conf.proxy.client_log_level,
        )
        self.nacos_manager = NacosMcpManager(self.conf.nacos)

    async def async_run(self):
        logger.info("load tools of MCP backend ...")
        tools = await self.backend.list_tools()
        logger.info("found {} tool(s)", len(tools))

        ip = (
            get_first_non_loopback_ip()
            if self.conf.host == "0.0.0.0"
            else self.conf.host
        )
        if not ip:
            raise ValueError("No non-loopback IP found")

        await self.nacos_manager.register_mcp_to_nacos(
            name=self.conf.name,
            version=self.conf.version,
            transport=self.conf.transport,
            ip=ip,
            port=self.conf.port,
            tools=tools,
            instructions=self.conf.instructions,
        )

        await self.backend.run_http_async(
            transport="streamable-http", host=self.conf.host, port=self.conf.port
        )
