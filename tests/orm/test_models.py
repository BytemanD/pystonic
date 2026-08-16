from sqlmodel import Field

from pystonic.orm.models import DBModel
from pystonic.orm.database import create_all_tables


class User(DBModel, table=True):
    name: str = Field()

def test_create_all_tables():
    create_all_tables()


def test_crud():
    user = User(name='foo')
    user.create()
    db_item = User.get_by_id(user.id)
    assert db_item is not None
    assert db_item.name == 'foo'

    user.name = 'bar'
    user.save()
    db_item = User.get_by_id(user.id)
    assert db_item is not None
    assert db_item.name == 'bar'

    user.delete()
    db_item = User.get_by_id(user.id)
    assert db_item is None
