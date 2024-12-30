from datetime import datetime

import sqlalchemy as sqla
from sqlalchemy import orm
from sqlalchemy.sql import sqltypes

from db.postgresql.models import Base
from db.postgresql.models.order_history import PaymentStatus, OrderHistory


class PaymentTransaction(Base):
    __tablename__: str = "payment_transaction"
    order_id: orm.Mapped[OrderHistory] = orm.mapped_column(
        sqla.ForeignKey("order_history.id"), primary_key=True
    )
    create_time: orm.Mapped[datetime] = orm.mapped_column(sqltypes.TIMESTAMP)
    payment_id: orm.Mapped[str | None] = orm.mapped_column(sqltypes.VARCHAR(255))
    refund_id: orm.Mapped[str | None] = orm.mapped_column(sqltypes.VARCHAR(255))
    transaction_id: orm.Mapped[str | None] = orm.mapped_column(sqltypes.VARCHAR(255))
    status: orm.Mapped[PaymentStatus]
    amount: orm.Mapped[float] = orm.mapped_column(sqltypes.REAL)
