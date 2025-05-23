from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

__all__ = [
    "product",
    "staff_account",
    "user_account",
    "order_history",
    "transaction",
    "blog",
    "chat",
    "shipper",
]
# Base = declarative_base()


class Base(AsyncAttrs, DeclarativeBase):
    pass
