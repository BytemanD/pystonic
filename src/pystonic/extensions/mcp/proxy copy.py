from nacos_mcp_wrapper.server.nacos_settings import NacosSettings
from nacos_mcp_wrapper.server.nacos_mcp import NacosMCP
from fastmcp import FastMCP

from pystonic.conf import McpConfig


class NacosMCPProxy(NacosMCP):
    def __init__(self, backend_url: str, **kwargs):
        super().__init__(**kwargs)

        self.backend = FastMCP.as_proxy(backend_url, name="HttpProxyServer")
        self._mcp_server.list_tools = self.backend._mcp_server.list_tools
        self._mcp_server.call_tool = self.backend._mcp_server.call_tool
        # import inspect
        # # breakpoint()
        # for member in inspect.getmembers(self.backend):
        #     if member[0].startswith('_') or :
        #         continue
        #     print('setting member:', member[0])
        #     try:
        #         setattr(self, member[0], getattr(self.backend, member[0]))
        #     except Exception as e:
        #         breakpoint()
        #         logger.error(e)


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
