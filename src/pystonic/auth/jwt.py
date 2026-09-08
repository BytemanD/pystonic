from datetime import UTC, datetime, timedelta

import jwt
from loguru import logger
from pydantic import BaseModel

from pystonic.common import exceptions
from pystonic.common.conf import CONF


class Payload(BaseModel):
    account: str
    exp: str


class JWTService:
    def __init__(self):
        pass

    def encode(
        self,
        account: str,
    ):
        token = jwt.encode(
            {
                "account": account,
                "exp": datetime.now(UTC) + timedelta(seconds=CONF.jwt.expired),
            },
            key=CONF.jwt.key,
            algorithm=CONF.jwt.algorithms,
        )
        return token

    def decode(self, token: str):
        try:
            payload = jwt.decode(token, key=CONF.jwt.key, algorithm=CONF.jwt.algorithms)
        except jwt.InvalidTokenError as e:
            logger.error("token decode failed: {}", e)
            raise exceptions.AuthFailed("invalid token")

        return Payload.model_validate(payload)


JWT = JWTService()
