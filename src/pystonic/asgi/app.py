from collections.abc import Callable, Sequence

from fastapi import FastAPI, Request
from fastapi.middleware import Middleware
from fastapi.responses import JSONResponse
from loguru import logger


async def default_livez_handler():
    return {}


def create_app(
    lifespan: Callable | None = None,
    livez_handler: Callable | None = None,
    livez_router: str = "/livez",
    title: str = "FastAPI",
    summary: str = "",
    description: str = "",
    version: str = "0.1.0",
    docs_url: str = "/docs",
    redoc_url: str = "/redoc",
    openapi_url: str = "/openapi.json",
    openapi_prefix: str = "",
    middlewares: Sequence[Middleware] | None = None,
    root_path: str = "",
):
    app = FastAPI(
        title=title,
        summary=summary,
        description=description,
        version=version,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_prefix=openapi_prefix,
        openapi_url=openapi_url,
        lifespan=lifespan,
        middleware=middlewares,
        root_path=root_path,
    )

    app.get(livez_router)(livez_handler or default_livez_handler)

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception):
        logger.exception("unexcept exception")
        return JSONResponse(status_code=500, content={"error": str(exc)})

    return app
