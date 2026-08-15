from typing import List, Optional, Sequence

from pydantic import BaseModel
from rich import box
from rich.console import Console
from rich.table import Column, Table

console = Console()


def print_model(item: BaseModel, fields: List[str] = []):
    fields = fields or [x for x in item.__class__.model_fields.keys()]

    table = Table(Column("Field", justify="left"), Column("Value", justify="left"))

    for field in fields:
        table.add_row(field, str(getattr(item, field)))

    console.print(table)


def print_models(
    items: Sequence[BaseModel],
    fields: List[str | Column] = [],
    title: Optional[str] = None,
    box: Optional[box.Box] = box.HEAVY_HEAD,
    show_lines: bool = False,
):
    if not items:
        console.print("No items", style="yellow")
        return
    if not fields:
        fields = [x for x in items[0].__class__.model_fields.keys()] if items else []

    model_fields = [x if isinstance(x, str) else str(x.header) for x in fields]
    headers = [Column(x) if isinstance(x, str) else x for x in fields]

    table = Table(*headers, title=title, box=box, show_lines=show_lines)
    for item in items:
        table.add_row(*[str(getattr(item, x)) for x in model_fields])
    console.print(table)
