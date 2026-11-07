import pytest

from pystonic.common.conf import CONF
from pystonic.integrations.omdb.client import OMDBClient

pytestmark = pytest.mark.skipif(
    not CONF.omdb.api_key, reason="OMDB api_key is empty, skip"
)


@pytest.fixture(scope="module", autouse=True)
def client():
    yield OMDBClient()


def test_search(client: OMDBClient):
    result = client.search("Inception", strict=True)
    assert result.title == "Inception"
    assert result.year == "2010"
    assert result.imdb_id
    assert result.plot
