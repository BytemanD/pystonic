from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

from pystonic.log import LogConfig, setup_logger
from pystonic.utils import httpclient


class BaseAppConfig(BaseSettings):
    """Base App Configuration"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )

    http_client: httpclient.HTTPClientConfig = httpclient.HTTPClientConfig()
    log: LogConfig = LogConfig()

    @classmethod
    def setup(cls, values: Optional[dict] = None):
        config = cls.model_validate(values or {})
        setup_logger(config.log)

        httpclient._DEFAULT_CONF = config.http_client
        return config
