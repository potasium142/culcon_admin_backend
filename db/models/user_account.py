from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

import sqlalchemy as sqla
from sqlalchemy import Column, orm
from sqlalchemy.dialects.postgresql import ARRAY, VARCHAR
from sqlalchemy.sql import sqltypes

from db.models import Base
from db.models.product import Product


class UserAccountStatus(Enum):
    NON_ACTIVE = 1
    NORMAL = 2
    BANNED = 3
    DEACTIVATE = 4


class UserAccount(Base):
    __tablename__: str = "user_account"
    id: orm.Mapped[UUID] = orm.mapped_column(
        primary_key=True, default=uuid4, unique=True
    )
    email: orm.Mapped[str] = orm.mapped_column(unique=True)
    username: orm.Mapped[str] = orm.mapped_column(unique=True)
    password: orm.Mapped[str]
    status: orm.Mapped[UserAccountStatus]
    address: orm.Mapped[str]
    phone: orm.Mapped[str]
    profile_pic_uri: orm.Mapped[str]
    profile_description: orm.Mapped[str]
    token: orm.Mapped[str]
    cart: orm.Mapped[list["Cart"]] = orm.relationship()
    bookmarked_posts: orm.Mapped[list[str]] = orm.mapped_column(ARRAY(VARCHAR(255)))


class Cart(Base):
    __tablename__: str = "cart"
    amount: orm.Mapped[int]
    account_id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey("user_account.id"), primary_key=True
    )
    product_id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey("product.id"), primary_key=True
    )


class PostComment(Base):
    __tablename__: str = "post_comment"
    timestamp: orm.Mapped[datetime] = orm.mapped_column(sqltypes.TIMESTAMP)
    post_id: orm.Mapped[str] = orm.mapped_column(
        sqltypes.VARCHAR(255), primary_key=True
    )
    account_id: orm.Mapped[UserAccount] = orm.mapped_column(
        sqltypes.UUID, sqla.ForeignKey("user_account.id"), primary_key=True
    )
    comment: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(255))


class AccountOTP(Base):
    __tablename__: str = "account_otp"
    id: orm.Mapped[int] = orm.mapped_column(sqltypes.BIGINT, primary_key=True)
    account_id: orm.Mapped[UserAccount] = orm.mapped_column(
        sqla.ForeignKey("user_account.id")
    )
    email: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(255))
    otp: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(255))
    activity_type: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(255))
    otp_expiration: orm.Mapped[datetime] = orm.mapped_column(sqltypes.TIMESTAMP)
