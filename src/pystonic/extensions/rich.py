from typing import List, Literal, Optional, Sequence, Union

from pydantic import BaseModel
from rich import box
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
    none_value: Optional[str] = None,
    header_format: Literal[None, "title", "upper"] = "title",
    slots: Optional[dict[str, callable]] = None,
    title: Optional[str] = None,
    box: Optional[Box] = box.HEAVY_HEAD,
    **table_settings,
) -> Table:
    """Make a rich Table from items
    Args:
        columns: List of column names or Column objects
        items: List of BaseModel items to display
        none_value: Value to display for None fields
        header_format: Format for the header ('title', 'upper', or None)
        slots: Optional dict of field name to function for custom field value
        title: Optional table title
        box: Optional box style for the table
        **table_settings: Additional settings for the Table constructor
    """
    fields = [str(x.header) if isinstance(x, Column) else x for x in columns]
    table_columns = [x if isinstance(x, Column) else Column(x.title()) for x in columns]
    if header_format:
        for column in table_columns:
            if not isinstance(column.header, str):
                continue
            if header_format == "title":
                column.header = column.header.title()
            elif header_format == "upper":
                column.header = column.header.upper()

    table = Table(*table_columns, box=box, title=title, **table_settings)

    def _get_field_value(item: BaseModel, field_name: str):
        if slots and field_name in slots:
            return slots[field_name](item)
        return getattr(item, field_name, none_value)

    for item in items:
        table.add_row(*[str(_get_field_value(item, x)) for x in fields])
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
