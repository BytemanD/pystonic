from typing import Callable, Sequence

from fastapi import FastAPI, Request
from fastapi.middleware import Middleware
from fastapi.responses import JSONResponse
from loguru import logger

from pystonic.common.conf import CONF


async def default_livez_handler():
    return {}


def create_app(
    lifespan: Callable | None = None,
    livez_handler: Callable | None = None,
    livez_router: str = "/livez",
    docs_url: str | None = None,
    redoc_url: str | None = None,
    openapi_prefix: str | None = None,
    openapi_url: str | None = None,
    middlewares: Sequence[Middleware] | None = None,
):
    app = FastAPI(
        title=CONF.asgi.name,
        summary=CONF.asgi.summary,
        description=CONF.asgi.description,
        docs_url=docs_url or CONF.asgi.docs_url,
        redoc_url=redoc_url or CONF.asgi.redoc_url,
        openapi_prefix=openapi_prefix or CONF.asgi.openapi_prefix,
        openapi_url=openapi_url or CONF.asgi.openapi_url,
        lifespan=lifespan,
        middleware=middlewares,
    )

    app.get(livez_router)(livez_handler or default_livez_handler)

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception):
        logger.exception("unexcept exception")
        return JSONResponse(status_code=500, content={"error": str(exc)})

    return app
