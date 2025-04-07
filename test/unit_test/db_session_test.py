# import os
# from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# DATABASE_URL = f"postgresql+asyncpg://postgres:postgres@localhost:{os.getenv('DB_PORT', '5432')}/postgres"

# engine = create_async_engine(DATABASE_URL, echo=True)  # echo=True helps debugging
# async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
