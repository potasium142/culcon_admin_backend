from db.postgresql.models import Base
from sqlalchemy.dialects import postgresql as psql
from sqlalchemy import orm


class ChatHistory(Base):
    __tablename__ = "chat_history"
    id: orm.Mapped[str] = orm.mapped_column(
        psql.VARCHAR(255),
        primary_key=True,
    )
    chatlog: orm.Mapped[dict[str, str]] = orm.mapped_column(
        psql.JSONB(),
    )
