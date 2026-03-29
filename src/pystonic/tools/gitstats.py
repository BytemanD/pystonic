from typing import Tuple

import click
from pystonic.core import dateutil
from rich import box
from rich.console import Console
from rich.table import Column, Table
from rich.text import Text

from pystonic.extensions.gitstats import stats

console = Console()


@click.group()
def app():
    """Git Stats Tools"""


@app.command()
@click.argument("date_range", nargs=-1, default=[], required=False)
@click.option(
    "-s",
    "--sort-by",
    type=click.Choice(["total", "added", "removed", "commits"]),
    default="total",
    help="Sort by lines",
)
@click.option("--no-sort", is_flag=True, help="Do not sort the results")
def lines(date_range: Tuple[str], sort_by: str = "total", no_sort: bool = False):
    """Show commit lines

    \b
    e.g.
        git-rich-stats lines
        git-rich-stats lines <today | yesterday | thisweek | thismonth>
        git-rich-stats lines 2026-01-12 2026-01-22
        ...
    """
    try:
        since, until = dateutil.parse_date_range(date_range)
    except ValueError:
        raise click.BadParameter("parse date range error")

    console.print(
        f"{since:%Y-%m-%d %H:%M:%S} ~ {until:%Y-%m-%d %H:%M:%S}", style="cyan underline"
    )
    click.secho()
    commit_stats_list = stats.lines(since, until)
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


@app.command()
@click.argument("date_range", nargs=-1, default=[], required=False)
def commits(date_range: Tuple[str]):
    """Show commits"""
    try:
        since, until = dateutil.parse_date_range(date_range)
    except ValueError:
        raise click.BadParameter("parse date range error")
    commit_detail_list = stats.commits(since, until)

    console.print(
        f"{since:%Y-%m-%d %H:%M:%S} ~ {until:%Y-%m-%d %H:%M:%S}", style="cyan underline"
    )
    click.secho()

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


if __name__ == "__main__":
    app()
