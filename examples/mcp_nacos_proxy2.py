import asyncio
from typing import Any, Optional
import uuid

from fastmcp import FastMCP
from loguru import logger
from nacos_mcp_wrapper.server.nacos_settings import NacosSettings
from nacos_mcp_wrapper.server.nacos_mcp import NacosMCP
from fastmcp.server import create_proxy
from pystonic.mcp import server

from pystonic.conf import McpConfig
from pystonic.mcp.proxy import NacosMCPProxy

from v2.nacos.ai.nacos_ai_service import NacosAIService
from nacos_mcp_wrapper.server.nacos_server import NacosServer

conf = McpConfig(
    name='nacos-mcp-python2',
    instructions="this is nacos mcp server demo",
    transport="streamable-http",
    enable_nacos=True,
    prroxy='http://localhost:18000/mcp',
    port=18001,
)

from mcp.types import Tool as MCPTool

class NacosMCPProxy(NacosMCP):
    def __init__(self, backend_url: str, name: str=None, **kwargs):
        self.backend = create_proxy(
            backend_url,
            name=name,
            client_log_level='debug',
            # port=18001,
        )
        # self.backend.run_async()

        super().__init__(
            name=name,
            tools=self.backend.list_tools(),
            **kwargs)
        # for tool in await self.backend.list_tools():
        #     tool.
        # self._tool_manager.add_tool(
            
        # )

    async def list_tools(self) -> list[MCPTool]:
        logger.info('111111111111')
        tools = await self.backend.list_tools()
        for tool in tools:
            logger.info('tool:   {}', tool)
        return [x.to_mcp_tool() for x in tools]

    # async def call_tool(self, name: str, arguments: dict[str, Any]):
    #     print('                       ')
    #     print(name, arguments)
    #     print('                       ')

    #     return self.backend.providers[0].call_tool(name, arguments)
    #     return await self.backend.call_tool(name, arguments)

    async def get_tool(self, name: str, version):
        logger.info('-------------- version: {}', version)
        # return await self.backend.providers[0].get_tool(name, version)
        
        return (await self.backend.get_tool(name, version)).to_mcp_tool()

    async def list_resources(self):
        result = await self.backend.providers[0].list_resources(
        )
        logger.info('-------------- list_resources: {}', result)
        
        return result

    # async def get_tool(
    #     self, name: str, version
    # ) -> MCPTool | None:
    #     tool = await self.backend.get_tool(
    #         name, version=version
    #     )
    #     return tool.to_mcp_tool()



backend = create_proxy(
    'http://localhost:8000/mcp',
    client_log_level='debug',
    name='pytthon-mcp-demo',
)


async def load_backend_tools():
    return await backend.list_tools()


nacos_settings = NacosSettings(
    SERVER_ADDR="localhost:8848",
    USERNAME="nacos",
    PASSWORD="nacos",
    NAMESPACE="public",
)

# mcp = NacosMCPProxy(
#     'http://localhost:18000/mcp',
#     name='NacosMCPProxy',
#     nacos_settings=NacosSettings(
#         SERVER_ADDR="localhost:8848",
#         USERNAME="nacos",
#         PASSWORD="nacos",
#         NAMESPACE="public",
#     ),
#     port=18001,
# )

def main():
    tools = asyncio.run(load_backend_tools())
    logger.info('tools:   {}', tools)
    for tool in tools:
        logger.info('tool:   {}', tool)
    mcp = NacosMCP(name='pytthon-mcp-demo', nacos_settings=nacos_settings, tools=tools,
                   port=18002)
    # mcp._mcp_server.list_tools
    mcp._mcp_server._tmp_tools[tools[0].name] = tools[0]
    mcp.run(transport="streamable-http",)
    


main()
