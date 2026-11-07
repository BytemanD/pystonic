from pystonic.common.conf import CONF
from pystonic.integrations.omdb.objects import MovieSearch
from pystonic.utils.httpclient import default_client


class OMDBClient:
    def __init__(self) -> None:
        self.api_key = CONF.omdb.api_key
        self._client = default_client(CONF.omdb.base_url, raise_for_status=True)

    def search(self, keyword: str, strict: bool = True):
        """搜索电影信息"""
        params = {
            "apikey": self.api_key,
            "t" if strict else "s": keyword,
        }
        response = self._client.get("/", params=params)
        data = response.json()
        if data.get("Response") == "False":
            raise RuntimeError(f"OMDB API Error: {data.get('Error')}")
        return MovieSearch.model_validate(data)
