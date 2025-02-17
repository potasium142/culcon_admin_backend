from db.postgresql.models import Base
from sqlalchemy.dialects import postgresql as psql
from sqlalchemy import orm
import sqlalchemy as sqla

from db.postgresql.models.user_account import UserAccount


class ChatHistory(Base):
    __tablename__ = "chat_history"
    id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey(UserAccount.id),
        primary_key=True,
    )
    chatlog: orm.Mapped[dict[str, str]] = orm.mapped_column(
        psql.JSONB(),
    )
