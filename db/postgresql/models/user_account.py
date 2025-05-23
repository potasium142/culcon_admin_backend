from datetime import datetime
from enum import Enum
from uuid import UUID

import sqlalchemy as sqla
from sqlalchemy import orm
from sqlalchemy.dialects.postgresql import ARRAY, VARCHAR
from sqlalchemy.sql import sqltypes

from db.postgresql.models import Base
from db.postgresql.models.blog import Blog
from db.postgresql.models.product import Product


class UserAccountStatus(str, Enum):
    NORMAL = "NORMAL"
    BANNED = "BANNED"


class OnlineStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


class UserAccount(Base):
    __tablename__: str = "user_account"
    id: orm.Mapped[UUID] = orm.mapped_column(
        sqltypes.VARCHAR(255), primary_key=True, unique=True
    )
    email: orm.Mapped[str] = orm.mapped_column(unique=True)
    username: orm.Mapped[str] = orm.mapped_column(unique=True)
    profile_name: orm.Mapped[str] = orm.mapped_column(
        VARCHAR(255),
    )
    password: orm.Mapped[str]
    status: orm.Mapped[UserAccountStatus]
    address: orm.Mapped[str]
    phone: orm.Mapped[str] = orm.mapped_column(unique=True)
    profile_pic_uri: orm.Mapped[str] = orm.mapped_column(
        default="defaultProfile",
    )
    profile_description: orm.Mapped[str]
    token: orm.Mapped[str] = orm.mapped_column(unique=True)
    cart: orm.Mapped[list["Cart"]] = orm.relationship(back_populates="user")
    online_status: orm.Mapped[OnlineStatus] = orm.mapped_column(
        default=OnlineStatus.OFFLINE
    )
    order_history: orm.Mapped[list["OrderHistory"]] = orm.relationship(
        back_populates="user"
    )
    chatlog: orm.Mapped["ChatHistory"] = orm.relationship(back_populates="user")


class Cart(Base):
    __tablename__: str = "cart"
    amount: orm.Mapped[int]
    account_id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey("user_account.id"), primary_key=True
    )
    product_id: orm.Mapped[Product] = orm.mapped_column(
        sqla.ForeignKey(Product.id), primary_key=True
    )
    user: orm.Mapped[UserAccount] = orm.relationship(back_populates="cart")


class CommentType(str, Enum):
    POST = "POST"
    REPLY = "REPLY"


class CommentStatus(str, Enum):
    NORMAL = "NORMAL"
    REPORTED = "REPORTED"
    DELETED = "DELETED"


class PostComment(Base):
    __tablename__: str = "post_comment"
    id: orm.Mapped[str] = orm.mapped_column(
        sqltypes.VARCHAR(255),
        primary_key=True,
    )
    timestamp: orm.Mapped[datetime] = orm.mapped_column(sqltypes.TIMESTAMP)
    post_id: orm.Mapped[str] = orm.mapped_column(
        sqltypes.VARCHAR(255),
        sqla.ForeignKey(Blog.id),
    )
    account_id: orm.Mapped[UserAccount | None] = orm.mapped_column(
        sqltypes.VARCHAR(255),
        sqla.ForeignKey("user_account.id"),
    )
    parent_comment: orm.Mapped[str | None] = orm.mapped_column(
        sqla.ForeignKey("post_comment.id")
    )
    comment: orm.Mapped[str] = orm.mapped_column(
        sqltypes.VARCHAR(255),
    )
    status: orm.Mapped[CommentStatus] = orm.mapped_column(
        default=CommentStatus.NORMAL,
    )
    comment_type: orm.Mapped[CommentType]


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


class Bookmark(Base):
    __tablename__: str = "bookmark"
    account_id: orm.Mapped[UserAccount] = orm.mapped_column(
        sqla.ForeignKey(UserAccount.id),
        primary_key=True,
    )
    blog_id: orm.Mapped[Blog] = orm.mapped_column(
        sqla.ForeignKey(Blog.id),
        primary_key=True,
    )
