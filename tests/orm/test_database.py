from sqlmodel import Field

from pystonic.orm.models import DBModel
from pystonic.orm.database import create_all_tables, get_table_structure


class SampleUser(DBModel, table=True):
    __tablename__ = "sample_users"

    name: str = Field(nullable=False, index=True)
    email: str = Field(nullable=True, unique=True)
    age: int = Field(nullable=True, default=18)


def test_get_table_structure():
    create_all_tables()

    structure = get_table_structure("sample_users")
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
