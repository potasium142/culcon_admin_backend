import datetime
import sqlalchemy as sqla

from sqlalchemy import orm
from sqlalchemy.sql import sqltypes

from db.postgresql.models import Base
from db.postgresql.models.staff_account import StaffAccount


class ShiperAvailbility(Base):
    __tablename__ = "shipper_availbility"
    id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey(StaffAccount.id),
        primary_key=True,
    )
    start_shift: orm.Mapped[datetime.time] = orm.mapped_column(sqltypes.TIME)
    end_shift: orm.Mapped[datetime.time] = orm.mapped_column(sqltypes.TIME)
    available: orm.Mapped[bool]
