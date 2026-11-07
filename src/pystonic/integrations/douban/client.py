from pystonic.common.conf import CONF
from pystonic.integrations.douban.objects import MovieSearch, MovieSubjectGet
from pystonic.utils.httpclient import default_client


class DoubanClient:
    def __init__(self) -> None:
        self._client = default_client(
            CONF.douban.base_url, timeout=CONF.douban.timeout, raise_for_status=True
        )

    def movie_search(self, keyword: str):
        """搜索电影信息"""
        params = {"q": keyword, "apikey": CONF.douban.api_key}
        resp = self._client.post(
            "/v2/movie/search",
            params=params,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return MovieSearch.model_validate(resp.json())

    def movie_get(self, subject_id: str):
        params = {"apikey": CONF.douban.api_key}
        resp = self._client.post(
            f"/v2/movie/subject/{subject_id}",
            params=params,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return MovieSubjectGet.model_validate(resp.json())
