from typing import List, Optional, Sequence, Union

from pydantic import BaseModel
from rich.console import Console
from rich.prompt import Prompt


from rich.table import Column, Table
from rich.box import Box


def print_model_data(items: Sequence[BaseModel]):
    pass


class DataTable:
    pass


def make_data_table(
    columns: List[Union[Column, str]],
    items: Sequence[BaseModel],
    title: Optional[str] = None,
    box: Optional[Box] = None,
    **table_settings,
) -> Table:

    table_columns = [x if isinstance(x, Column) else Column(x) for x in columns]
    table = Table(*table_columns, box=box, title=title, **table_settings)
    for item in items:
        table.add_row(*[str(getattr(item, str(x.header))) for x in table_columns])
    return table


def select_items(
    items: List[str],
    default_index: Optional[int] = None,
    select_prompt: Optional[str] = None,
    input_prompt: Optional[str] = None,
) -> Optional[str]:
    """打印items列表, 并获取用户选择结果"""
    if default_index is not None and not (0 < default_index <= len(items)):
        raise ValueError("default_index out of range")

    select_prompt = select_prompt or "请选择:"
    input_prompt = input_prompt or "请输入编号"

    console = Console()
    console.print(f"---- {select_prompt} ----", style="yellow")
    for i, item in enumerate(items, start=1):
        console.print(f"{i:<{len(str(len(items)))}}. {item}")
    selected = Prompt.ask(
        f" [bold cyan]{input_prompt} [/bold cyan]",
        choices=[str(i) for i in range(1, len(items) + 1)],
        show_choices=False,
        default=str(default_index) if default_index else None,
    )
    return items[int(selected) - 1] if selected is not None else None
