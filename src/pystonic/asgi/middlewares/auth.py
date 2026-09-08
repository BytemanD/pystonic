from fastapi import HTTPException
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from pystonic.auth.jwt import JWT
from pystonic.common import context


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        authorizen = request.headers.get("Authorizen")
        if not authorizen:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized"
            )

        try:
            auth_type, token = authorizen.split()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid Authorizen"
            )

        if auth_type == "Bearer":
            payload = JWT.decode(token)
            context.set_account(payload.account)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="unsupported auth type: {auth_type}",
            )
        return await call_next(request)
