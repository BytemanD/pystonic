import os
from pathlib import Path
from typing import Dict, List, Literal, Optional, Union
from urllib.parse import quote_plus

import toml
from loguru import logger
from pydantic import BaseModel, HttpUrl, SecretStr
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from pystonic import app_name

DEFAULT_CONF_FILE = [
    Path("etc", "app.toml"),
    Path.home().joinpath(".config", app_name(), "app.toml"),
]
DEFAULT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}:{line}</cyan> <level>[{extra[context]}]</level> - <level>{message}</level>"
)


class LogConfig(BaseModel):
    level: Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    file: Optional[str] = None
    format: str = DEFAULT_FORMAT
    colorize: Optional[bool] = None
    encoding: str = "utf-8"
    rotation: str = "10 MB"
    retention: str = "30 days"
    compression: str = "zip"
    custom_extra: List[str] = []
    enqueue: bool = True
    intercept_logging: bool = True


class HTTPClientConfig(BaseModel):
    log_response_detail: bool = True
    timeout: int = 60
    retries: int = 0


class DBConfig(BaseModel):
    # connection: str = "mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset={charset}"
    connection: str = "sqlite://./data/develop.db"
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
        if self.is_sqlite():
            file = Path(db_url.replace("sqlite://", ""))
            file.parent.mkdir(parents=True, exist_ok=True)
        return db_url

    def is_sqlite(self):
        return self.connection.startswith("sqlite:")


class AsgiConfig(BaseModel):
    name: str = "Pystonic ASGI"
    summary: str = ""
    description: str = ""
    version: str = "0.1.0"

    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_prefix: str = ""
    openapi_url: str = "/openai.json"


class NacosConfig(BaseModel):
    server_addr: str = "localhost:8848"
    username: str = "nacos"
    password: SecretStr = SecretStr("nacos")

    namespace: str = "public"
    group_name: str = "DEFAULT_GROUP"

    retry_interval: Optional[int] = 10
    log_level: str = "info"


class McpProxyConfig(BaseModel):
    target: Optional[str] = ""
    client_log_level: str = "info"


class McpConfig(BaseModel):
    """Mcp Server Configuration"""

    name: str = "pystonic-mcp-server"
    instructions: str = ""
    transport: Literal["stdio", "http", "sse", "streamable-http"] = "streamable-http"
    version: str = "1.0.0"

    host: str = "0.0.0.0"
    port: int = 18000

    enable_nacos: bool = False
    nacos: NacosConfig = NacosConfig()
    proxy: Optional[McpProxyConfig] = None


class ProviderConfig(BaseModel):
    base_url: HttpUrl
    api_key: str = ""
    models: List[str] = []
    openai_use_responses: bool = True
    extra_body: dict = {}

    def set_enable_thinking(self, enable: bool):
        if not self.extra_body:
            self.extra_body = {}
        self.extra_body["enable_thinking"] = enable


class AgentSessionConfig(BaseModel):
    store: Optional[str] = None


class AgentConfig(BaseModel):
    system_prompt: str = "你是一个专业的AI助手"
    max_turns: int = 100
    openai_timeout: int = 180
    session: AgentSessionConfig = AgentSessionConfig()
    # stream: bool = True
    default_provider: str = "zipu/glm-4.7-flash"
    providers: Dict[str, ProviderConfig] = {
        "alibaba": ProviderConfig(
            base_url=HttpUrl("https://dashscope.aliyuncs.com/compatible-mode/v1"),
            api_key="",
            models=["qwen-plus"],
        ),
        "zipu": ProviderConfig(
            base_url=HttpUrl("https://open.bigmodel.cn/api/paas/v4"),
            models=["glm-4.7-flash"],
            openai_use_responses=False,
            api_key="",
        ),
    }
    disable_tracing: bool = True

    def get_provider(self, model: Optional[str] = None) -> ProviderConfig:
        provider, model_name = (model or self.default_provider).split("/")

        if provider not in self.providers:
            raise ValueError(f"Provider '{provider}' not found in configuration")
        if model_name not in self.providers[provider].models:
            raise ValueError(f"model '{model_name}' not found in configuration")

        return self.providers[provider]


class HueyConfig(BaseModel):
    name: str = "huey app"
    storage: Literal["db"] = "db"
    database: str | None = None
    workers: int = 1
    periodic: bool = (True,)
    backoff: float = 1.15
    max_delay: float = 10
    scheduler_interval: int = 1
    # initial_delay: float = 0.1
    # worker_type: str = WORKER_THREAD
    # check_worker_health: bool = True
    # health_check_interval: int = 10
    # flush_locks: bool = False
    # max_tasks: int = None
    # shutdown_timeout: int | None = None
    # graceful_signal: str = "INT"


class BaseAppConfig(BaseSettings):
    """Base App Configuration"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter=".",
        extra="ignore",
        frozen=True,
        toml_file=os.getenv("CONF_FILE") or DEFAULT_CONF_FILE,
    )

    # global config
    store: str = "data"

    log: LogConfig = LogConfig()
    db: DBConfig = DBConfig()
    http_client: HTTPClientConfig = HTTPClientConfig()
    asgi: AsgiConfig = AsgiConfig()
    mcp: McpConfig = McpConfig()
    agent: AgentConfig = AgentConfig()

    huey: HueyConfig = HueyConfig()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ):
        return (
            env_settings,
            dotenv_settings,
            file_secret_settings,
            TomlConfigSettingsSource(settings_cls),
            init_settings,
        )

    def save(self, exclude_defaults=False, encoding="utf-8"):
        file_path = self.get_conf_file()
        if not file_path:
            logger.warning("No configuration file specified, skipping save")
            return

        logger.debug("saving config: {}", self.model_dump_json())
        file_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("保存配置 {}", file_path)
        with open(file_path, "w", encoding=encoding) as f:
            toml.dump(
                self.model_dump(mode="json", exclude_defaults=exclude_defaults), f
            )

    @classmethod
    def get_conf_file(cls) -> Optional[Path]:
        files = cls.model_config.get("toml_file") or []
        if not files:
            return None

        if isinstance(files, (Path, str)):
            return Path(files)
        for file in files:
            if Path(file).exists():
                return Path(file)

        return Path(files[0])

    @classmethod
    def get_init_settings(cls) -> Dict:
        return getattr(cls, "_init_settings", {})

    @classmethod
    def setup(
        cls,
        init_settings: Optional[Dict] = None,
        toml_file: Optional[Union[Path, List[Path]]] = None,
    ):
        """初始化配置"""
        if init_settings is not None:
            cls._init_settings = init_settings
        if toml_file is not None:
            cls.model_config["toml_file"] = (
                toml_file if isinstance(toml_file, list) else [toml_file]
            )


CONF = BaseAppConfig()
