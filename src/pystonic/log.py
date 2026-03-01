import sys
from functools import partial
from typing import Dict, List, Optional

from loguru import logger
from pydantic import BaseModel

from pystonic import context

DEFAULT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}:{line}</cyan> <level>[{extra[context]}]</level> - <level>{message}</level>"
)


class LogConfig(BaseModel):
    level: str = "INFO"
    file: Optional[str] = None
    format: str = DEFAULT_FORMAT
    colorize: Optional[bool] = None
    custom_extra: List[str] = []


def _context_patcher(extra_keys: List[str], record: Dict):
    ctx_value = " ".join([str(context.getvar(x) or "-") for x in extra_keys])
    record.update(extra={"context": ctx_value or "-"})


def setup_logger(config: LogConfig):
    """Setup logging configuration."""
    kwargs = {}
    if config.format:
        kwargs["format"] = config.format
    if config.colorize:
        kwargs["colorize"] = config.colorize
    logger.remove()
    logger.add(
        config.file if config.file else sys.stdout,
        level=config.level.upper(),
        **kwargs,
    )
    logger.configure(
        extra={"context": "-"},
        patcher=partial(_context_patcher, ["trace"] + config.custom_extra),
    )


def add_console_handler(level: str, config: LogConfig):
    kwargs = {}
    if config.format:
        kwargs["format"] = config.format
    if config.colorize:
        kwargs["colorize"] = config.colorize
    logger.add(sys.stdout, level=level.upper(), **kwargs)
