import pytest

from pystonic.common.conf import CONF
from pystonic.integrations.douban.client import FrodoDoubanClient

pytestmark = pytest.mark.skipif(
    not CONF.douban.api_key, reason="douban api_key is empty, skip"
)


@pytest.fixture(scope="module", autouse=True)
def client():
    yield FrodoDoubanClient()


def test_movie_search(client: FrodoDoubanClient):
    subjects = client.search_subjects("聪明镇", target_types=["movie"])
    # breakpoint()
    for x in subjects:
        print(x)
    assert len(subjects) > 0
    assert "聪明镇" in [movie.title for movie in subjects]
