import abc
import os
import platform
import subprocess  # nosec B404 - 本模块核心即 shell 执行驱动
import tempfile
from enum import Enum

from loguru import logger


class Cmd(str, Enum):
    POWERSHELL = "powershell"
    CALL = "call"
    BASH = "bash"


class ExecuteDriver(abc.ABC):
    SCRIPT_SUFFIX = ""

    # 子进程默认超时(秒)，防止脚本挂死占满调用线程
    DEFAULT_TIMEOUT = 300

    def __init__(self) -> None:
        self.platform = platform.system()
        self.version = platform.version()
        self.architecture = platform.architecture()

    def execute(self, code_block: str, timeout: float | None = None):
        logger.debug("code block: {}", code_block)
        output = ""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=self.SCRIPT_SUFFIX, encoding="utf-8"
        ) as file:
            file.write(code_block)
            file.flush()
            file.close()
            logger.debug("Run file: {}", file.name)
            try:
                result = subprocess.run(
                    self.file_command(file.name),  # nosec B603 - 本驱动的职责即执行框架写入的脚本文件，非外部输入
                    check=False,  # 非零退出码由下方读取 returncode 处理，不抛异常
                    capture_output=True,
                    text=True,
                    timeout=timeout if timeout is not None else self.DEFAULT_TIMEOUT,
                )
                output = result.stdout or ""
                if result.returncode != 0:
                    logger.warning(
                        "exit {}: {}", result.returncode, (result.stderr or "").strip()
                    )
                    output += result.stderr or ""
            except subprocess.TimeoutExpired as e:
                logger.error("execute timeout: {}", e)
                stdout = e.stdout or ""
                if isinstance(stdout, bytes):
                    stdout = stdout.decode(errors="replace")
                output = f"{stdout}\n(timeout after {e.timeout}s)"
            finally:
                logger.debug("Remove file: {}", file.name)
                os.remove(file.name)
        return output

    @abc.abstractmethod
    def oneline_command(self, code: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def file_command(self, file: str) -> list[str]:
        """返回执行脚本文件的参数列表（shell=False 方式执行，避免命令注入）"""
        raise NotImplementedError()


class PowershellDriver(ExecuteDriver):
    SCRIPT_SUFFIX = ".ps1"

    def oneline_command(self, code: str):
        return f'{Cmd.POWERSHELL.value} -Command "{code}"'

    def file_command(self, file: str) -> list[str]:
        return [Cmd.POWERSHELL.value, "-File", file]


class CmdDriver(ExecuteDriver):
    SCRIPT_SUFFIX = ".bat"

    def oneline_command(self, code: str):
        return f'{Cmd.CALL.value} "{code}"'

    def file_command(self, file: str) -> list[str]:
        return ["cmd", "/C", "call", file]


class BashDriver(ExecuteDriver):
    SCRIPT_SUFFIX = ""

    def __init__(self) -> None:
        super().__init__()
        self.cmd = Cmd.BASH.value

    def oneline_command(self, code: str):
        return f'{Cmd.BASH.value} -c "{code}"'

    def file_command(self, file: str) -> list[str]:
        return [self.cmd, file]
