from typing import List, Sequence

from pydantic import BaseModel
from rich.console import Console
from rich.table import Column, Table


def print_model(item: BaseModel, fields: List[str] = None):
    fields = fields or [x for x in item.__class__.model_fields.keys()]

    table = Table(Column("Field", justify="left"), Column("Value", justify="left"))

    for field in fields:
        table.add_row(field, str(getattr(item, field)))

    Console().print(table)


def print_models(
    items: Sequence[BaseModel],
    fields: List[str] = None,
    headers: dict[str, Column] = {},
):
    if not fields:
        fields = [x for x in items[0].__class__.model_fields.keys()] if items else []

    table = Table(*[headers.get(x, Column(x)) for x in fields])
    for item in items:
        table.add_row(*[str(getattr(item, x)) for x in fields])
    Console().print(table)
