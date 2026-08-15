import html
import html.parser
import re
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import httpx
from loguru import logger


class HtmlLinkParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr in attrs:
                if attr[0] == "href" and attr[1]:
                    self.links.append(attr[1])


def get_links(url: str):
    resp = httpx.get(url)
    resp.raise_for_status()
    parser = HtmlLinkParser()
    parser.feed(resp.text)
    return parser.links


def rglob(url: str, parttern: Optional[re.Pattern] = None):
    """Recursive glob from url"""

    files: List[str] = []
    dirs = [url + "/"]
    while dirs:
        base_url = dirs.pop()
        logger.debug("get links of {}", base_url)
        try:
            links = get_links(base_url)
        except httpx.HTTPError as e:
            logger.warning("get links error: {}", e)
            continue

        for link in links:
            if link.endswith("/"):
                dirs.append(base_url + link)
                continue
            if parttern and not parttern.match(link):
                continue
            files.append(base_url + link)
        logger.debug("found {} files total", len(links))
    return files


def sync_files_from_http_server(
    url: str, output: str, parttern: Optional[re.Pattern] = None
):
    """sync files from http server

    >>> sync_files_from_http_server("http://127.0.0.1:8000", output="data")
    """

    files = rglob(url, parttern=parttern)
    if not files:
        logger.error("no files found")
        return
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("download {} files...", len(files))
    for link in files:
        resp = httpx.get(link)
        resp.raise_for_status()
        file_path = output_dir.joinpath(urlparse(link).path.lstrip("/"))
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(resp.content)
    logger.success("download done.")
