import pytest
import pytest_asyncio
from datetime import date

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select  

from services.account import create_account
from dtos.request.account import AccountCreateDto, AccountInfoForm
from db.postgresql.models.staff_account import AccountType, AccountStatus, StaffAccount
from db.postgresql.models import Base
from db.postgresql.models.shipper import ShipperAvailbility
from sqlalchemy.exc import IntegrityError
from etc.local_error import HandledError

from .set_up.test_account_data import *
from unittest.mock import AsyncMock, patch
# Test database URL
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

engine = create_async_engine(DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="function", autouse=True)
async def create_test_db():
    async with engine.begin() as conn:
        # Enable pgvector extension if not already
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Drop all public tables
        await conn.execute(text("""
            DO $$ 
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END 
            $$;
        """))

        # Create tables
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

# Provide DB session for tests
@pytest_asyncio.fixture()
async def db_session():
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


#-----------------------------------------------------------

@pytest.mark.asyncio
async def test_create_account_success_with_db(db_session):
    account_dto = ex_account_dto_1()

    # ✅ Create account and get the token
    token = await create_account(account_dto, db_session)

    # Query the database to retrieve the account by token
    account = await db_session.execute(
        select(StaffAccount).filter(StaffAccount.token == token)  # Use 'select' from sqlalchemy
    )
    account = account.scalar_one_or_none()  # Fetch the first result or None if no match

    # Assert the account details
    assert account is not None  # Ensure the account exists in the database
    assert account.username == "testuser1"
    assert account.type == AccountType.STAFF  # 🧐 double-check if you meant STAFF or ADMIN

@pytest.mark.asyncio
async def test_create_account_success_shipper(db_session):
    account_dto = ex_account_dto_2_shipper()

    # ✅ Create account and get the token
    token = await create_account(account_dto, db_session)

    # Query the database to retrieve the account by token
    account = await db_session.execute(
        select(StaffAccount).filter(StaffAccount.token == token)  # Use 'select' from sqlalchemy
    )
    account = account.scalar_one_or_none()  # Fetch the first result or None if no match

    # Assert the account details
    assert account is not None  # Ensure the account exists in the database
    assert account.username == "testuser1"
    assert account.type == AccountType.SHIPPER  # 🧐 double-check if you meant STAFF or ADMIN
    
    shipper_result = await db_session.execute(
        select(ShipperAvailbility).filter(ShipperAvailbility.id == account.id)
    )
    shipper_availability = shipper_result.scalar_one_or_none()

    # ✅ Assert that the ShipperAvailbility entry exists
    assert shipper_availability is not None

@pytest.mark.asyncio
async def test_create_account_shipper_missing_acc_id(db_session):
    account_dto = ex_account_dto_2_shipper()

    with patch.object(db_session, "scalar", AsyncMock(return_value=None)):
        with pytest.raises(HandledError) as exc_info:
            await create_account(account_dto, db_session)

        assert "Cannot find account after created" in str(exc_info.value)

@pytest.mark.asyncio
async def test_create_account_already_exists(db_session):
    # First, create the account
    account_dto = ex_account_dto_1()
    
    # Create the account the first time, it should succeed
    await create_account(account_dto, db_session)
    
    # Try to create the same account again, should raise HandledError
    with pytest.raises(HandledError, match="duplicate key value violates unique constraint"):
        await create_account(account_dto, db_session)


@pytest.mark.asyncio
async def test_create_account_null_input(db_session):
    # Prepare DTO with NULL value
    account_dto = ex_account_dto_1_null01()

    try:
        # Attempt to create account with NULL 'username'
        await create_account(account_dto, db_session)
    except HandledError as e:
        print(f"Error raised: {str(e)}")  # Log the error message to help debugging
        # Adjust the regex to match the relevant part of the error message
        assert 'null value in column' in str(e)

@pytest.mark.asyncio
async def test_create_account_null_input_password(db_session):
    # Prepare DTO with NULL value
    account_dto = ex_account_dto_1_null02()

    try:
        # Attempt to create account with NULL 'username'
        await create_account(account_dto, db_session)
    except TypeError as e:
        print(f"Error raised: {str(e)}")  # Log the error message to help debugging
        # Adjust the regex to match the relevant part of the error message
        assert 'secret must be unicode or bytes, not None' in str(e)



