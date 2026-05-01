from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote_plus

import toml
from loguru import logger
from pydantic import BaseModel, ConfigDict, SecretStr
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from pystonic import log
from pystonic.core import httpclient
from pystonic.log import LogConfig


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class DBConfig(BaseModel):
    # connection: str = "mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?charset={self.charset}"
    connection: str = "sqlite:///data/develop.db"
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
        if db_url.startswith("sqlite:"):
            file = Path(db_url.replace("sqlite:///", ""))
            file.parent.mkdir(parents=True, exist_ok=True)
        return db_url


class BaseAppConfig(BaseSettings):
    """Base App Configuration"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter=".",
        extra="ignore",
        frozen=True,
    )
    http_client: httpclient.HTTPClientConfig = httpclient.HTTPClientConfig()
    log: LogConfig = LogConfig()

    db: DBConfig = DBConfig()

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

    def init_hook(self):
        log.setup_logger(self.log)
        log.setup_logging(self.log)
        httpclient._DEFAULT_CONF = self.http_client

    @classmethod
    def new(cls, init_settings: Optional[Any] = None):
        config = super().model_validate(
            init_settings if init_settings is not None else cls.get_init_settings(),
        )
        config.init_hook()
        return config

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
