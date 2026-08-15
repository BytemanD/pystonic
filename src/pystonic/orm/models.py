import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, event, func
from sqlalchemy.orm import Mapped, mapped_column

from pystonic.orm.database import Base


def db_session():
    from pystonic.orm.database import _SessionLocal

    return _SessionLocal()


class DBModel(Base):
    __abstract__ = True  # 表示这是一个抽象基类，不会创建单独的表

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),  # 数据库默认值（创建时）
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),  # 更新时自动修改
        nullable=False,
    )

    # 非 DB 属性：存储加载时的原始值
    _changes: dict = {}

    def __setattr__(self, name, value):
        """支持 dict-like 访问"""
        if name not in self.__table__.columns.keys():
            object.__setattr__(self, name, value)
        if getattr(self, name) != value:
            self._changes[name] = value
        object.__setattr__(self, name, value)

    def _get_changes(self) -> dict:
        """返回字段名到 (原值, 新值) 的映射"""
        return {
            k: v
            for k, v in self._changes.items()
            if k not in ["id", "uuid", "created_at", "updated_at"] and hasattr(self, k)
        }

    @classmethod
    def delete_all(cls, *criterion, **filters):
        """删除所有符合条件的数据"""
        with db_session() as session:
            query = session.query(cls)
            if criterion:
                query = query.filter(*criterion)
            elif filters:
                query = query.filter_by(**filters)
            query.delete()
            session.commit()

    @classmethod
    def query(cls, *criterion, **filters):
        """返回一个 QueryBuilder 用于链式查询"""
        with db_session() as session:
            query = session.query(cls)
            if criterion:
                query = query.filter(*criterion)
            elif filters:
                query = query.filter_by(**filters)
        return query

    @classmethod
    def get_by_id(cls, id: int):
        items = cls.query(cls).filter(cls.id == id)
        if not items:
            raise ValueError(f"{cls} with uuid {id} not exists")
        return items[0]

    @classmethod
    def get_by_uuid(cls, uuid: str):
        items = cls.query(cls).filter(cls.uuid == uuid)
        if not items:
            raise ValueError(f"{cls} with uuid {uuid} not exists")
        return items[0]

    @classmethod
    def delete_by_id(cls, id: int, ignore_not_exists=False) -> None:
        """根据 id 删除记录"""
        if not ignore_not_exists:
            cls.get_by_id(id)
        with db_session() as session:
            session.query(cls).filter(cls.id == id).delete()
            session.commit()

    @classmethod
    def delete_by_uuid(cls, uuid: str, ignore_not_exists=False) -> None:
        """根据 id 删除记录"""
        if not ignore_not_exists:
            cls.get_by_uuid(uuid)
        with db_session() as session:
            session.query(cls).filter(cls.uuid == uuid).delete()
            session.commit()

    @classmethod
    def update_by_uuid(cls, uuid: str, **kwargs) -> None:
        """根据 id 删除记录"""
        with db_session() as session:
            session.query(cls).filter(cls.uuid == uuid).update(**kwargs)
            session.commit()

    def _get_updated(self) -> dict:
        updated = {}
        for field in self.__table__.columns.keys():
            if field in ["id", "uuid", "create_at", "update_at"]:
                continue
            updated[field] = getattr(self, field)
        return updated

    def save(self):
        """更新当前实例到数据库，id 不存在则抛出异常"""
        if self.id is None:
            raise ValueError(f"{self.__class__} is not created")
        changes = self._get_changes()
        if not changes:
            return
        with db_session() as session:
            session.query(self.__class__).filter_by(id=self.id).update(changes)
            session.commit()

    def create(self):
        """创建新记录到数据库, id 已存在则抛出异常"""
        if self.id is not None or self.uuid is not None:
            raise ValueError(f"{self.__class__} is already created")
        # self.uuid = generate_uuid()
        with db_session() as session:
            session.add(self)
            session.commit()
            session.refresh(self)

    def delete(self):
        """删除当前实例"""
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
