from typing import Optional, Set
import uuid
from datetime import datetime

from pydantic import PrivateAttr

from pystonic.orm.database import get_session

from sqlmodel import Field, SQLModel, delete, select, update
from sqlalchemy import event


class DBModel(SQLModel):
    __abstract__ = True

    id: int = Field(default=None, primary_key=True)
    uuid: str = Field(default=None, nullable=False, unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.now, nullable=True)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=True)

    # 非 DB 属性：存储变化的值
    _modified_fields: Set[str] = PrivateAttr(default_factory=set)

    def __setattr__(self, field: str, value):
        """支持 dict-like 访问"""
        super().__setattr__(field, value)
        if field in self.__class__.model_fields:
            if not self.__pydantic_private__:
                self.__pydantic_private__ = {}
                self.__pydantic_private__["_modified_fields"] = set([])
            self._modified_fields.add(field)

    def _get_changes(self) -> dict:
        """返回字段名到 (原值, 新值) 的映射"""
        return {
            x: getattr(self, x)
            for x in self._modified_fields
            if x not in ["id", "uuid", "created_at", "updated_at"] and hasattr(self, x)
        }

    @classmethod
    def query(cls, *criterion, **filters):
        """返回一个 QueryBuilder 用于链式查询"""
        stm = select(cls).where(*criterion).filter_by(**filters)
        with get_session() as session:
            query = session.exec(stm)
            return query.all()

    @classmethod
    def get_by_id(cls, id: int, raise_if_not_exists: bool = False):
        items = cls.query(cls.id == id)
        if not items:
            if raise_if_not_exists:
                raise ValueError(f"{cls} with uuid {id} not exists")
            else:
                return None
        return items[0]

    @classmethod
    def delete_all(cls, *criterion, **filters):
        """删除所有符合条件的数据"""
        stm = delete(cls).where(*criterion)
        if filters:
            stm = stm.where(
                *[
                    getattr(cls, field_name) == value
                    for field_name, value in filters.items()
                ]
            )
        with get_session() as session:
            session.exec(stm)
            session.commit()

    @classmethod
    def get_by_uuid(cls, uuid: str):
        items = cls.query(cls.uuid == uuid)
        if not items:
            raise ValueError(f"{cls} with uuid {uuid} not exists")
        return items[0]

    @classmethod
    def delete_by_id(cls, id: int, raise_if_not_exists=False) -> None:
        """根据 id 删除记录"""
        stm = delete(cls).where(cls.id == id)  # type: ignore
        with get_session() as session:
            deleted_count = session.exec(stm)
            if not deleted_count and raise_if_not_exists:
                raise ValueError(f"id {id} not exists")
            session.commit()

    @classmethod
    def delete_by_uuid(cls, uuid: str, raise_if_not_exists=False) -> None:
        """根据 id 删除记录"""
        stm = delete(cls).where(cls.uuid == uuid)  # type: ignore
        with get_session() as session:
            delete_count = session.exec(stm)
            if not delete_count and raise_if_not_exists:
                raise ValueError(f"id {id} not exists")
            session.commit()

    @classmethod
    def update_by_uuid(cls, uuid: str, **kwargs) -> None:
        """根据 id 删除记录"""
        stm = update(cls).where(cls.uuid == uuid).values(**kwargs)  # type: ignore
        with get_session() as session:
            session.exec(stm)
            session.commit()

    def save(self):
        """更新当前实例到数据库，id 不存在则抛出异常"""
        if self.id is None:
            raise ValueError(f"{self.__class__} is not created")
        changes = self._get_changes()
        if not changes:
            return
        stm = (
            update(self.__class__).where(self.__class__.id == self.id).values(**changes) # type: ignore
        )
        with get_session() as session:
            session.exec(stm)
            session.commit()
        self._modified_fields.clear()

    def create(self):
        """创建新记录到数据库, id 已存在则抛出异常"""
        if self.id is not None or self.uuid is not None:
            raise ValueError(f"{self.__class__} is already created")
        # self.uuid = generate_uuid()
        with get_session() as session:
            session.add(self)
            session.commit()
            session.refresh(self)

    def delete(self):
        """删除当前实例"""
        if not self.id:
            raise ValueError("object not created")
        self.delete_by_id(self.id)


@event.listens_for(DBModel, "before_insert", propagate=True)
def before_insert(mapper, connection, target: DBModel):
    """插入时自动设置 uuid、create_at 和 update_at"""
    if target.uuid is None:
        target.uuid = str(uuid.uuid4())

    target.created_at = datetime.now()
    target.updated_at = datetime.now()


@event.listens_for(DBModel, "before_update", propagate=True)
def before_update(mapper, connection, target):
    """更新时自动设置 update_at"""
    target.updated_at = datetime.now()
