from enum import Enum
from uuid import UUID, uuid4

import sqlalchemy as sqla
from sqlalchemy import orm
from sqlalchemy.dialects.postgresql import ARRAY, VARCHAR

from db.models import Base
from db.models.product import Product


class UserAccountStatus(Enum):
    NON_ACTIVE = 1
    NORMAL = 2
    BANNED = 3
    DEACTIVATE = 4


class UserAccount(Base):
    __tablename__: str = "user_account"
    id: orm.Mapped[UUID] = orm.mapped_column(primary_key=True, default=uuid4)
    email: orm.Mapped[str] = orm.mapped_column(unique=True)
    username: orm.Mapped[str] = orm.mapped_column(unique=True)
    password: orm.Mapped[str]
    address: orm.Mapped[str]
    phone: orm.Mapped[str]
    profile_pic_uri: orm.Mapped[str]
    profile_description: orm.Mapped[str]
    token: orm.Mapped[str]
    bookmarked_posts: orm.Mapped[list[str]] = orm.mapped_column(ARRAY(VARCHAR(255)))


class UserCart(Base):
    __tablename__: str = "cart"
    amount: orm.Mapped[int]
    account_id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey("user_account.id"), primary_key=True
    )
    product_id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey("product.id"), primary_key=True
    )
