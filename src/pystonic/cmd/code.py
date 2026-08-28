import os
from pathlib import Path
from typing import List


import click

from pystonic.utils.pkg import is_package_installed


def _get_source_paths() -> List[str | Path]:
    """查找python代码所在的目录"""
    source_paths: List[str | Path] = []
    for path in ["src", "tests"]:
        if os.path.exists(path):
            source_paths.append(path)
    if not source_paths:
        source_paths.append(".")
    return source_paths


def check_code(
    source_paths: List[str | Path],
    test=False,
    cover=False,
    cover_path="src",
    cover_fail_under=80,
    bandit=False,
):
    source_arg = " ".join([str(x) for x in source_paths])
    commands = [f"ruff format {source_arg}", f"ruff check --fix {source_arg}"]
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
        commands.append(f"bandit -r {source_arg}")

    for command in commands:
        click.secho(f"🚀 {command}", fg="magenta")
        os.system(command)
        # click.echo(output)
        print()


@click.group("code")
def root():
    pass


@root.command()
@click.option("-t", "--test", is_flag=True, help="Run tests with pytest")
@click.option("-b", "--bandit", is_flag=True, help="Run check with bandit")
@click.option("-c", "--cover", is_flag=True, help="Run pytest with coverage")
@click.option(
    "-u",
    "--cover-failed-under",
    type=int,
    default=80,
    help="Minimum coverage percentage required",
)
@click.option(
    "-p",
    "--cover-path",
    default="src",
    help="Path to the source code for coverage",
)
def check(
    test: bool, bandit: bool, cover: bool, cover_failed_under: int, cover_path: str
):
    check_code(
        _get_source_paths(),
        test=test,
        bandit=bandit,
        cover=cover,
        cover_fail_under=cover_failed_under,
        cover_path=cover_path,
    )
