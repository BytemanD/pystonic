import sys
from typing import List, Literal, Optional

from loguru import logger
from pydantic import BaseModel, ConfigDict

from pystonic import context

DEFAULT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}:{line}</cyan> <level>[{extra[context]}]</level> - <level>{message}</level>"
)


class LogConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    level: Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR"] = "WARNING"
    file: Optional[str] = None
    format: str = DEFAULT_FORMAT
    colorize: Optional[bool] = None
    rotation: str = "10 MB"
    retention: str = "30 days"
    compression: str = "zip"
    custom_extra: List[str] = []


def setup_logger(config: LogConfig):
    """Setup logging configuration."""
    kwargs = {}
    if config.format:
        kwargs["format"] = config.format
    if config.colorize:
        kwargs["colorize"] = config.colorize
    if config.file:
        kwargs["rotation"] = config.rotation
        kwargs["retention"] = config.retention
        kwargs["compression"] = config.compression
    logger.remove()
    logger.add(
        config.file if config.file else sys.stdout,
        level=config.level.upper(),
        **kwargs,
    )

    def _context_patcher(record):
        extra_keys = ["trace"] + config.custom_extra
        ctx_value = " ".join([str(context.getvar(x) or "-") for x in extra_keys])
        record.update(extra={"context": ctx_value or "-"})

    logger.configure(
        extra={"context": "-"},
        patcher=_context_patcher,
    )


def add_console_handler(level: str, config: LogConfig):
    kwargs = {}
    if config.format:
        kwargs["format"] = config.format
    if config.colorize:
        kwargs["colorize"] = config.colorize
    logger.add(sys.stdout, level=level.upper(), **kwargs)
