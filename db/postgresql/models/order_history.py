from datetime import datetime, date
from enum import Enum

from sqlalchemy import Column, ForeignKey, Table, orm, ForeignKeyConstraint
from sqlalchemy.sql import sqltypes

from db.postgresql.models import Base
from db.postgresql.models.product import Product, ProductPriceHistory


class OrderStatus(Enum):
    ON_CONFIRM = 1
    ON_PROCESSING = 2
    ON_SHIPPING = 3
    SHIPPED = 4
    CANCELLED = 5


class PaymentMethod(Enum):
    BANKING = 1
    COD = 2


class PaymentStatus(Enum):
    PENDING = 1
    RECEIVED = 2
    REFUNDED = 3
    REFUNDING = 4
    CREATED = 5
    CHANGED = 6


class Coupon(Base):
    __tablename__: str = "coupon"
    id: orm.Mapped[str] = orm.mapped_column(primary_key=True)
    expire_time: orm.Mapped[date] = orm.mapped_column(sqltypes.DATE)
    sale_percent: orm.Mapped[float] = orm.mapped_column(sqltypes.REAL)
    usage_amount: orm.Mapped[int] = orm.mapped_column(sqltypes.INTEGER)
    usage_left: orm.Mapped[int] = orm.mapped_column(sqltypes.INTEGER)


OrderHistoryItems = Table(
    "order_history_items",
    Base.metadata,
    Column("order_history_id", ForeignKey("order_history.id")),
    Column("product_id_product_id"),
    Column("product_id_date"),
    Column("quantity", sqltypes.INTEGER),
    ForeignKeyConstraint(
        ["product_id_date", "product_id_product_id"],
        ["product_price_history.date", "product_price_history.product_id"],
    ),
)


class OrderHistory(Base):
    __tablename__: str = "order_history"
    id: orm.Mapped[int] = orm.mapped_column(sqltypes.BIGINT, primary_key=True)
    user_id: orm.Mapped[str] = orm.mapped_column(ForeignKey("user_account.id"))
    order_date: orm.Mapped[datetime] = orm.mapped_column(sqltypes.TIMESTAMP)
    delivery_address: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(255))
    note: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(255))
    total_price: orm.Mapped[float] = orm.mapped_column(sqltypes.REAL)
    receiver: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(255))
    phonenumber: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(12))
    coupon: orm.Mapped[Coupon | None] = orm.mapped_column(ForeignKey("coupon.id"))
    updated_coupon: orm.Mapped[bool]
    updated_payment: orm.Mapped[bool]
    payment_method: orm.Mapped[PaymentMethod]
    payment_status: orm.Mapped[PaymentStatus]
    order_status: orm.Mapped[OrderStatus]
    order_history_items: orm.Mapped[list[ProductPriceHistory]] = orm.relationship(
        secondary=OrderHistoryItems
    )
