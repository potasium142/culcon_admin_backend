# conftest.py  Stupide code dosnt work when split, i give up
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from db.postgresql.models.staff_account import StaffAccount  # Import the model directly
from db.postgresql.models import Base

DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
engine = create_async_engine(DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def create_test_db():
    # Directly import all the models you need
    from db.postgresql.models.staff_account import StaffAccount
    # Import other models as needed

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Drop all public tables
        await conn.execute(
            text("""
            DO $$ 
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END 
            $$;
        """)
        )

        # Log the models that are being registered
        print("Registered models:", Base.metadata.tables.keys())

        # Create tables
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture()
async def db_session():
    async with TestingSessionLocal() as session:
        # Start a SAVEPOINT for rollback even if the session is closed by service
        async with session.begin():
            await session.begin_nested()

        yield session

        # The session may be closed after service runs, so we reopen a new one to clean up if needed
        if session.is_active:
            await session.rollback()
