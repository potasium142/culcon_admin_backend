import sqlalchemy as sqla
import sqlalchemy_utils as sqlau
from pgvector.psycopg import register_vector
from sqlalchemy import event, text
from config import env
from db.postgresql.models import Base

## DO NOT DELETE THIS LINE
from db.postgresql.models import *  # noqa: F403


engine = sqla.create_engine(
    sqla.URL.create(
        host=env.DB_URL,
        drivername=env.DB_DRIVER,
        username=env.DB_USERNAME,
        password=env.DB_PASSWORD,
        port=env.DB_PORT,
        database=env.DB_NAME,
    ),
    pool_pre_ping=True,
)

if not sqlau.database_exists(engine.url):
    sqlau.create_database(engine.url)

with engine.connect() as connection:
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    connection.commit()

DBSession: sqla.orm.Session = sqla.orm.sessionmaker(engine)


@event.listens_for(engine, "connect")
def connect(dbapi_connection, _):
    register_vector(dbapi_connection)


Base.metadata.create_all(engine)
