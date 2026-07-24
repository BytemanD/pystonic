import asyncio
import logging
from typing import Optional

from fastmcp.tools import Tool
from loguru import logger
from maintainer.ai.model.nacos_mcp_info import (
    McpEndpointSpec,
    McpServerBasicInfo,
    McpServerRemoteServiceConfig,
    McpTool,
    McpToolSpecification,
)
from maintainer.ai.model.registry_mcp_info import ServerVersionDetail
from maintainer.ai.nacos_mcp_service import NacosAIMaintainerService
from maintainer.common.ai_maintainer_client_config_builder import (
    AIMaintainerClientConfigBuilder,
)
from v2.nacos import ClientConfigBuilder, NacosNamingService, RegisterInstanceParam

from pystonic.conf import NacosConfig

TRANSPORT_MAP = {
    "stdio": "stdio",
    "sse": "mcp-sse",
    "streamable-http": "mcp-streamable",
}


class NacosMcpManager:
    def __init__(self, conf: NacosConfig):
        self.conf = conf
        self.ai_client_config = (
            AIMaintainerClientConfigBuilder()
            .server_address(self.conf.server_addr)
            .username(self.conf.username)
            .password(self.conf.password.get_secret_value())
            .log_level(self.conf.log_level.upper())
            .app_conn_labels({})
            .build()
        )

        self.client_config = (
            ClientConfigBuilder()
            .namespace_id(self.conf.namespace)
            .server_address(self.conf.server_addr)
            .username(self.conf.username)
            .password(self.conf.password.get_secret_value())
            .log_level(self.conf.log_level.upper())
            .app_conn_labels({})
            .build()
        )

    async def register_mcp_to_nacos(
        self,
        name: str,
        version: str,
        transport: str,
        ip: str,
        port: int,
        tools: list[Tool] = [],
        instructions: Optional[str] = None,
    ):
        service_name = f"{name}::{version}"

        mcp_service = await NacosAIMaintainerService.create_mcp_service(
            self.ai_client_config
        )
        naming_service = await NacosNamingService.create_naming_service(
            self.client_config
        )

        mcp_type = TRANSPORT_MAP.get(transport)
        endpoint_spec = McpEndpointSpec(
            type="REF",
            data={
                "serviceName": service_name,
                "groupName": self.conf.group_name,
                "namespaceId": self.conf.namespace,
            },
        )
        server_basic_info = McpServerBasicInfo(
            name=name,
            versionDetail=ServerVersionDetail(version=version),
            description=instructions or name,
            protocol=mcp_type,
            frontProtocol=mcp_type,
            remoteServerConfig=McpServerRemoteServiceConfig(exportPath="/mcp"),
        )

        mcp_service_detail = None
        try:
            mcp_service_detail = await mcp_service.get_mcp_server_detail(
                self.conf.namespace, name, version
            )
        except Exception as e:
            logger.warning("get mcp server detail failed: {}", e)
        else:
            logger.info("mcp_service_detail: {}", mcp_service_detail.model_dump_json())

        mcp_tool_specification = McpToolSpecification(
            tools=[
                McpTool(
                    name=tool.name,
                    description=tool.description,
                    inputSchema=tool.parameters,
                    outputSchema=tool.output_schema,
                )
                for tool in tools
            ]
        )
        if mcp_service_detail:
            logger.info(
                "mcp service exists, detail {}", mcp_service_detail.model_dump_json()
            )
            logger.info("update mcp server: {}")
            await mcp_service.update_mcp_server(
                naming_service.namespace_id,
                name,
                True,
                server_basic_info,
                mcp_tool_specification,
                endpoint_spec,
            )
        else:
            logger.info("create mcp server: {}", name)
            await mcp_service.create_mcp_server(
                naming_service.namespace_id,
                name,
                server_basic_info,
                mcp_tool_specification,
                endpoint_spec,
            )

        register_instance_param = RegisterInstanceParam(
            group_name=self.conf.group_name,
            service_name=service_name,
            ip=ip,
            port=port,
            ephemeral=True,
            metadata={"source": f"pystonic-mcp-{version}"},
        )
        logger.info("register instance: {}", register_instance_param.model_dump_json())
        await naming_service.register_instance(request=register_instance_param)

        logger.info("subscribe ...")
        asyncio.create_task(self._subscribe(mcp_service, name, version))

    async def _subscribe(
        self, mcp_service: NacosAIMaintainerService, name: str, version: str
    ):
        while True:
            try:
                await asyncio.sleep(30)
            except asyncio.TimeoutError:
                logging.debug("Timeout occurred")
            except asyncio.CancelledError:
                return
            try:
                server_detail_info = await mcp_service.get_mcp_server_detail(
                    self.conf.namespace, name, version
                )
                logger.info(
                    "mcp server deteail: {}", server_detail_info.model_dump_json()
                )
            except Exception as e:
                logging.error("get mcp server detail failed: {}", e)
