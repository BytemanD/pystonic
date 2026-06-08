import asyncio
from typing import Optional, Sequence

from loguru import logger
from fastmcp.server import create_proxy
from pydantic import BaseModel

from fastmcp.server.proxy import ProxyTool

from v2.nacos.ai.nacos_ai_service import GetMcpServerParam, NacosAIService
from v2.nacos import (
    RegisterInstanceParam,
    ClientConfigBuilder,
    NacosException,
    NacosNamingService,
)
from v2.nacos.ai.model.mcp.registry import ServerVersionDetail
from v2.nacos.ai.model.mcp.mcp import (
    McpTool,
    McpToolSpecification,
    McpServerBasicInfo,
    McpServerRemoteServiceConfig,
    McpEndpointSpec,
)
from v2.nacos.ai.model.ai_param import ReleaseMcpServerParam


TRANSPORT_MAP = {
    "stdio": "stdio",
    "sse": "mcp-sse",
    "streamable-http": "mcp-streamable",
}

TRANSPORT_PATH = {
    "sse": "/sse",
    "streamable-http": "/mcp",
}


class NacosSettings(BaseModel):
    server_addr: str = "localhost:8848"
    username: str = "nacos"
    password: str = ""

    namespace: str = "public"
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    meta: dict = {}
    connect_labels: dict = {}


class NacosMCPProxy:
    def __init__(
        self,
        target: str,
        name: str,
        nacos_settings: NacosSettings,
        group_name: str = "DEFAULT_GROUP",
        transport: str = "streamable-http",
        **kwargs,
    ):
        self.nacos_settings = nacos_settings
        self.transport = transport
        self.group_name = group_name
        self.client_config = self._create_nacos_client_config()

        self.backend = create_proxy(target, name=name)
        self._tools: Sequence[ProxyTool] = []

    async def _load_backend_tools(self) -> Sequence[ProxyTool]:
        self._tools = await self.backend.list_tools()

    def _create_nacos_client_config(self):
        ai_client_config_builder = (
            ClientConfigBuilder()
            .server_address(self.nacos_settings.server_addr)
            .username(self.nacos_settings.username)
            .password(self.nacos_settings.password)
            .namespace_id(self.nacos_settings.namespace)
        )
        if self.nacos_settings.access_key:
            ai_client_config_builder.access_key(self.nacos_settings.access_key)
        if self.nacos_settings.secret_key:
            ai_client_config_builder.secret_key(self.nacos_settings.secret_key)
        if self.nacos_settings.connect_labels:
            ai_client_config_builder.app_conn_labels(self.nacos_settings.connect_labels)

        return ai_client_config_builder.build()

    async def _load_nacos_client(self):
        client_config = self._create_nacos_client_config()
        self.nacos_ai_service = await NacosAIService.create_ai_service(client_config)
        self.nacos_naming_service = await NacosNamingService.create_naming_service(
            client_config
        )

    def get_service_name(self):
        return f"{self.backend.name}::{self.backend.version}"

    def run(self, port: int = 18002):
        asyncio.run(self.register_to_nacos(port=port))
        self.backend.run(transport=self.transport, host="0.0.0.0", port=port)

    async def _get_mcp_server_detail_info(self):
        server_detail_info = None
        try:
            server_detail_info = await self.nacos_ai_service.get_mcp_server(
                GetMcpServerParam(
                    mcp_name=self.backend.name, version=self.backend.version
                )
            )
        except NacosException as e:
            if not e.error_code == 404:
                raise e
        return server_detail_info

    async def register_to_nacos(self, port: int):
        await self._load_backend_tools()
        await self._load_nacos_client()

        endpoint_spec = McpEndpointSpec(
            type="REF",
            data={
                "serviceName": f"{self.backend.name}::{self.backend.version}",
                "groupName": "DEFAULT_GROUP",
            },
        )
        tools_spec = [
            McpTool(
                name=tool.name,
                description=tool.description,
                inputSchema=tool.parameters,
                outputSchema=tool.output_schema,
            )
            for tool in self._tools
        ]
        mcp_server_detail_info = await self._get_mcp_server_detail_info()
        if not mcp_server_detail_info:
            logger.warning("MCP server {} not found", self.backend.name)

        server_basic_info = McpServerBasicInfo(
            name=self.backend.name,
            versionDetail=ServerVersionDetail(version=self.backend.version),
            description=self.backend.instructions or self.backend.name,
            protocol=TRANSPORT_MAP.get(self.transport),
            frontProtocol=TRANSPORT_MAP.get(self.transport),
            remoteServerConfig=McpServerRemoteServiceConfig(
                exportPath=TRANSPORT_PATH.get(self.transport),
            ),
        )

        mcp_tool_specification = McpToolSpecification(tools=tools_spec)
        if not mcp_server_detail_info:
            await self.nacos_ai_service.release_mcp_server(
                ReleaseMcpServerParam(
                    server_spec=server_basic_info,
                    tool_spec=mcp_tool_specification,
                    mcp_endpoint_spec=endpoint_spec,
                )
            )

        service_meta_data = {"source": "nacos-mcp-proxy", **self.nacos_settings.meta}

        await self.nacos_naming_service.register_instance(
            request=RegisterInstanceParam(
                service_name=self.backend.name,
                group_name=self.group_name,
                ip="localhost",
                port=8000,
                ephemeral=True,
                metadata=service_meta_data,
            )
        )
