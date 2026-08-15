from datetime import datetime
from typing import List, Optional, Tuple


import click
from pydantic import BaseModel, ConfigDict
from rich import box
from rich.console import Console
from rich.table import Column
from rich.text import Text

from pystonic.core import dateutil
from pystonic.pretty import output

from pystonic.git import utils


def parse_date_range(since: str, until: Optional[str]) -> Tuple[datetime, datetime]:
    """Parse date range"""
    if not until:
        if not since or since in ["today", "thisday"]:
            return dateutil.thisday()
        if since == "yesterday":
            return dateutil.yestoday()
        if since == "thisweek":
            return dateutil.thisweek()
        if since == "lastweek":
            return dateutil.lastweek()
        if since == "thismonth":
            return dateutil.thismonth()
        if since == "lastmonth":
            return dateutil.lastmonth()
        return datetime.strptime(since, dateutil.FORMAT_DATETIME), datetime.now()

    return datetime.strptime(since, dateutil.FORMAT_DATETIME), datetime.strptime(
        until, dateutil.FORMAT_DATETIME
    )


class CodeLines(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    author: str
    added: Text
    removed: Text
    total: Text
    commits: int


@click.group("gitstats")
def root():
    pass


@root.command()
@click.argument("date_range", required=False, nargs=-1)
@click.option(
    "-s",
    "--sort-by",
    type=click.Choice(["total", "added", "removed", "commits"]),
    default="total",
    help="Sort by",
)
def lines(
    date_range: List[str],
    sort_by: Optional[str] = None,
):
    if not date_range:
        date_range = ["today"]

    try:
        since, until = parse_date_range(
            date_range[0], until=date_range[1] if len(date_range) > 1 else None
        )
    except ValueError as e:
        raise ValueError(f"parse date range error: {e}")

    console = Console()
    console.print(
        f"{since:%Y-%m-%d %H:%M:%S} ~ {until:%Y-%m-%d %H:%M:%S}",
        style="cyan underline",
    )
    console.print()
    commit_stats_list = utils.lines(since, until)
    if sort_by:
        commit_stats_list.sort(key=lambda x: getattr(x, sort_by))

    output.print_models(
        [
            CodeLines(
                author=x.author,
                added=Text(str(x.added), style="green"),
                removed=Text(str(x.removed), style="red"),
                total=Text(str(x.total), style="magenta"),
                commits=x.commits,
            )
            for x in commit_stats_list
        ],
        fields=[
            Column("author", justify="left"),
            Column("added", justify="right"),
            Column("removed", justify="right"),
            Column("total", justify="right"),
            Column("commits", justify="right"),
        ],
        title="Code lines",
        box=box.SIMPLE,
    )


@root.command()
@click.argument("date_range", required=False, nargs=-1, default=["today"])
@click.option("--author", "-a", help="Filter commits by author")
@click.option("--changes", is_flag=True, help="show changes")
def commits(
    date_range: List[str],
    changes: bool = False,
    author: Optional[str] = None,
):
    if not date_range:
        date_range = ["today"]

    console = Console()

    try:
        since, until = parse_date_range(
            date_range[0], until=date_range[1] if len(date_range) > 1 else None
        )
    except ValueError as e:
        raise ValueError(f"parse date range error: {e}")
    commits = utils.commits(since, until, author=author)

    console.print(
        f"{since:%Y-%m-%d %H:%M:%S} ~ {until:%Y-%m-%d %H:%M:%S}",
        style="cyan underline",
    )
    console.print()
    fields: List[str | Column] = [
        Column("date"),
        Column("author", justify="left"),
        Column("hexsha", justify="left"),
        Column("message", justify="left"),
    ]
    if changes:
        for x in range(len(commits)):
            commits[x].changes = "\n".join(commits[x].changes)
        fields.append(Column("changes", justify="left", no_wrap=True))

    output.print_models(commits, fields=fields, show_lines=True)
