import abc
import os
import platform
import subprocess  # nosec B404 - 本模块核心即 shell 执行驱动
import tempfile

from loguru import logger


class ExecuteDriver(abc.ABC):
    SCRIPT_SUFFIX = ""

    def __init__(self) -> None:
        self.platform = platform.system()
        self.version = platform.version()
        self.architecture = platform.architecture()

    def execute(self, *args: str, check=True, timeout: float | None = 300):
        p = subprocess.run(
            self.get_run_command(*args),
            check=check,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if p.returncode != 0:
            logger.warning("exit {}: {}", p.returncode, (p.stderr or "").strip())

        output = p.stdout
        if p.stderr:
            output += ("\n" if output else "") + p.stderr
        return output

    def execute_file(self, code_block: str, check=True, timeout: float | None = 600):
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
                output = self.execute(
                    *self.get_file_command(file.name), check=check, timeout=timeout
                )
            except subprocess.TimeoutExpired as e:
                logger.error("execute timeout: {}", e)
                raise
            finally:
                logger.debug("Remove file: {}", file.name)
                os.remove(file.name)
        return output

    @abc.abstractmethod
    def get_run_command(self, *args: str) -> list[str]:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_file_command(self, file: str) -> list[str]:
        """返回执行脚本文件的参数列表（shell=False 方式执行，避免命令注入）"""
        raise NotImplementedError()


class BashDriver(ExecuteDriver):
    CMD = "bash"
    SCRIPT_SUFFIX = ""

    def get_run_command(self, *args: str) -> list[str]:
        return [self.CMD, "-c", *args]

    def get_file_command(self, file: str) -> list[str]:
        return [self.CMD, file]


class PowershellDriver(ExecuteDriver):
    CMD = "powershell"
    SCRIPT_SUFFIX = ".ps1"

    def get_run_command(self, *args: str) -> list[str]:
        return [self.CMD, "-Command", *args]

    def get_file_command(self, file: str) -> list[str]:
        return [self.CMD, "-File", file]


class CmdDriver(ExecuteDriver):
    CMD = "cmd.exe"
    SCRIPT_SUFFIX = ".bat"

    def get_run_command(self, *args: str) -> list[str]:
        return [self.CMD, "/c", *args]

    def get_file_command(self, file: str) -> list[str]:
        return [self.CMD, "/c", file]
