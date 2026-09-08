from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from pystonic.common import context


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        context.set_trace()
        return await call_next(request)
