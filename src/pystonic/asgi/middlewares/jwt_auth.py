from datetime import datetime, timedelta

import jwt
from loguru import logger
from pydantic import BaseModel
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
    BaseUser,
    SimpleUser,
    UnauthenticatedUser,
)
from starlette.requests import HTTPConnection

from pystonic.common import context
from pystonic.common.conf import CONF
from pystonic.utils.dateutil import utcnow


class JWTToken(BaseModel):
    sub: str
    exp: datetime


class JWTService:
    def encode(self, user: str):
        payload = {"sub": user, "exp": utcnow() + timedelta(hours=1)}
        return jwt.encode(payload, key=CONF.jwt.key, algorithm=CONF.jwt.algorithms[0])

    def decode(self, token: str, verify: bool = False):
        return jwt.decode(
            token, key=CONF.jwt.key, algorithms=CONF.jwt.algorithms, verify=verify
        )

    def verify(self, token: str):
        return JWTToken.model_validate(self.decode(token, verify=True))


JWT_SERVICE = JWTService()


class JWTBackend(AuthenticationBackend):
    def __init__(self, exclude_routes: set[tuple[str, str]] = set()) -> None:
        super().__init__()
        self.exclude_routes = exclude_routes

    async def authenticate(
        self, conn: HTTPConnection
    ) -> tuple[AuthCredentials, BaseUser] | None:
        if (conn.scope["method"], conn.url.path) in self.exclude_routes:
            return AuthCredentials(["authenticated"]), UnauthenticatedUser()

        auth_header = conn.headers.get("Authorization")
        if not auth_header:
            raise AuthenticationError("Missing Authorization header")
        if auth_header.startswith(("Bearer ", "bearer ")):
            try:
                token = JWT_SERVICE.verify(token=auth_header.split(maxsplit=1)[1])
                context.set_account(token.sub)
                return AuthCredentials(["authenticated"]), SimpleUser(token.sub)
            except jwt.exceptions.PyJWTError as e:
                logger.error("auth faield: {}", e)
                raise AuthenticationError("Invalid token")
        raise AuthenticationError("Invalid token")
