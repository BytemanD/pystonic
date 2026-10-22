from pydantic import BaseModel


class Knowledge(BaseModel):
    uuid: str
    path: str = ""
