from pathlib import Path
from typing import Dict, Optional

import toml
from loguru import logger
from pydantic import BaseModel, ConfigDict
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from pystonic import log
from pystonic.log import LogConfig
from pystonic.utils import httpclient


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True)


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

    @classmethod
    def get_conf_file(cls) -> Optional[Path]:
        for file in cls.model_config.get("toml_file") or []:
            if file.exists():
                return file
        return None

    def save(self, exclude_defaults=False, encoding="utf-8"):
        files = self.model_config.get("toml_file") or []
        if not files:
            logger.warning("No configuration file specified, skipping save")
            return
        if isinstance(files, list):
            file_path = files[0]
            for file in files:
                if file.exists():
                    file_path = file
                    break
        else:
            file_path = Path(files)
        if not file_path:
            return
        logger.debug("saving config: {}", self.model_dump_json())
        file_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("保存配置 {}", file_path)
        with open(file_path, "w", encoding=encoding) as f:
            toml.dump(
                self.model_dump(mode="json", exclude_defaults=exclude_defaults), f
            )

    def setup(self):
        log.setup_logger(self.log)
        httpclient._DEFAULT_CONF = self.http_client

    @classmethod
    def init(cls, init_settings: Dict = {}):
        config = cls.model_validate(init_settings or getattr(cls, "_init_settings", {}))
        config.setup()
        return config


def setup(init_settings={}, toml_file=None):
    BaseAppConfig._init_settings = init_settings
    if toml_file:
        BaseAppConfig.model_config["toml_file"] = (
            toml_file if isinstance(toml_file, list) else [toml_file]
        )
