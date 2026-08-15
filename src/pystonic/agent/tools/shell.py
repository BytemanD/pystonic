import os
import subprocess
import tempfile

from agents import function_tool
from loguru import logger
from pystonic.shell import Shell


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
            except Exception as e:
                logger.exception("Failed to run code block")
                output = str(e)
            finally:
                logger.debug("Remove file: {}", file.name)
                os.remove(file.name)
        return output


executor = ShellWrapper()


@function_tool
def execute_command(command: str) -> str:
    """执行 Shell/Bash/Cmd/Powershell 命令"""
    return executor.execute(command)
