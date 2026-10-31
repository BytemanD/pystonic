import os
import socket
from collections.abc import Sequence
from pathlib import Path
from typing import Literal, Union, get_args, get_origin
from urllib.parse import quote_plus

import dotenv
import toml
from loguru import logger
from pydantic import BaseModel, HttpUrl, SecretStr
from pydantic_core import PydanticUndefined
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from pystonic.utils.system import user_app_data

dotenv.load_dotenv()

DEFAULT_CONF_FILES = [
    Path("etc", "app.toml"),
    user_app_data().joinpath("app.toml"),
]
DEFAULT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}:{line}</cyan> <level>[{extra[context]}]</level> - <level>{message}</level>"
)


class FrozenBaseModel(BaseModel):
    model_config = SettingsConfigDict(
        frozen=True,
    )


class LogConfig(FrozenBaseModel):
    level: Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR"] = "WARNING"
    file: str | None = None
    format: str = DEFAULT_FORMAT
    colorize: bool | None = None
    encoding: str = "utf-8"
    rotation: str = "10 MB"
    retention: str = "30 days"
    compression: str = "zip"
    custom_extra: list[str] = []
    enqueue: bool = True
    intercept_logging: bool = False

    console_verbose: int = 0


class HTTPClientConfig(FrozenBaseModel):
    log_response_detail: bool = True
    timeout: int = 60
    retries: int = 0


class DBConfig(FrozenBaseModel):
    # connection: str = "mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset={charset}"
    connection: str = f"sqlite:///{user_app_data().joinpath('db.sqlite')}"
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: SecretStr = SecretStr("")
    database: str = "develop"
    charset: str = "utf8mb4"

    # Connection pool settings
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False

    disable_warning: bool = False

    @property
    def url(self):
        db_url = self.connection.format(
            host=self.host,
            port=self.port,
            user=quote_plus(self.user),
            password=quote_plus(self.password.get_secret_value()),
            database=self.database,
            charset=self.charset,
        )
        return db_url

    def is_sqlite(self):
        return self.connection.startswith("sqlite:")

    def engine_params(self):
        params = {
            "echo": self.echo,
            "pool_size": self.pool_size,
            "pool_recycle": self.pool_recycle,
        }
        if not self.is_sqlite():
            params.update(
                pool_timeout=self.pool_timeout, max_overflow=self.max_overflow
            )
        return params


# class AsgiConfig(FrozenBaseModel):
#     name: str = "Pystonic ASGI"
#     summary: str = ""
#     description: str = ""
#     version: str = "0.1.0"

#     docs_url: str = "/docs"
#     redoc_url: str = "/redoc"
#     openapi_prefix: str = ""
#     openapi_url: str = "/openapi.json"


class JWTConfig(FrozenBaseModel):
    key: str = "this-is-a-test-key-please-change-in-prod"
    expired: int = 3600
    algorithms: list[str] = ["HS256"]


class NacosConfig(FrozenBaseModel):
    server_addr: str = "localhost:8848"
    username: str = "nacos"
    password: SecretStr = SecretStr("nacos")

    namespace: str = "public"
    group_name: str = "DEFAULT_GROUP"

    retry_interval: int | None = 10
    log_level: str = "info"


class McpProxyConfig(FrozenBaseModel):
    target: str | None = ""
    client_log_level: str = "info"


class McpConfig(FrozenBaseModel):
    """Mcp Server Configuration"""

    name: str = "pystonic-mcp-server"
    instructions: str = ""
    transport: Literal["stdio", "http", "sse", "streamable-http"] = "streamable-http"
    version: str = "1.0.0"

    host: str = "0.0.0.0"  # nosec B104 - 服务端默认监听所有网卡，部署时可显式收敛
    port: int = 18000

    enable_nacos: bool = False
    nacos: NacosConfig = NacosConfig()
    proxy: McpProxyConfig | None = None


class AgentSessionConfig(FrozenBaseModel):
    store: str | None = None


class LLMProviderConfig(BaseModel):
    base_url: str
    api_key: SecretStr
    models: list[str] = []


class AgentConfig(FrozenBaseModel):
    system_prompt: str = "你是一个专业的AI助手"
    max_turns: int = 100
    openai_timeout: int = 180
    session: AgentSessionConfig = AgentSessionConfig()
    # Usage: db_config, mysql+pymysql://xxxx, sqlite:///xxxx
    checkpoint_connection: str = (
        f"sqlite:///{user_app_data().joinpath('agent', 'checkpoint.sqlite')}"
    )
    providers: dict[str, LLMProviderConfig] = {}


class SchedulerConfig(FrozenBaseModel):
    background_max_workers: int = 10


