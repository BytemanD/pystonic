import argparse
import os
from pystonic.core.pkg import is_package_installed

from termcolor import cprint


def _get_source_paths():
    """查找python代码所在的目录"""
    source_paths = []
    for path in ["src", "tests"]:
        if os.path.exists(path):
            source_paths.append(path)
    if not source_paths:
        source_paths.append(".")
    return source_paths


def check_code(test=False, cover=False, cover_path="src", cover_fail_under=80):
    soruce_paths = " ".join(_get_source_paths())
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
            pytest_cmd += (
                f" --cov=src --cov-report=term --cov-fail-under={cover_fail_under}"
            )

        commands.append(pytest_cmd)

    for command in commands:
        cprint(f"🚀 {command}", color="magenta", attrs=["bold"])

        os.system(command)
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Code Quality Tools",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_check = subparsers.add_parser("check")
    parser_check.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="Run tests with pytest",
    )
    parser_check.add_argument(
        "-c", "--cover", action="store_true", help="Run pytest with coverage"
    )
    parser_check.add_argument(
        "-u",
        "--cover-failed-under",
        type=int,
        default=80,
        help="Minimum coverage percentage required",
    )
    parser_check.add_argument(
        "-p",
        "--cover-path",
        type=str,
        default="src",
        help="Path to the source code for coverage",
    )
    args = parser.parse_args()

    if args.command == "check":
        check_code(
            test=args.test,
            cover=args.cover,
            cover_fail_under=args.cover_failed_under,
            cover_path=args.cover_path,
        )


if __name__ == "__main__":
    main()
