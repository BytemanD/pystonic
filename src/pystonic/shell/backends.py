import abc
import shlex


class ShellBackend:
    @abc.abstractmethod
    def get_run_command(self, *args: str) -> list[str]:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_file_command(self, file: str) -> list[str]:
        """返回执行脚本文件的参数列表（shell=False 方式执行，避免命令注入）"""
        raise NotImplementedError()


class Bash(ShellBackend):
    CMD = "bash"
    SCRIPT_SUFFIX = ""

    def get_run_command(self, *args: str) -> list[str]:
        return list(args)

    def get_file_command(self, file: str) -> list[str]:
        return [self.CMD, file]


class Powershell(ShellBackend):
    CMD = "powershell"
    SCRIPT_SUFFIX = ".ps1"

    def get_run_command(self, *args: str) -> list[str]:
        return [self.CMD, "-Command", shlex.join(args)]

    def get_file_command(self, file: str) -> list[str]:
        return [self.CMD, "-File", file]


class Cmd(ShellBackend):
    CMD = "cmd.exe"
    SCRIPT_SUFFIX = ".bat"

    def get_run_command(self, *args: str) -> list[str]:
        return [self.CMD, "/c", shlex.join(args)]

    def get_file_command(self, file: str) -> list[str]:
        return [self.CMD, "/c", file]
