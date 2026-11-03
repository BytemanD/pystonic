import uuid

import pytest
from sqlmodel import Field

from pystonic.orm import database
from pystonic.orm.models import DBModel

TABLE_NAME = f"test_sample_user_{uuid.uuid4()}"


class SampleUser(DBModel, table=True):
    __tablename__ = TABLE_NAME  # type: ignore
    name: str = Field()


@pytest.fixture(scope="function", autouse=True)
def create_table():
    database.create_all_tables()
    yield
    database.drop_all_tables()


def test_crud():
    user = SampleUser(name="foo")
    user.create()
    assert user.id
    assert user.uuid

    db_item = SampleUser.get_by_id(user.id)
    assert db_item is not None
    assert db_item.name == "foo"

    user.name = "bar"
    user.save()
    db_item = SampleUser.get_by_uuid(user.uuid)
    assert db_item is not None
    assert db_item.name == "bar"

    user.delete()
    db_item = SampleUser.get_by_id(user.id)
    assert db_item is None


def test_delete_all():
    user = SampleUser(name="foo")
    user.create()
    assert len(SampleUser.query()) == 1

    SampleUser.delete_all()
    assert len(SampleUser.query()) == 0


def test_delete():
    user = SampleUser(name="foo")
    user.create()
    user.delete()
    assert not SampleUser.get_by_id(user.id)
