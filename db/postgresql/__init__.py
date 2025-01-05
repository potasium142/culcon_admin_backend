import sqlalchemy as sqla
import sqlalchemy_utils as sqlau
from pgvector.psycopg import register_vector
from sqlalchemy import event, text
from config import env
from db.postgresql.models import Base

URL_DATABASE = env.DB_URL

engine = sqla.create_engine(URL_DATABASE)
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
