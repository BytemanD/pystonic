from datetime import datetime
import os
from pathlib import Path
import subprocess
import tempfile

import httpx
from langchain.tools import ToolRuntime
from langchain_core.tools import BaseToolkit, tool
from loguru import logger

from pystonic.agents.langchain_agent.exceptions import PermissionDeny
from pystonic.agents.langchain_agent.objects import RuntimeContext
from pystonic.shell import Shell
from pystonic.utils.system import platform_info


@tool
def get_iso_datetime():
    """获取当前日期和时间

    当需要获取当前日期和时间时使用。

    Returns:
        ISO格式日期和时间
    """
    return datetime.now().isoformat()


@tool
def get_platform_info():
    """获取当前操作系统信息

    当需要获取当前操作系统信息时使用。

    Returns:
        系统信息(JSON 格式)
    """
    return platform_info().model_dump_json()


@tool
def list_dir(
    path: str | None = None,
    name: str | None = None,
    include_hidden: bool = False,
) -> list[str]:
    """列出目录下的子目录和文件

    Args:
        path: 路径，如何不指定，则使用当前目录
        name: 模糊匹配文件/目录名
        include_hidden: 是否包含 隐藏文件/目录
    Returns:
        文件/目录列表
    """
    find_path = Path(path) if path else Path.cwd()

    def _filter(x: Path):
        if name and name not in x.name:
            return False

        return not (not include_hidden and x.name.startswith("."))

    children = [x for x in find_path.iterdir()]
    return [str(x.relative_to(find_path)) for x in filter(_filter, children)]


@tool
def read_file(
    runtime: ToolRuntime[RuntimeContext], file_path: str, encoding: str = "utf-8"
) -> str:
    """读取文本文件内容

    Args:
        file_path: 文件路径
        encoding: 文件编码，默认 utf-8

    Returns:
        文件内容
    """
    path = runtime.context.workspace.joinpath(file_path)
    if not runtime.context.allow_outside_workspace and not path.relative_to(
        runtime.context.workspace
    ):
        raise PermissionDeny("No permission to access file: {file_path}")
    if not path.exists():
        raise FileNotFoundError(f"path {path} not exists")
    if not path.is_file():
        raise ValueError(f"path {path} is not a file")
    return path.read_text(encoding=encoding)


@tool
def write_file(
    runtime: ToolRuntime[RuntimeContext],
    file_path: str,
    content: str,
    encoding="utf-8",
    overwrite=False,
) -> Path:
    """创建文本文件, 并写入数据
    Args:
        path: 文件路径
        content: 文件内容
        encoding: 文件编码，默认 utf-8
    Returns:
        文件路径
    """
    path = runtime.context.workspace.joinpath(file_path)
    if not runtime.context.allow_outside_workspace and not path.relative_to(
        runtime.context.workspace
    ):
        raise PermissionDeny("No permission to access file: {file_path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if overwrite and path.exists():
        raise FileExistsError("file {} already exists", file_path)
    path.write_text(content, encoding=encoding)


class ShellWrapper(Shell):
    def execute(self, code: str):
        logger.debug("code block: {}", code)
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=self.driver.SCRIPT_SUFFIX
        ) as file:
            file.write(code)
            file.flush()
            file.close()
            logger.debug("Run file: {}", file.name)
            try:
                _, output = subprocess.getstatusoutput(
                    self.driver.file_command(file.name)
                )
            except subprocess.CalledProcessError as e:
                logger.exception("Failed to run code block")
                output = str(e)
            finally:
                logger.debug("Remove file: {}", file.name)
                os.remove(file.name)
        return output


executor = ShellWrapper()


@tool
def execute_command(command: str) -> str:
    """执行 Shell/Bash/Cmd/Powershell 命令"""
    return executor.execute(command)


@tool
def web_get(
    url: str, params: dict | None = None, headers: dict | None = None, timeout=60
) -> str:
    """HTTP GET请求

    当需要获取网页内容是使用。

    Args:
        url: 网页地址
        params: 请求参数(例如： {"name": "foo"})
        headers: 请求头, JSON格式(例如： {"Authorization": "Bearer xxxxxxx})
        timeout: 超时时间

    Returns:
        网页内容
    """
    resp = httpx.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.text


class WorkToolkit(BaseToolkit):
    enable_read: bool = True
    enable_write: bool = True
    enable_execute_shell: bool = True
    enable_web_get: bool = True
    enable_get_platform_info: bool = True

    def get_tools(self) -> list:
        tools = [
            get_iso_datetime,
            read_file,
            write_file,
        ]
        if self.enable_read:
            tools.append(read_file)
        if self.enable_write:
            tools.append(write_file)
        if self.enable_execute_shell:
            tools.append(execute_command)
        if self.enable_web_get:
            tools.append(web_get)
        if self.enable_get_platform_info:
            tools.append(get_platform_info)
        return tools
