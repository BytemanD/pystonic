from urllib import parse

import click
from loguru import logger
from pydantic import BaseModel

from pystonic.pretty import output
from pystonic.utils.system import execute


class PipRepo(BaseModel):
    name: str
    url: str


PIP_REPOS = [
    PipRepo(name="官方", url="https://pypi.org/simple"),
    PipRepo(name="清华大学", url="https://pypi.tuna.tsinghua.edu.cn/simple"),
    PipRepo(name="中国科技大学", url="https://pypi.mirrors.ustc.edu.cn/simple"),
    PipRepo(name="阿里云", url="https://mirrors.aliyun.com/pypi/simple"),
    PipRepo(name="腾讯", url="http://mirrors.cloud.tencent.com/pypi/simple"),
]


@click.group("pip")
def root():
    pass


@root.command()
def list_repo():
    output.print_models(PIP_REPOS)


@root.command
@click.argument("repo")
def set_repo(repo: str):
    repo_map = {x.name: x.url for x in PIP_REPOS}
    if repo.startswith(("http://", "https://")):
        index_url = repo
    else:
        index_url = repo_map.get(repo)
    if not index_url:
        raise click.ClickException(f"invalid repo: {repo}")

    result = parse.urlparse(repo_map[repo])
    logger.success("set pip repo ({}) success", index_url)
    cmd_prefix = ["python", "-m", "pip", "config", "set"]
    execute(*cmd_prefix, "global.index-url", index_url, check=True)
    execute(*cmd_prefix, "global.trusted-host", result.hostname, check=True)
