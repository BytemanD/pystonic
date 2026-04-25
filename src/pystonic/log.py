import sys
from typing import List, Literal, Optional

from loguru import logger
from pydantic import BaseModel, ConfigDict

from pystonic import context

VERBOSE_LEVELS = ["ERROR", "WARNING", "INFO", "DEBUG", "TRACE"]
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


def setup_logger(
    config: LogConfig, versbose: Optional[int] = None, remove: bool = False
):
    """Setup logging configuration."""
    if remove:
        logger.remove()
    if versbose is not None:
        logger.add(
            sys.stdout,
            level=VERBOSE_LEVELS[min(len(VERBOSE_LEVELS) - 1, versbose)],
            format=config.format,
            colorize=True,
        )
    if config.file:
        logger.add(
            config.file,
            level=config.level.upper(),
            format=config.format,
            colorize=config.colorize,
            rotation=config.rotation,
            retention=config.retention,
            compression=config.compression,
        )

    def _context_patcher(record):
        extra_keys = ["trace"] + config.custom_extra
        ctx_value = " ".join([str(context.getvar(x) or "-") for x in extra_keys])
        record.update(extra={"context": ctx_value or "-"})

    logger.configure(
        extra={"context": "-"},
        patcher=_context_patcher,
    )
