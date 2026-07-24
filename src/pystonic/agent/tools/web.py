from typing import Optional, Sequence, Tuple
from urllib.parse import parse_qs

from agents import function_tool

from pystonic.conf import CONF
from pystonic.core import httpclient

WEB_SEARCH = httpclient.default_client(
    raise_for_status=True,
    timeout=CONF.http_client.timeout,
)


@function_tool
def web_get(
    url: str,
    params: Optional[str] = None,
    headers: Optional[Sequence[Tuple[str, str]]] = None,
) -> str:
    """HTTP GET请求

    Args:
        url: 网页地址
        params: 请求参数(例如： name='张三'&age=18)
        headers: 请求头, JSON格式(例如： {"Authorization": "Bearer xxxxxxx})

    Returns:
        网页内容
    """
    resp = WEB_SEARCH.get(
        url, params=parse_qs(params) if params else None, headers=headers
    )
    return resp.text
