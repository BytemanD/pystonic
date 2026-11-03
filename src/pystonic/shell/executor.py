import os
import platform
import subprocess
import tempfile
from enum import StrEnum

from loguru import logger

from pystonic.shell.backends import Bash, Cmd, Powershell
from pystonic.utils.system import is_darwin, is_linux, is_windows


class Terminal(StrEnum):
    POWERSHELL = "powershell"
    CMD = "cmd"
    BASH = "bash"


def get_terminal() -> Terminal:
    if is_windows():
        return Terminal.POWERSHELL if "PSModulePath" in os.environ else Terminal.CMD
    elif is_linux() or is_darwin():
        return Terminal.BASH

    raise RuntimeError(f"Unsupported OS: {platform.system()}")


class ShellExecutor:
    def __init__(self) -> None:
        self.terminal = get_terminal()
        if self.terminal == Terminal.CMD:
            self.backend = Cmd()
        if self.terminal == Terminal.POWERSHELL:
            self.backend = Powershell()
        else:
            self.backend = Bash()

    def _execute(self, *args: str, check=True, timeout: float | None = 300):
        logger.debug("Run: {}", " ".join(args))
        p = subprocess.run(
            args,
            check=check,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if p.returncode != 0:
            logger.warning("exit {}: {}", p.returncode, (p.stderr or "").strip())

        output = p.stdout.rstrip("\n")
        if p.stderr:
            output += ("\n" if output else "") + p.stderr.rstrip("\n")
        return output

    def execute(self, *args: str, check=True, timeout: float | None = None):
        return self._execute(*args, check=check, timeout=timeout or 300)

    def execute_code(self, code_block: str, check=True, timeout: float | None = None):
        logger.trace("code block: {}", code_block)
        output = ""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=self.backend.SCRIPT_SUFFIX, encoding="utf-8"
        ) as file:
            file.write(code_block)
            file.flush()
            file.close()
            logger.debug("Run file: {}", file.name)
            try:
                output = self._execute(
                    *self.backend.get_file_command(file.name),
                    check=check,
                    timeout=timeout or 600,
                )
            finally:
                logger.debug("Remove file: {}", file.name)
                os.remove(file.name)
        return output


def execute(*args: str, check=True, timeout: float | None = None):
    return ShellExecutor().execute(*args, check=check, timeout=timeout)


def execute_code(code: str, check=True, timeout: float | None = None):
    return ShellExecutor().execute_code(code, check=check, timeout=timeout)
