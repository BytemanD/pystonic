import argparse
import os
from typing import List

from pystonic.core.plugin import CommandPlugin, hookimpl
from pystonic.plugins.code import utils


def _get_source_paths():
    """查找python代码所在的目录"""
    source_paths: List[str] = []
    for path in ["src", "tests"]:
        if os.path.exists(path):
            source_paths.append(path)
    if not source_paths:
        source_paths.append(".")
    return source_paths


class Command(CommandPlugin):
    name = "code"

    @hookimpl
    def register_subcommand(self, subparsers: argparse._SubParsersAction):
        parser_root = subparsers.add_parser(self.name)
        subparsers = parser_root.add_subparsers(dest="subcommand", required=True)

        parser_check = subparsers.add_parser("check")

        parser_check.add_argument(
            "-t",
            "--test",
            action="store_true",
            help="Run tests with pytest",
        )
        parser_check.add_argument(
            "-b",
            "--bandit",
            action="store_true",
            help="Run check with bandit",
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

    def run(self, args):
        if args.subcommand == "check":
            utils.check_code(
                _get_source_paths(),
                test=args.test,
                cover=args.cover,
                cover_path=args.cover_path,
                cover_fail_under=args.cover_failed_under,
                bandit=args.bandit,
            )
