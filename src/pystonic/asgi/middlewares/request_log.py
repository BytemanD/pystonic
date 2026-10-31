from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from pystonic.utils.strutil import text_shorten


async def _get_request_body(req: Request):
    content_type = req.headers.get("content-type") or ""
    if "application/json" in content_type:
        return text_shorten((await req.body()).decode())

    return f"<omit {content_type}>"


def _get_response_body(resp: Response):
    content_type = resp.headers.get("content-type") or ""
    if "event-stream" in content_type:
        # 流式响应不读 body，避免破坏流
        return f"<stream {content_type}>"
    body = getattr(resp, "body", None)
    if body and isinstance(body, bytes) and "application/json" in content_type:
        return text_shorten(body.decode())

    return f"<omit {content_type}>"


def _redact(headers: dict) -> str:
    sensitive = {"authorization", "cookie", "set-cookie"}
    return "\n".join(
        f"{k.title()}: {v}" for k, v in headers.items() if k.lower() not in sensitive
    )


class DetailedRequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        log_request_body: bool = True,
        log_response_body: bool = True,
        max_body_length: int = 1024,
    ):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_length = max_body_length

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):  # type: ignore
        request_body = "<omit>"
        try:
            # 必须在 call_next 之前读取请求体，否则会触发 "Stream consumed"
            if self.log_request_body:
                request_body = await _get_request_body(request)
                body = await request.body()
                if body:
                    # 重新设置请求体，以便后续处理
                    async def receive():
                        return {
                            "type": "http.request",
                            "body": body,
                            "more_body": False,
                        }

                    request._receive = receive
        except Exception as e:  # noqa: BLE001
            logger.warning(f"无法读取请求体: {e}")
            request_body = "<无法读取>"
        # 记录请求日志
        response = await call_next(request)

        resp_body = f"<omit {response.headers.get('content-type') or ''}>"
        if self.log_response_body:
            content_type = response.headers.get("content-type") or ""
            try:
                if (
                    "application/json" in content_type
                    and "event-stream" not in content_type
                ):
                    # 捕获后原样重放，不破坏响应流
                    raw = b""
                    async for chunk in response.body_iterator:
                        raw += chunk

                    async def replay():
                        yield raw

                    response.body_iterator = replay()
                    resp_body = text_shorten(raw.decode("utf-8", errors="replace"))
            except Exception as e:  # noqa: BLE001
                logger.warning(f"无法读取响应体: {e}")
                resp_body = "<无法读取>"

        detail = """
        {req_headers}

        {req_body}
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        {resp_headers}

        {resp_body}
        """

        logger.log(
            "INFO"
            if response.status_code < 400
            else "WARNING"
            if response.status_code < 500
            else "ERROR",
            "ASGI Request: {} {} -> {}\n{}",
            request.method,
            request.url,
            response.status_code,
            detail.format(
                req_headers=_redact(dict(request.headers)),
                req_body=request_body,
                resp_headers=_redact(dict(response.headers)),
                resp_body=resp_body,
            ),
        )
        return response
