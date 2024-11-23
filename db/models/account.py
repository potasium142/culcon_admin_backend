import sqlalchemy as sqla
from uuid import UUID, uuid4
from sqlalchemy import orm
from enum import Enum
from datetime import date

from db.models import Base


class AccountType(Enum):
    MANAGER = 1
    STAFF = 2


class EmployeeInfo(Base):
    __tablename__ = "employee_info"
    account_id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey("account.id"), primary_key=True)
    ssn: orm.Mapped[str] = orm.mapped_column(unique=True)
    phonenumber: orm.Mapped[str] = orm.mapped_column(unique=True)
    realname: orm.Mapped[str]
    email: orm.Mapped[str] = orm.mapped_column(unique=True)
    dob: orm.Mapped[date]


class Account(Base):
    __tablename__ = "account"
    id: orm.Mapped[UUID] = orm.mapped_column(
        primary_key=True,
        default=uuid4
    )
    username: orm.Mapped[str] = orm.mapped_column(unique=True)
    password: orm.Mapped[str]
    type: orm.Mapped[AccountType]
    token: orm.Mapped[str]
    employee_info: orm.Mapped[EmployeeInfo] = orm.relationship()
