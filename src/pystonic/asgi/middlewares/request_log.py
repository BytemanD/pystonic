import time
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
    if (
        resp.body
        and isinstance(resp.body, bytes)
        and "application/json" in content_type
    ):
        return text_shorten(resp.body.decode())

    return f"<omit {content_type}>"


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
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", f"{int(start_time * 1000)}")

        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url = str(request.url)
        headers = dict(request.headers)

        request_body = None
        if self.log_request_body and method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # 限制记录长度
                    body_str = body.decode("utf-8")
                    if len(body_str) > self.max_body_length:
                        body_str = body_str[: self.max_body_length] + "... (truncated)"
                    request_body = body_str

                    # 重新设置请求体，以便后续处理
                    async def receive():
                        return {"type": "http.request", "body": body}

                    request._receive = receive
            except Exception as e:
                logger.warning(f"无法读取请求体: {e}")
                request_body = "<无法读取>"

        # 记录请求日志
        log_data = {
            "request_id": request_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "client_ip": client_ip,
            "method": method,
            "url": url,
            "user_agent": headers.get("user-agent", ""),
            "referer": headers.get("referer", ""),
            "headers": {
                k: v
                for k, v in headers.items()
                if k.lower() not in ["authorization", "cookie"]
            },
        }

        if request_body:
            log_data["request_body"] = request_body

        response = await call_next(request)
        detail = """
        {req_headers}

        {req_body}
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        {resp_headers}

        {resp_body}
        """

        logger.log(
            "INFO"
            if response.status_code <= 400
            else "ERRORASGI Request: {} {} -> {}\n{}",
            request.method,
            request.url,
            response.status_code,
            detail.format(
                req_headers="\n".join(
                    [f"{k.title()}: {v}" for k, v in request.headers.items()]
                ),
                req_body=await _get_request_body(request),
                resp_headers="\n".join(
                    [f"{k.title()}: {v}" for k, v in response.headers.items()]
                ),
                resp_body=_get_response_body(response),
            ),
        )
