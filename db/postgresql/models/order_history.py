from datetime import datetime, date
from enum import Enum
from uuid import uuid4

from sqlalchemy import ForeignKey, orm
from sqlalchemy.sql import sqltypes

from db.postgresql.models import Base
from db.postgresql.models.product import ProductPriceHistory
from db.postgresql.models.staff_account import StaffAccount
from db.postgresql.models.user_account import UserAccount

import sqlalchemy as sqla


class OrderStatus(str, Enum):
    ON_CONFIRM = "ON_CONFIRM"
    ON_PROCESSING = "ON_PROCESSING"
    ON_SHIPPING = "ON_SHIPPING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, Enum):
    PAYPAL = "PAYPAL"
    VNPAY = "VNPAY"
    COD = "COD"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    RECEIVED = "RECEIVED"
    REFUNDED = "REFUNDED"


class Coupon(Base):
    __tablename__: str = "coupon"
    id: orm.Mapped[str] = orm.mapped_column(primary_key=True)
    expire_time: orm.Mapped[date] = orm.mapped_column(sqltypes.DATE)
    sale_percent: orm.Mapped[float] = orm.mapped_column(sqltypes.REAL)
    usage_amount: orm.Mapped[int] = orm.mapped_column(sqltypes.INTEGER)
    usage_left: orm.Mapped[int] = orm.mapped_column(sqltypes.INTEGER)
    minimum_price: orm.Mapped[float] = orm.mapped_column(sqltypes.REAL)
    orders: orm.Mapped[list["OrderHistory"]] = orm.relationship(
        back_populates="coupon_detail",
    )


class OrderHistoryItems(Base):
    __tablename__: str = "order_history_items"
    order_history_id: orm.Mapped[str] = orm.mapped_column(
        ForeignKey("order_history.id"),
        primary_key=True,
    )
    product_id: orm.Mapped[str] = orm.mapped_column(
        primary_key=True,
    )
    date: orm.Mapped[datetime] = orm.mapped_column(
        primary_key=True,
    )
    quantity: orm.Mapped[int] = orm.mapped_column(sqltypes.INTEGER)
    __table_args__ = (
        sqla.ForeignKeyConstraint(
            ["date", "product_id"],
            ["product_price_history.date", "product_price_history.product_id"],
        ),
    )

    item: orm.Mapped[ProductPriceHistory] = orm.relationship(back_populates="orders")


class OrderHistory(Base):
    __tablename__: str = "order_history"
    id: orm.Mapped[str] = orm.mapped_column(
        sqltypes.VARCHAR(255), primary_key=True, default=uuid4
    )
    user_id: orm.Mapped[str] = orm.mapped_column(ForeignKey("user_account.id"))
    order_date: orm.Mapped[datetime] = orm.mapped_column(sqltypes.TIMESTAMP)
    delivery_address: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(255))
    note: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(255))
    total_price: orm.Mapped[float] = orm.mapped_column(sqltypes.REAL)
    receiver: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(255))
    phonenumber: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(255))
    coupon: orm.Mapped[Coupon | None] = orm.mapped_column(
        ForeignKey(Coupon.id),
    )
    payment_method: orm.Mapped[PaymentMethod]
    payment_status: orm.Mapped[PaymentStatus]
    order_status: orm.Mapped[OrderStatus]
    order_history_items: orm.Mapped[list[OrderHistoryItems]] = orm.relationship()
    user: orm.Mapped[UserAccount] = orm.relationship(back_populates="order_history")

    coupon_detail: orm.Mapped[Coupon | None] = orm.relationship(back_populates="orders")

    process: orm.Mapped["OrderProcess"] = orm.relationship(back_populates="order")


class ShippingStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    ON_SHIPPING = "ON_SHIPPING"
    DELIVERED = "DELIVERED"
    ASSIGN = "ASSIGN"


class OrderProcess(Base):
    __tablename__ = "order_process"
    order_id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey(OrderHistory.id),
        primary_key=True,
    )
    confirm_date: orm.Mapped[datetime] = orm.mapped_column(
        sqltypes.TIMESTAMP,
    )
    process_by: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey(StaffAccount.id),
    )
    shipping_date: orm.Mapped[datetime | None] = orm.mapped_column(
        sqltypes.TIMESTAMP, default=None
    )
    deliver_by: orm.Mapped[str | None] = orm.mapped_column(
        sqla.ForeignKey(StaffAccount.id), default=None
    )
    status: orm.Mapped[ShippingStatus | None] = orm.mapped_column(default=None)
    order: orm.Mapped[OrderHistory] = orm.relationship(back_populates="process")
