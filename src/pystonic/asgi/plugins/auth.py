from typing import Callable

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, SecretStr
from starlette import status
from starlette.authentication import AuthenticationError
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import HTTPConnection

from pystonic.asgi.middlewares.jwt_auth import JWT_SERVICE, JWTBackend


class LoginRequest(BaseModel):
    username: str
    password: SecretStr


class LoginResponse(BaseModel):
    token: str


def unauthorized_error(conn: HTTPConnection, exc: Exception) -> Response:
    return JSONResponse({"error": str(exc)}, status_code=status.HTTP_401_UNAUTHORIZED)


def setup(
    app: FastAPI,
    on_login: Callable[[str, str], None],
    login_url: str | None = "/api/v1/auth/login",
    exclude_routes: set[tuple[str, str]] | None = None,
):
    """安装 JWT 认证插件

    - 添加登录接口
    - 添加认证中间件

    Args:
        app: FastAPI app
        on_login: 用户名+密码登录的方法, 如果认证失败，抛出 AuthenticationError 异常
        login_url: 用户名+密码登录接口路由
        exclude_routes: 需要排除认证的路由
    """

    exclude_routes = exclude_routes or set([])
    if login_url:
        exclude_routes.update({("POST", login_url)})

        @app.post(login_url)
        def _login(req: Request, body: LoginRequest):
            try:
                on_login(body.username, body.password.get_secret_value())
            except AuthenticationError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
                )
            token = JWT_SERVICE.encode(body.username)
            logger.success("login success")
            return LoginResponse(token=token)

    app.add_middleware(
        AuthenticationMiddleware,
        backend=JWTBackend(exclude_routes=exclude_routes),
        on_error=unauthorized_error,
    )
