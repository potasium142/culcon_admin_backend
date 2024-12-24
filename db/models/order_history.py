from datetime import datetime
from enum import Enum

import sqlalchemy as sqla
from sqlalchemy import orm
from sqlalchemy.sql import sqltypes

from db.models import Base


class OrderStatus(Enum):
    CREATE = 1


class OrderHistory(Base):
    __tablename__: str = "order_history"
    id: orm.Mapped[int] = orm.mapped_column(sqltypes.BIGINT, primary_key=True)
    order_date: orm.Mapped[datetime] = orm.mapped_column(sqltypes.TIMESTAMP)
    delivery_address: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(255))
    note: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(255))
