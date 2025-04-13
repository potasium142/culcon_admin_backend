import asyncio
import sqlalchemy as sqla
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
import sqlalchemy_utils as sqlau
from pgvector.psycopg import register_vector_async
from sqlalchemy import event, text
from config import env
from db.postgresql.models import Base

## DO NOT DELETE THIS LINE
from db.postgresql.models import *  # noqa: F403


engine = create_async_engine(
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


async def init_db():
    if not sqlau.database_exists(engine.url):
        sqlau.create_database(engine.url)

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()


# @event.listens_for(engine.sync_engine, "connect")
# def connect(dbapi_connection, _):
#     dbapi_connection.run_async(register_vector_async)


# async def session():
#     with async_sessionmaker(engine) as ss:
#         yield ss


DBSession = async_sessionmaker(engine)
