from loguru import logger
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from pystonic.conf import DBConfig

Base = declarative_base()

_engine: Engine = None
_SessionLocal = None


def setup(config: DBConfig):
    global _engine, _SessionLocal

    if _engine is None:
        _engine = create_engine(
            config.url,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout,
            pool_recycle=config.pool_recycle,
            echo=config.echo,
        )

    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine,
        )


def create_all_tables():
    assert _engine is not None

    logger.info("Creating all tables...")
    Base.metadata.create_all(bind=_engine)
    logger.success("All tables created successfully.")
