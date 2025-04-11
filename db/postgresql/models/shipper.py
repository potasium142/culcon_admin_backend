import datetime
import sqlalchemy as sqla

from sqlalchemy import orm
from sqlalchemy.sql import sqltypes

from db.postgresql.models import Base
from db.postgresql.models.staff_account import StaffAccount


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
    occupied: orm.Mapped[bool] = orm.mapped_column(default=False)
