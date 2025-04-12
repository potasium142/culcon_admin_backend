import datetime
from enum import Enum
import sqlalchemy as sqla

from sqlalchemy import orm
from sqlalchemy.sql import sqltypes

from db.postgresql.models import Base
from db.postgresql.models.order_history import OrderProcess
from db.postgresql.models.staff_account import StaffAccount


class ShipperStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    ON_SHIPPING = "ON_SHIPPING"
    DELIVERED = "DELIVERED"
    ASSIGN = "ASSIGN"
    IDLE = "IDLE"


class ShipperAvailbility(Base):
    __tablename__ = "shipper_availbility"
    id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey(StaffAccount.id),
        primary_key=True,
    )
    start_shift: orm.Mapped[datetime.time | None] = orm.mapped_column(
        sqltypes.TIME, default=None
    )
    end_shift: orm.Mapped[datetime.time | None] = orm.mapped_column(
        sqltypes.TIME, default=None
    )
    current_order: orm.Mapped[str | None] = orm.mapped_column(
        sqla.ForeignKey(OrderProcess.order_id), default=None
    )
    status: orm.Mapped[ShipperStatus] = orm.mapped_column(default=ShipperStatus.IDLE)
