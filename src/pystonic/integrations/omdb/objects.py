from pydantic import BaseModel, Field


class MovieSearch(BaseModel):
    title: str | None = Field(alias="Title")
    year: str | None = Field(alias="Year")
    released: str | None = Field(alias="Released")
    director: str | None = Field(alias="Director")
    runtime: str | None = Field(alias="Runtime")
    imdb_id: str | None = Field(alias="imdbID")
    type: str | None = Field(alias="Type")
    poster: str | None = Field(alias="Poster")
    actors: str | None = Field(alias="Actors")
    language: str | None = Field(alias="Language")
    country: str | None = Field(alias="Country")
    ratings: list[dict] | None = Field(alias="Ratings")
    plot: str | None = Field(alias="Plot")
    imdb_votes: str | None = Field(alias="imdbVotes")
    box_office: str | None = Field(alias="BoxOffice")
