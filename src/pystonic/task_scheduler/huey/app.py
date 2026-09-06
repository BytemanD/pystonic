from pathlib import Path

from huey import SqliteHuey
from huey.contrib.sql_huey import SqlHuey

from pystonic.conf import CONF
from pystonic.task_scheduler.huey.storage import SqlStorageWithTablePrefix


def create_huery():
    if CONF.huey.storage == "db":
        db_url = CONF.db.url
        if db_url.startswith("sqlite:"):
            filename = db_url.replace("sqlite://", "")
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            return SqliteHuey(name=CONF.huey.name, filename=filename)
        elif db_url.startswith("mysql"):
            database = CONF.db.url.replace("+pymysql", "")
            return SqlHuey(
                name=CONF.huey.name,
                database=database,
                storage_class=SqlStorageWithTablePrefix,
                create_tables=False,
            )

    raise ValueError(f"storage '{CONF.huey.storage}' not support")
