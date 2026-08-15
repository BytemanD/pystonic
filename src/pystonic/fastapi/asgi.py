import fastapi


def create_app(
    debug: bool = False,
    docs_url: str | None = "/docs",
    redoc_url: str | None = "/redoc",
):
    app = fastapi.FastAPI(debug=debug, docs_url=docs_url, redoc_url=redoc_url)
    return app
