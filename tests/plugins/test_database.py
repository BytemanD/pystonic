from sqlalchemy import Column, Integer, String

from pystonic.conf import DBConfig
from pystonic.plugins.orm.database import (
    Base,
    create_all_tables,
    get_table_structure,
    setup,
)


class SampleUser(Base):
    __tablename__ = "sample_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, index=True)
    email = Column(String(100), unique=True)
    age = Column(Integer, nullable=True, default=18)


def test_get_table_structure():
    db_config = DBConfig(connection="sqlite:///:memory:")
    setup(db_config)
    create_all_tables()

    structure = get_table_structure("sample_users")

    assert len(structure) == 4

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
