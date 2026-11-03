import uuid

import pytest
from sqlmodel import Field

from pystonic.orm import database
from pystonic.orm.models import DBModel

TABLE_NAME = f"test_sample_model_{uuid.uuid4()}"


class SampleModel(DBModel, table=True):
    __tablename__ = TABLE_NAME  # type: ignore

    name: str = Field(nullable=False, index=True)
    email: str = Field(nullable=True, unique=True)
    age: int = Field(nullable=True, default=18)


@pytest.fixture(scope="module", autouse=True)
def create_table():
    database.create_all_tables()
    yield
    database.drop_all_tables()


def test_get_table_structure():
    structure = database.get_table_structure(TABLE_NAME)
    name_map = {col.name: col for col in structure}

    assert name_map["id"].primary_key is True
    assert name_map["id"].nullable is False
    assert "integer" in name_map["id"].type.lower()

    assert name_map["name"].nullable is False
    assert name_map["name"].indexed is True
    assert name_map["name"].unique is False
    assert "varchar" in name_map["name"].type.lower()

    assert name_map["email"].nullable is True
    assert name_map["email"].unique is True

    assert name_map["age"].nullable is True
    assert name_map["age"].default is None
