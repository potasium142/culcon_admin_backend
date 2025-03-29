from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase

__all__ = [
    "product",
    "staff_account",
    "user_account",
    "order_history",
    "transaction",
    "blog",
    "chat",
]
# Base = declarative_base()


class Base(AsyncAttrs, DeclarativeBase):
    pass
