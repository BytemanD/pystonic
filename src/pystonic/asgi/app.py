from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from pystonic.conf import CONF


def create_app(
    lifespan: Callable | None = None,
):
    app = FastAPI(
        title=CONF.asgi.name,
        summary=CONF.asgi.summary,
        description=CONF.asgi.description,
        docs_url=CONF.asgi.docs_url,
        redoc_url=CONF.asgi.redoc_url,
        openapi_prefix=CONF.asgi.openapi_prefix,
        openapi_url=CONF.asgi.openapi_url,
        lifespan=lifespan,
    )

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception):
        logger.exception("unexcept exception")
        return JSONResponse(status_code=500, content={"error": str(exc)})

    return app
