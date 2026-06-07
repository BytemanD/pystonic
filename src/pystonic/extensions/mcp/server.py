from loguru import logger
from nacos_mcp_wrapper.server.nacos_settings import NacosSettings
from nacos_mcp_wrapper.server.nacos_mcp import NacosMCP
from fastmcp import FastMCP

from pystonic.conf import McpConfig

nacos_settings = NacosSettings(
    SERVER_ADDR="localhost:8848",
    USERNAME="nacos",
    PASSWORD="nacos",
)

# 创建 MCP 服务端实例
mcp = NacosMCP("nacos-mcp-python", nacos_settings=nacos_settings, port=18001)


class McpServer:
    def __init__(self, conf: McpConfig):
        self.conf = conf
        if self.conf.enable_nacos:
            self.mcp = NacosMCP(
                name=self.conf.name,
                version=self.conf.version,
                instructions=self.conf.instructions,
                nacos_settings=NacosSettings(
                    SERVER_ADDR=self.conf.nacos.server_addr,
                    USERNAME=self.conf.nacos.username,
                    PASSWORD=self.conf.nacos.password.get_secret_value(),
                ),
                retry_interval=self.conf.nacos.retry_interval,
                host=self.conf.host,
                port=self.conf.port,
            )
        else:
            self.mcp = FastMCP(
                self.conf.name, instructions=conf.instructions, version=conf.version
            )

        self.tool = self.mcp.tool

    def run(self):
        if isinstance(self.mcp, NacosMCP):
            logger.info("starting nacos mcp server...")
            transport = (
                "streamable-http"
                if self.conf.version == "http"
                else self.conf.transport
            )
            self.mcp.run(transport)
        else:
            logger.info("starting mcp server...")
            self.mcp.run(
                transport=self.conf.transport,
                host=self.conf.host,
                port=self.conf.port,
            )


def nacos_proxy_wrapper(conf: McpConfig, tools):
    mcp = NacosMCP(
        name="xxxxxxxxxxxx",
        tools=tools,
        nacos_settings=NacosSettings(
            SERVER_ADDR=conf.nacos.server_addr,
            USERNAME=conf.nacos.username,
            PASSWORD=conf.nacos.password.get_secret_value(),
        ),
        retry_interval=conf.nacos.retry_interval,
        host=conf.host,
        port=conf.port,
    )
    mcp.run()
