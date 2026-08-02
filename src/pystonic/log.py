import logging
import os
import sys
from pathlib import Path

from loguru import logger

from pystonic import context
from pystonic.conf import CONF

VERBOSE_LEVELS = ["WARNING", "INFO", "DEBUG", "TRACE"]


def setup_logger(remove: bool = False):
    """Setup logging configuration."""
    if remove:
        logger.remove()
    verbose = os.getenv("LOG_VERBOSE", 0)
    versbose = int(verbose) if verbose is not None else 1
    logger.add(
        sys.stdout,
        level=VERBOSE_LEVELS[min(len(VERBOSE_LEVELS) - 1, versbose)],
        format=CONF.log.format,
        colorize=True,
    )
    if CONF.log.file:
        Path(CONF.log.file).parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            CONF.log.file,
            level=CONF.log.level.upper(),
            format=CONF.log.format,
            colorize=CONF.log.colorize,
            rotation=CONF.log.rotation,
            retention=CONF.log.retention,
            compression=CONF.log.compression,
            encoding=CONF.log.encoding,
        )

    def _context_patcher(record):
        extra_keys = ["trace"] + CONF.log.custom_extra
        ctx_value = " ".join([str(context.getvar(x) or "-") for x in extra_keys])
        record.update(extra={"context": ctx_value or "-"})

    logger.configure(
        extra={"context": "-"},
        patcher=_context_patcher,
    )


def setup_logging():
    logging.basicConfig(
        filename=CONF.log.file,
        level="DEBUG" if CONF.log.level == "TRACE" else CONF.log.level,
        format="%(asctime)s | %(levelname)s | %(name)s - %(message)s",
        encoding=CONF.log.encoding,
    )
