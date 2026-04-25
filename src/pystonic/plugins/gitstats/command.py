import argparse
from typing import Set

from rich import box
from rich.console import Console
from rich.table import Column, Table
from rich.text import Text

from pystonic.core import dateutil
from pystonic.core.plugin import CommandPlugin, hookimpl
from pystonic.plugins.gitstats import utils


class Command(CommandPlugin):
    name = "gitstats"

    @hookimpl
    def register_subcommand(self, subparsers: argparse._SubParsersAction):
        parser_root = subparsers.add_parser(self.name)
        subparsers = parser_root.add_subparsers(dest="subcommand", required=True)

        parser_lines = subparsers.add_parser("lines")
        parser_lines.add_argument("date_range", nargs='*', help="date range to get lines for")
        parser_lines.add_argument(
            "-s",
            "--sort-by",
            default="total",
            choices=["total", "added", "removed", "commits"],
            help="Sort by lines",
        )
        parser_lines.add_argument(
            "--no-sort", action="store_true", help="Do not sort the results"
        )

        parser_commits = subparsers.add_parser("commits")
        parser_commits.add_argument("date_range", nargs='*', help="date range to get lines for")

    def run(self, args):
        if args.subcommand == "lines":
            self._run_lines(
                date_range=args.date_range, sort_by=args.sort_by, no_sort=args.no_sort
            )
        else:
            self._run_commits(date_range=args.date_range)

    def _run_lines(
        self, date_range: Set[str], sort_by: str = "total", no_sort: bool = False
    ):
        """Show commit lines

        \b
        e.g.
            git-rich-stats lines
            git-rich-stats lines <today | yesterday | thisweek | thismonth>
            git-rich-stats lines 2026-01-12 2026-01-22
            ...
        """
        console = Console()
        try:
            since, until = dateutil.parse_date_range(date_range)
        except ValueError:
            raise ValueError("parse date range error")

        console.print(
            f"{since:%Y-%m-%d %H:%M:%S} ~ {until:%Y-%m-%d %H:%M:%S}",
            style="cyan underline",
        )
        console.print()
        commit_stats_list = utils.lines(since, until)
        if not no_sort:
            commit_stats_list.sort(key=lambda x: getattr(x, sort_by))
        table = Table(
            Column("Author", justify="left"),
            Column("Added", justify="right"),
            Column("Removed", justify="right"),
            Column("Total", justify="right"),
            Column("Commits", justify="right"),
            title="Code lines",
            box=box.SIMPLE,
        )

        for commit_stats in commit_stats_list:
            table.add_row(
                commit_stats.author,
                Text(str(commit_stats.added), style="green"),
                Text(str(commit_stats.removed), style="red"),
                Text(str(commit_stats.total), style="magenta"),
                str(commit_stats.commits),
            )

        console.print(table)

    def _run_commits(self, date_range: Set[str]):
        """Show commits"""
        console = Console()

        try:
            since, until = dateutil.parse_date_range(date_range)
        except ValueError:
            raise ValueError("parse date range error")
        commit_detail_list = utils.commits(since, until)

        console.print(
            f"{since:%Y-%m-%d %H:%M:%S} ~ {until:%Y-%m-%d %H:%M:%S}",
            style="cyan underline",
        )
        console.print()
        table = Table(
            Column("Date"),
            Column("Author", justify="left"),
            Column("Message", justify="left"),
            Column("Changes", justify="left", no_wrap=True),
            title="Commit Details",
            show_lines=True,
        )
        for item in commit_detail_list:
            table.add_row(
                item.date,
                item.author,
                Text(str(item.message), style="red" if "fix" in item.message else ""),
                "\n".join(item.changes),
            )

        console.print(table)
