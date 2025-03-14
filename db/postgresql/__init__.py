import sqlalchemy as sqla
from sqlalchemy.orm import query
import sqlalchemy_utils as sqlau
from sqlalchemy import text
from config import env
import os
from db.postgresql.models import Base

## DO NOT DELETE THIS LINE
from db.postgresql.models import *  # noqa: F403

unix_socket_path: str | None = os.getenv("INSTANCE_UNIX_SOCKET")

if unix_socket_path:
    query = {"unix_sock": f"{unix_socket_path}/.s.PGSQL.5432"}
else:
    query = {}

engine = sqla.create_engine(
    sqla.URL.create(
        host=env.DB_URL,
        drivername=env.DB_DRIVER,
        username=env.DB_USERNAME,
        password=env.DB_PASSWORD,
        port=env.DB_PORT,
        database=env.DB_NAME,
        query=query,
    )
)

if not sqlau.database_exists(engine.url):
    sqlau.create_database(engine.url)

with engine.connect() as connection:
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    connection.commit()

DBSession: sqla.orm.Session = sqla.orm.sessionmaker(engine)


# @event.listens_for(engine, "connect")
# def connect(dbapi_connection, _):
#     register_vector(dbapi_connection)


Base.metadata.create_all(engine)
