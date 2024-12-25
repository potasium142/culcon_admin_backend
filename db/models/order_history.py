from ast import For
from datetime import datetime, date
from enum import Enum

from sqlalchemy import Column, ForeignKey, Table, orm
from sqlalchemy.sql import sqltypes

from db.models import Base
from db.models.product import Product, ProductPriceHistory


class OrderStatus(Enum):
    ON_CONFIRM = 1
    ON_PROCESSING = 2
    ON_SHIPPING = 3
    SHIPPED = 4
    CANCELLED = 5


class Coupon(Base):
    __tablename__: str = "coupon"
    id: orm.Mapped[str] = orm.mapped_column(primary_key=True)
    expire_time: orm.Mapped[date] = orm.mapped_column(sqltypes.DATE)
    sale_percent: orm.Mapped[float] = orm.mapped_column(sqltypes.REAL)
    usage_amount: orm.Mapped[int] = orm.mapped_column(sqltypes.INTEGER)
    usage_left: orm.Mapped[int] = orm.mapped_column(sqltypes.INTEGER)


# class OrderHistoryItems(Base):
#     __tablename__: str = "order_history_items"
#     order_history_id: orm.Mapped[int] = orm.mapped_column(
#         ForeignKey("order_history.id"), primary_key=True
#     )
#     product_id: orm.Mapped[str] = orm.mapped_column(
#         ForeignKey("product_price_history.product_id"), primary_key=True
#     )
#     date: orm.Mapped[datetime] = orm.mapped_column(
#         ForeignKey("product_price_history.date"), primary_key=True
#     )
#     quantity: orm.Mapped[int] = orm.mapped_column(sqltypes.INTEGER)


OrderHistoryItems = Table(
    "order_history_items",
    Base.metadata,
    Column("order_history_id", ForeignKey("order_history.id"), primary_key=True),
    Column(
        "product_id", ForeignKey("product_price_history.product_id"), primary_key=True
    ),
    Column("date", ForeignKey("product_price_history.date")),
    Column("quantity", sqltypes.INTEGER),
)


class OrderHistory(Base):
    __tablename__: str = "order_history"
    id: orm.Mapped[int] = orm.mapped_column(sqltypes.BIGINT, primary_key=True)
    order_date: orm.Mapped[datetime] = orm.mapped_column(sqltypes.TIMESTAMP)
    delivery_address: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(255))
    note: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(255))
    total_price: orm.Mapped[float] = orm.mapped_column(sqltypes.REAL)
    receiver: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(255))
    phonenumber: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(12))
    updated_coupon: orm.Mapped[bool]
    updated_payment: orm.Mapped[bool]
    order_history_items: orm.Mapped[list[Product]] = orm.relationship(
        secondary=OrderHistoryItems
    )
