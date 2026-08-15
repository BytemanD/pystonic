import os
from pathlib import Path
from typing import List

from termcolor import cprint

from pystonic.core.pkg import is_package_installed


def check_code(
    source_paths: List[str | Path],
    test=False,
    cover=False,
    cover_path="src",
    cover_fail_under=80,
    bandit=False,
):
    soruce_paths = " ".join([str(x) for x in source_paths])
    commands = [f"ruff format {soruce_paths}", f"ruff check --fix {soruce_paths}"]
    if test:
        # 检查 pytest 是否安装
        if not is_package_installed("pytest"):
            print("❌ Error: pytest is not installed. Please install it first.")
            return
        pytest_cmd = "pytest"
        # 如果启用覆盖率检查，验证 pytest-cov 是否安装
        if cover:
            if not is_package_installed("pytest_cov"):
                print("❌ Error: pytest-cov is not installed. Please install it first.")
                return
            pytest_cmd += f" --cov={cover_path} --cov-report=term --cov-fail-under={cover_fail_under}"

        commands.append(pytest_cmd)

    if bandit:
        if not is_package_installed("bandit"):
            print("❌ Error: bandit is not installed. Please install it first.")
            return
        commands.append(f"bandit -r {' '.join(soruce_paths)}")

    for command in commands:
        cprint(f"🚀 {command}", color="magenta", attrs=["bold"])

        os.system(command)
        print()
