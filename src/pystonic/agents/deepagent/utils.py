from pathlib import Path

from langgraph.checkpoint.mysql.asyncmy import AsyncMySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from loguru import logger

from pystonic.common.conf import CONF


def get_checkpointer_saver():
    if CONF.agent.checkpoint_connection == "db_config":
        conn_string = CONF.db.url
    else:
        conn_string = CONF.agent.checkpoint_connection

    if conn_string.startswith(("mysql:", "mysql+pymysql:")):
        logger.info("use mysql checkpoint saver")
        return AsyncMySaver.from_conn_string(conn_string)

    elif conn_string.startswith("sqlite:"):
        sqlite_path = conn_string.removeprefix("sqlite:///")
        logger.info("use sqlite checkpoint saver")
        logger.debug("sqlite path: {}", sqlite_path)
        if sqlite_path != ":memory:":
            Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        return AsyncSqliteSaver.from_conn_string(sqlite_path)

    raise RuntimeError("checkpoint connection is inavlid")
