from pydantic import BaseModel


class VectorDocument(BaseModel):
    id: int | str
    content: str | None = None
    metadata: dict = {}
    score: float | None = None
