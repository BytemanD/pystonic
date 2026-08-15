from pathlib import Path
from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel
from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from pystonic.conf import DBConfig


class TableColumn(BaseModel):
    name: str
    type: str
    nullable: bool = True
    default: str | None = None
    primary_key: bool = False
    foreign_key: str | None = None
    indexed: bool = False
    unique: bool = False


Base = declarative_base()

_engine: Optional[Engine] = None
_SessionLocal = None


def setup(config: DBConfig):
    global _engine, _SessionLocal

    if _engine is None:
        url = config.url
        is_sqlite = url.startswith("sqlite:")

        kwargs: dict[str, Any] = {"echo": config.echo}
        if not is_sqlite:
            kwargs["pool_size"] = config.pool_size
            kwargs["max_overflow"] = config.max_overflow
            kwargs["pool_timeout"] = config.pool_timeout
            kwargs["pool_recycle"] = config.pool_recycle

        _engine = create_engine(url, **kwargs)

    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine,
        )


def create_all_tables():
    assert _engine is not None

    if _engine.dialect.name == "sqlite":
        db_path = _engine.url.database
        if db_path and db_path != ":memory:":
            db_dir = Path(db_path).parent
            if db_dir.name:
                db_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Ensured SQLite database directory exists: {db_dir}")

    logger.info("Creating all tables...")
    Base.metadata.create_all(bind=_engine)
    logger.success("All tables created successfully.")


def get_all_databases() -> list[str]:
    assert _engine is not None

    dialect_name = _engine.dialect.name
    if dialect_name == "sqlite":
        return []
    elif dialect_name == "mysql":
        with _engine.connect() as conn:
            result = conn.execute(text("SHOW DATABASES"))
            return [row[0] for row in result]
    elif dialect_name == "postgresql":
        with _engine.connect() as conn:
            result = conn.execute(
                text("SELECT datname FROM pg_database WHERE datistemplate = false")
            )
            return [row[0] for row in result]
    else:
        raise NotImplementedError(
            f"Listing databases is not implemented for dialect: {dialect_name}"
        )


def get_all_tables() -> list[str]:
    assert _engine is not None

    inspector = inspect(_engine)
    return inspector.get_table_names()


def get_table_structure(table_name: str) -> list[TableColumn]:
    assert _engine is not None

    inspector = inspect(_engine)
    columns = inspector.get_columns(table_name)
    primary_key = inspector.get_pk_constraint(table_name)
    foreign_keys = inspector.get_foreign_keys(table_name)
    indexes = inspector.get_indexes(table_name)
    unique_constraints = inspector.get_unique_constraints(table_name)

    pk_cols = set(primary_key.get("constrained_columns", []))
    fk_map = {
        col: fk["referred_table"]
        for fk in foreign_keys
        for col in fk["constrained_columns"]
    }
    idx_map = {}
    for idx in indexes:
        for col in idx["column_names"]:
            idx_map[col] = idx.get("unique", False)

    unique_cols = set()
    for uc in unique_constraints:
        unique_cols.update(uc["column_names"])

    return [
        TableColumn(
            name=col["name"],
            type=str(col["type"]),
            nullable=col.get("nullable", True),
            default=col.get("default"),
            primary_key=col["name"] in pk_cols,
            foreign_key=fk_map.get(col["name"]),
            indexed=col["name"] in idx_map,
            unique=col["name"] in unique_cols or idx_map.get(col["name"], False),
        )
        for col in columns
    ]
