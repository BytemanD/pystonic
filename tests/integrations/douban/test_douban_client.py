import pytest

from pystonic.common.conf import CONF
from pystonic.integrations.douban.client import DoubanClient

pytestmark = pytest.mark.skipif(
    not CONF.douban.api_key, reason="douban api_key is empty, skip"
)


@pytest.fixture(scope="module", autouse=True)
def client():
    yield DoubanClient()


def test_movie_search(client: DoubanClient):
    result = client.movie_search("聪明镇")
    assert result.total > 0
    assert "聪明镇" in [movie.title for movie in result.subjects]


def test_movie_get(client: DoubanClient):
    result = client.movie_search("聪明镇")
    assert result.subjects
    sub = client.movie_get(result.subjects[0].id)
    assert "聪明镇" == sub.title
    assert sub.summary
