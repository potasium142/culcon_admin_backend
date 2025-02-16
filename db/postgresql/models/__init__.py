from sqlalchemy.ext.declarative import declarative_base

__all__ = [
    "product",
    "staff_account",
    "user_account",
    "order_history",
    "transaction",
    "blog",
    "chat",
]
Base = declarative_base()
