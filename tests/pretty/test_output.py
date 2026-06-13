from datetime import datetime
from unittest.mock import Mock, patch

from pydantic import BaseModel
from rich.table import Column, Table

from pystonic.pretty.output import print_model, print_models


class Foo(BaseModel):
    name: str
    age: int
    is_active: bool
    created_at: datetime


@patch("rich.console.Console.print")
def test_print_model(mock_console_print: Mock):
    now = datetime.now()
    model = Foo(name="John", age=30, is_active=True, created_at=now)
    print_model(model)

    mock_console_print.assert_called_once()
    table = mock_console_print.call_args[0][0]
    assert isinstance(table, Table)
    assert len(table.columns) == 2

    column1, column2 = table.columns[0], table.columns[1]
    assert isinstance(column1, Column)
    assert isinstance(column2, Column)

    assert column1.header == "Field"
    assert column2.header == "Value"

    assert table.row_count == 4
    assert [x for x in column1.cells] == ["name", "age", "is_active", "created_at"]
    assert [x for x in column2.cells] == [
        str(model.name),
        str(model.age),
        str(model.is_active),
        str(model.created_at),
    ]


@patch("rich.console.Console.print")
def test_print_models(mock_console_print: Mock):
    models = [
        Foo(name="John", age=30, is_active=True, created_at=datetime.now()),
        Foo(name="Jane", age=28, is_active=False, created_at=datetime.now()),
    ]
    print_models(models)

    mock_console_print.assert_called_once()
    table = mock_console_print.call_args[0][0]

    assert isinstance(table, Table)
    assert len(table.columns) == 4
    column1, column2, column3, column4 = (
        table.columns[0],
        table.columns[1],
        table.columns[2],
        table.columns[3],
    )
    assert column1.header == "name"
    assert column2.header == "age"
    assert column3.header == "is_active"
    assert column4.header == "created_at"

    assert table.row_count == 2
    assert [x for x in column1.cells] == [str(models[0].name), str(models[1].name)]
    assert [x for x in column2.cells] == [str(models[0].age), str(models[1].age)]
    assert [x for x in column3.cells] == [
        str(models[0].is_active),
        str(models[1].is_active),
    ]
    assert [x for x in column4.cells] == [
        str(models[0].created_at),
        str(models[1].created_at),
    ]


@patch("rich.console.Console.print")
def test_print_models_with_empty_items(mock_console_print: Mock):
    print_models([])

    mock_console_print.assert_called_once()
    table = mock_console_print.call_args[0][0]

    assert isinstance(table, Table)
    assert len(table.columns) == 0
    assert table.row_count == 0


@patch("rich.console.Console.print")
def test_print_models_with_custom_fields(mock_console_print: Mock):
    print_models([], fields=["name", "age"])

    mock_console_print.assert_called_once()
    table = mock_console_print.call_args[0][0]

    assert isinstance(table, Table)
    assert len(table.columns) == 2
    assert [x.header for x in table.columns] == ["name", "age"]

    assert table.row_count == 0
