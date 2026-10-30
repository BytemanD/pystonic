from sqlmodel import Field

from pystonic.orm.models import DBModel


class AgentSession(DBModel, table=True):
    __tablename__ = "agent_sessions"  # type: ignore

    user: str = Field(nullable=False, default="guest", description="所属用户")
    agent: str = Field(nullable=False, description="智能体 UUID")
    title: str = Field(nullable=True, default="", description="会话标题")
