from datetime import datetime

from pydantic import BaseModel


class FilePath(BaseModel):
    name: str
    path: str
    is_dir: bool
    modify_time: datetime
    size: int = 0
    create_time: datetime | None = None
