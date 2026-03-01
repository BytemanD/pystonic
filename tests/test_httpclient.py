import httpx
import pytest

from pystonic.utils import httpclient


def test_httpclient():
    client = httpclient.default_client(base_url="https://www.baidu.com/")
    resp = client.get("https://www.baidu.com/")
    assert not resp.is_error


def test_httpclient_with_check_status():
    client = httpclient.default_client(timeout=10, raise_for_status=True)
    with pytest.raises(httpx.HTTPStatusError):
        client.post("https://www.baidu.com/")
