from datetime import datetime
from enum import Enum
from db.postgresql.models import Base
from sqlalchemy.dialects import postgresql as psql
from sqlalchemy import orm
import sqlalchemy as sqla

from db.postgresql.models.user_account import UserAccount


class Sender(str, Enum):
    CUSTOMER = "CUSTOMER"
    STAFF = "STAFF"


class ChatHistory(Base):
    __tablename__ = "chat_history"
    user_id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey(UserAccount.id),
        primary_key=True,
    )
    timestamp: orm.Mapped[datetime] = orm.mapped_column(
        psql.TIMESTAMP,
        primary_key=True,
    )
    msg: orm.Mapped[str] = orm.mapped_column(psql.TEXT)
    sender: orm.Mapped[Sender]
    user: orm.Mapped[UserAccount] = orm.relationship(back_populates="chatlog")
