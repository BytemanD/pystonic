from typing import Literal

from pystonic.common.conf import CONF
from pystonic.integrations.douban.objects import (
    FrodoSearchResult,
    FrodoSubject,
    MovieSearch,
    MovieSubjectGet,
    Subject,
)
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


class FrodoDoubanClient:
    def __init__(self) -> None:
        self._client = default_client(
            CONF.douban.frodo_base_url,
            timeout=CONF.douban.timeout,
            raise_for_status=True,
            headers={
                "referer": "https://servicewechat.com/wx2f9b06c1de1ccfca/91/page-frame.html",
                "User-Agent": "MicroMessenger/",
            },
        )
        self._api_key = CONF.douban.frodo_api_key

    def search_subjects(
        self, keyword: str, target_types: list[Literal["movie", "tv"]] | None = None
    ) -> list[FrodoSubject]:
        subjects = []
        params = {"q": keyword, "apikey": self._api_key, "start": 0, "count": 20}
        while True:
            resp = self._client.post(
                "/api/v2/search/subjects",
                params=params,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            result = FrodoSearchResult.model_validate(resp.json())
            if not result.subjects.items:
                print(result)
                break
            print(len(result.subjects.items))
            subjects.extend(
                x.target
                for x in result.subjects.items
                if x.target and (not target_types or x.target_type in target_types)
            )
            params["start"] += 20

        return subjects

    def get_tv_photos(self):
        # https://frodo.douban.com/api/v2/tv/35896166/photos?apikey=0ac44ae016490db2204ce0a042db2916&subtype=o&start=0&type=R
        pass
