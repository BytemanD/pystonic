import threading

import httpx
import pytest

from pystonic.core import httpclient


def start_http_server():
    import os

    os.system("python -m http.server 80")


thread = threading.Thread(target=start_http_server)
thread.daemon = True
thread.start()


def test_httpclient():
    client = httpclient.default_client(base_url="http://127.0.0.1")
    resp = client.get("/")
    assert not resp.is_error


def test_httpclient_with_check_status():
    client = httpclient.default_client(
        base_url="http://127.0.0.1", timeout=10, raise_for_status=True
    )
    with pytest.raises(httpx.HTTPStatusError):
        client.post("/")
