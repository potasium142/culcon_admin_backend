from db.postgresql.models import Base
from sqlalchemy.dialects import postgresql as psql
from sqlalchemy import orm
import sqlalchemy as sqla

from db.postgresql.models.user_account import UserAccount


class ChatSession(Base):
    __tablename__ = "chat_session"
    id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey(UserAccount.id),
        primary_key=True,
    )
    chatlog: orm.Mapped[list[dict[str, str]]] = orm.mapped_column(
        psql.JSONB(),
    )
    connected: orm.Mapped[bool] = orm.mapped_column(
        psql.BOOLEAN,
        default=False,
    )
    user: orm.Mapped[UserAccount] = orm.relationship(back_populates="chatlog")
