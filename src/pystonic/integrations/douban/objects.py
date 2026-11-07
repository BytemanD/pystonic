from pydantic import BaseModel


class Cast(BaseModel):
    id: str | None = None
    name: str | None = None
    alt: str | None = None
    avatars: dict | None = None


class Director(BaseModel):
    id: str | None = None
    name: str | None = None
    alt: str | None = None
    avatars: dict | None = None


class Rating(BaseModel):
    max: int | None = None
    average: float | None = None
    stars: int | None = None
    min: int | None = None


class Subject(BaseModel):
    id: str
    title: str
    original_title: str
    year: str
    alt: str
    subtype: str
    directors: list[Director] = []
    # 演员阵容
    casts: list[Cast] | None = None
    # 类型
    genres: list[str] | None = None
    rating: Rating | None = None


class MovieSearch(BaseModel):
    count: int
    start: int
    total: int
    title: str
    subjects: list[Subject]


class MovieSubjectGet(Subject):
    subtype: str
    comments_count: int
    ratings_count: int
    collect_count: int
    aka: list[str] | None = None
    countries: list[str] | None = None
    summary: str | None = None