class S3Config(FrozenBaseModel):
    endpoint_url: str = ""
    region: str = ""
    access_key_id: str = ""
    secret_access_key: str = ""
    session_token: str = ""
    bucket: str = ""


class RedisConfig(FrozenBaseModel):
    url: str = ""


class UpstashConfig(FrozenBaseModel):
    url: str = "https://blob.upstash.io/v1/credentials"
    token: str = ""


class MilvusConfig(FrozenBaseModel):
    uri: str = ""
    token: str = ""
    timeout: int = 300
    user: str = ""
    password: str = ""
    db_name: str = ""
    default_collection: str = "default"
    embedding_model: str = "all-MiniLM-L6-v2"
    # 有 GPU 可改为 'cuda:0'
    embedding_device: str = "cpu"
    # 一致性级别
    consistency_level: str = "Session"


class ChromaConfig(FrozenBaseModel):
    persist_directory: str | None = None
    host: str | None = None
    port: int | None = None
    default_collection: str = "default"
    splite_thresold: int = 1000


class BaseAppConfig(BaseSettings):
    """Base App Configuration"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        frozen=True,
        toml_file=os.getenv("CONF_FILE") or DEFAULT_CONF_FILES,
    )
    hostname: str = socket.gethostname()
    # global config
    store: str = "data"

    log: LogConfig = LogConfig()
    db: DBConfig = DBConfig()
    http_client: HTTPClientConfig = HTTPClientConfig()
    # asgi: AsgiConfig = AsgiConfig()
    jwt: JWTConfig = JWTConfig()
    mcp: McpConfig = McpConfig()
    s3: S3Config = S3Config()
    redis: RedisConfig = RedisConfig()
    upstash: UpstashConfig = UpstashConfig()
    milvus: MilvusConfig = MilvusConfig()
    chroma: ChromaConfig = ChromaConfig()
    agent: AgentConfig = AgentConfig()

    scheduler: SchedulerConfig = SchedulerConfig()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ):
        # 优先级（先者优先）：init > 环境变量 > .env > toml > file_secret
        # 环境变量出问题（如 shell 中存在 AGENT=1）将直接抛 ValidationError，
        # 由调用方处理；.env 走独立 dotenv 源，同样严格：值不合法直接抛错
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

    def get_conf_files(self):
        """获取当前生效的配置文件路径（setup(toml_file=...) 指定的或默认文件）"""
        file_paths = []
        configured = self.model_config.get("toml_file") or []
        if isinstance(configured, (str, Path)):
            file_paths = [Path(configured)]
        elif configured and isinstance(configured, (list, Sequence)):
            file_paths = [Path(str(x)) for x in configured if os.path.exists(str(x))]

        if not file_paths:
            file_paths.append(DEFAULT_CONF_FILES[-1])
        return file_paths

    def save(self, exclude_defaults=False, encoding="utf-8"):
        file_paths = self.get_conf_files()
        if not file_paths:
            raise ValueError("conf file not exists")
        file_path = file_paths[0]
        # debug 日志仍走 model_dump_json（SecretStr 保持掩码）
        logger.debug("saving config: {}", self.model_dump_json())
        file_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("保存配置 {}", file_path)
        with open(file_path, "w", encoding=encoding) as f:
            toml.dump(
                _plain_data(self, exclude_defaults=exclude_defaults),
                f,
            )


def _strip_optional(annotation):
    if get_origin(annotation) is Union:
        args = [a for a in get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return annotation


def _plain_value(value, annotation, exclude_defaults: bool):
    """递归展开 model_dump(mode="json") 的等价物，但 SecretStr 输出真实值"""
    annotation = _strip_optional(annotation)
    if isinstance(value, SecretStr):
        return value.get_secret_value()
    if isinstance(value, BaseModel):
        return _plain_data(value, exclude_defaults=exclude_defaults)
    if isinstance(value, dict):
        inner = _inner_annotation(annotation)
        return {k: _plain_value(v, inner, exclude_defaults) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        inner = _inner_annotation(annotation)
        return [_plain_value(v, inner, exclude_defaults) for v in value]
    return value


def _inner_annotation(annotation):
    if get_origin(annotation) in (dict, list, tuple, set):
        args = get_args(annotation)
        if args:
            return args[-1]
    return type(None)


def _plain_data(model: BaseModel, exclude_defaults: bool = False) -> dict:
    """导出可写回 toml 的 dict：SecretStr 还原真实值，其余与 model_dump(mode="json") 一致"""
    plain = {}
    for name, field in type(model).model_fields.items():
        raw = getattr(model, name, None)
        if exclude_defaults:
            default = field.default
            if default is not PydanticUndefined and raw == default:
                continue
        plain[name] = _plain_value(raw, field.annotation, exclude_defaults)
    return plain


CONF = BaseAppConfig()
