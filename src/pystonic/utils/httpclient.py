import re
from typing import Dict, List, Optional

import httpx
from loguru import logger
from pydantic import BaseModel


TYPE_WWW_FORM = "application/x-www-form-urlencoded"
TYPE_JSON = "application/json"
TYPE_TEXT_HTML = "text/html"


_text_regex = re.compile(r".*(application/json|text/html).*")
_resp_detail = """
{method} {url} {status_code}
{headers}

-.-.-.- response (elapsed: {elapsed}) -.-.-.-
{status_code} {reason_phrase}
{resp_headers}

{content}
"""


class HTTPClientConfig(BaseModel):
    log_response_detail: bool = True
    timeout: int = 60
    retries: int = 0


_DEFAULT_CONF: HTTPClientConfig = HTTPClientConfig()


def format_headers(headers: httpx.Headers):
    return "\n".join(f"{k}: {v}" for k, v in headers.items())


def _log_request(request: httpx.Request) -> None:
    """Log request details."""
    logger.debug("Req: {} {}", request.method, request.url)


def _log_response(resp: httpx.Response) -> None:
    """Log request details."""
    if resp.status_code < 400:
        log_func = logger.debug
    else:
        log_func = logger.warning
    log_func(
        "Resp: {} {} -> [{} {}], <{} {}>",
        resp.request.method,
        resp.request.url,
        resp.status_code,
        resp.reason_phrase,
        resp.headers.get("Content-Type") or "*",
        resp.headers.get("Content-Length") or "*",
    )


def _log_response_detail(resp: httpx.Response):
    if _text_regex.match(resp.headers.get("Content-Type", "")):
        resp.read()
        content = resp.text
        elapsed = resp.elapsed.total_seconds()
    else:
        content = "<omitted>"
        elapsed = ""
    logger.trace(
        _resp_detail,
        method=resp.request.method,
        url=resp.request.url,
        headers=format_headers(resp.request.headers),
        status_code=resp.status_code,
        reason_phrase=resp.reason_phrase,
        resp_headers=format_headers(resp.headers),
        elapsed=elapsed,
        content=content,
    )


def _raise_for_status(resp: httpx.Response):
    """Log request details."""
    resp.raise_for_status()


def default_client(
    base_url: str = "",
    auth=None,
    raise_for_status=False,
    headers: Optional[Dict] = None,
    retries: Optional[int] = None,
    timeout: Optional[int] = None,
) -> httpx.Client:
    event_hooks: Dict[str, List] = {
        "request": [_log_request],
        "response": [_log_response],
    }
    if _DEFAULT_CONF.log_response_detail:
        event_hooks["response"].append(_log_response_detail)
    if raise_for_status:
        event_hooks["response"].append(_raise_for_status)
    timeout = timeout or _DEFAULT_CONF.timeout
    retries = retries or _DEFAULT_CONF.retries
    kwargs = {}
    if timeout:
        kwargs["timeout"] = timeout
    return httpx.Client(
        base_url=base_url,
        auth=auth,
        headers=headers,
        event_hooks=event_hooks,
        transport=httpx.HTTPTransport(retries=retries),
        **kwargs,
    )
