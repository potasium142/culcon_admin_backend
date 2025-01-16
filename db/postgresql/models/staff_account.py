import sqlalchemy as sqla

from uuid import UUID, uuid4
from sqlalchemy import orm
from sqlalchemy.sql import sqltypes
from enum import Enum, Flag
from datetime import date

from db.postgresql.models import Base


class AccountType(Flag):
    MANAGER = 1
    STAFF = 2


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISABLE = "DISABLE"


class EmployeeInfo(Base):
    __tablename__: str = "employee_info"
    account_id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey("staff_account.id"), primary_key=True
    )
    ssn: orm.Mapped[str] = orm.mapped_column(unique=True)
    phonenumber: orm.Mapped[str] = orm.mapped_column(unique=True)
    realname: orm.Mapped[str]
    email: orm.Mapped[str] = orm.mapped_column(unique=True)
    dob: orm.Mapped[date]


class StaffAccount(Base):
    __tablename__: str = "staff_account"
    id: orm.Mapped[str] = orm.mapped_column(
        sqltypes.UUID, primary_key=True, default=uuid4
    )
    username: orm.Mapped[str] = orm.mapped_column(unique=True)
    password: orm.Mapped[str]
    type: orm.Mapped[AccountType]
    status: orm.Mapped[AccountStatus]
    token: orm.Mapped[str]
    employee_info: orm.Mapped[EmployeeInfo] = orm.relationship()
