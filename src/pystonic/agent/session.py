import sqlite3
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional

from agents import SQLiteSession
from loguru import logger
from pydantic import BaseModel

from pystonic.conf import CONF


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class AgentSession(BaseModel):
    session_id: str
    create_at: datetime
    update_at: datetime


class SessionNotFound(Exception):
    pass


class SessionHisotry:
    def __init__(self):
        self.store_file = Path(CONF.agent.session.store or CONF.store).joinpath(
            "session.db"
        )
        self.load()

    def load(self):
        self.store_file.parent.mkdir(parents=True, exist_ok=True)

    def get_session(self, session_id: Optional[str] = None):
        session_id = session_id or uuid.uuid4().hex
        return SQLiteSession(session_id, db_path=self.store_file)

    def _query_agent_session(self, session_id: Optional[str] = None):
        if not self.store_file:
            return
        conn = sqlite3.connect(self.store_file)
        conn.row_factory = sqlite3.Row
        sql = "SELECT * FROM agent_sessions"
        params = ()
        if session_id:
            sql += " WHERE session_id = ?"
            params = (session_id,)
        return conn.execute(sql, params)

    def get_agent_sessions(self, session_id: Optional[str] = None):
        sessions: List[AgentSession] = []
        cursor = self._query_agent_session(session_id=session_id)
        if not cursor:
            return sessions
        return [
            AgentSession(
                session_id=item["session_id"],
                create_at=item["created_at"],
                update_at=item["updated_at"],
            )
            for item in cursor
        ]

    def get_last_agent_session(self):
        items = self.get_agent_sessions()
        if not items:
            return
        return items[-1]

    def get_agent_session(self, session_id: str):
        items = self.get_agent_sessions(session_id=session_id)
        if not items:
            return
        return items[0]

    async def delete_agent_session(self, session_id: str):
        session_store = self.get_session(session_id=session_id)
        logger.info("clear session messages ...")
        await session_store.clear_session()
        session_store.close()
        logger.info("delete session ...")
        conn = sqlite3.connect(self.store_file)
        conn.execute(
            f"DELETE FROM {session_store.sessions_table} where session_id = ?",
            (session_id,),
        )
        conn.commit()
