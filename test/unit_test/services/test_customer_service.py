import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from db.postgresql.models.user_account import UserAccount, UserAccountStatus, PostComment
from etc.local_error import HandledError
from db.postgresql.db_session import db_session
from services.customer import *
from auth import encryption
from db.postgresql.models.order_history import OrderHistory
from db.postgresql.models.user_account import (
    Cart,
    UserAccount,
    UserAccountStatus,
)
from dtos.request.user_account import EditCustomerAccount, EditCustomerInfo

from etc.local_error import HandledError
from db.postgresql.paging import display_page, paging, Page, table_size
import sqlalchemy as sqla

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from db.postgresql.models import Base

from sqlalchemy.exc import NoResultFound 

from .set_up.test_user_account_data import *
from .set_up.test_account_data import *


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
async def test_set_account_status_success(db_session):
    # Arrange: Create a dummy user account
    user = preb_user_account_1()

    db_session.add(user)
    await db_session.commit()

    # Act: Change the user status
    new_status = UserAccountStatus.BANNED
    result = await set_account_status(user.id, new_status, db_session)

    # Assert
    assert result["id"] == user.id
    assert result["status"] == new_status

    # Fetch again from DB to be sure
    updated_user = await db_session.get(UserAccount, user.id)
    assert updated_user.status == new_status

def test_set_account_status_not_found():
    with patch.object(db_session.session, "get", return_value=None):
        with pytest.raises(HandledError, match="Customer account not found"):
            set_account_status("invalid_user_id", UserAccountStatus.DEACTIVATE)

@pytest.mark.asyncio
async def test_set_account_status_fail_account_not_found(db_session):
    # Arrange: Create a dummy user account
    user = preb_user_account_1()


    # Act: Change the user status
    new_status = UserAccountStatus.BANNED
    with pytest.raises(NoResultFound):
        await set_account_status(user.id, new_status, db_session)


@pytest.mark.asyncio
async def test_get_customer_success():
    # Arrange
    mock_user = MagicMock(spec=UserAccount)
    mock_user.id = "user-id"
    mock_user.email = "test@example.com"
    mock_user.username = "testuser"
    mock_user.profile_name = "Test User"
    mock_user.address = "123 Test St"
    mock_user.phone = "1234567890"
    mock_user.profile_pic_uri = "http://example.com/profile.jpg"

    mock_session = MagicMock()
    mock_session.get_one = AsyncMock(return_value=mock_user)
    
    # Patch the context manager behavior
    mock_context = MagicMock()
    mock_context.__aenter__.return_value = mock_session
    mock_context.__aexit__.return_value = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = AsyncMock()
    
    # Act
    result = await get_customer("user-id", mock_session)

    # Assert
    expected_result = {
        "id": "user-id",
        "email": "test@example.com",
        "username": "testuser",
        "profile_name": "Test User",
        "address": "123 Test St",
        "phone": "1234567890",
        "profile_pic": "http://example.com/profile.jpg",
    }
    assert result == expected_result


@pytest.mark.asyncio
async def test_get_customer_not_found():
    # Arrange
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)  # Mock the context manager entry
    mock_session.__aexit__ = AsyncMock(return_value=False)  # Mock the context manager exit
    
    # Simulate `session.get_one()` returning None
    mock_session.get_one = AsyncMock(return_value=None)
    
    # Act & Assert
    with pytest.raises(AttributeError):  # The exception that will be raised due to accessing attributes of `None`
        await get_customer("nonexistent-id", mock_session)



@pytest.mark.asyncio
async def test_edit_customer_info_success():
    # Arrange
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)  # Mock the context manager entry
    mock_session.__aexit__ = AsyncMock(return_value=False)  # Mock the context manager exit
    
    # Creating a mock UserAccount object for the customer
    mock_customer = MagicMock(spec=UserAccount)
    mock_customer.id = "existing-id"
    mock_customer.email = "old_email@example.com"
    mock_customer.address = "Old Address"
    mock_customer.phone = "123456789"
    mock_customer.profile_description = "Old Description"
    mock_customer.profile_name = "Old Name"
    
    # Set the mock session to return the mock customer when `get_one` is called
    mock_session.get_one = AsyncMock(return_value=mock_customer)
    
    # Mock the `flush` method to be an AsyncMock (to be awaited)
    mock_session.flush = AsyncMock()

    # Define the info to update with a valid phone number
    info = EditCustomerInfo(
        email="new_email@example.com",
        address="New Address",
        phone="0123456789",  # Updated to match the expected phone pattern
        profile_description="New Description",
        profile_name="New Name"
    )

    # Act
    updated_info = await edit_customer_info("existing-id", info, mock_session)

    # Assert
    assert updated_info["email"] == "new_email@example.com"
    assert updated_info["address"] == "New Address"
    assert updated_info["phone"] == "0123456789"
    assert updated_info["profile_description"] == "New Description"
    assert updated_info["profile_name"] == "New Name"
    mock_session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_edit_customer_info_account_not_found():
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.get_one = AsyncMock(return_value=None)  # Simulate not found

    info = EditCustomerInfo(
        email="new_email@example.com",
        address="New Address",
        phone="0123456789",
        profile_description="New Description",
        profile_name="New Name"
    )

    with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'email'"):
        await edit_customer_info("nonexistent-id", info, mock_session)

@pytest.mark.asyncio
async def test_edit_customer_account_success():
    
    # Arrange
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    # Mock the flush method to behave like an async function
    mock_session.flush = AsyncMock()

    mock_user = MagicMock(spec=UserAccount)
    mock_user.id = "user-123"
    mock_user.username = "olduser"
    mock_user.password = "oldhash"

    new_username = "newuser"
    new_password = "newpassword"
    hashed = "hashedpassword123"

    info = EditCustomerAccount(username=new_username, password=new_password)

    # Patch encryption.hash to return a fake hashed password
    with patch("auth.encryption.hash", return_value=hashed):
        # Mock session.get_one to return the mock_user for both calls
        mock_session.get_one = AsyncMock(side_effect=[mock_user, mock_user])

        # Act
        result = await edit_customer_account("user-123", info, mock_session)

# @pytest.mark.asyncio
# async def test_edit_customer_account_user_not_found():
#     # Arrange
#     mock_session = MagicMock()
#     mock_session.__aenter__ = AsyncMock(return_value=mock_session)
#     mock_session.__aexit__ = AsyncMock(return_value=False)
    
#     # Mock the flush method to behave like an async function
#     mock_session.flush = AsyncMock()
    
#     # Simulate the case where the user is not found (None is returned by get_one)
#     mock_session.get_one = AsyncMock(return_value=None)
    
#     new_username = "newuser"
#     new_password = "newpassword"
#     info = EditCustomerAccount(username=new_username, password=new_password)
    
#     # Act & Assert: Ensure that when user is not found, an exception is raised
#     try:
#         await edit_customer_account("nonexistent-user-id", info, mock_session)
#     except AttributeError:  # Catch the AttributeError due to 'NoneType'
#         raise ValueError("User not found")  # Raise ValueError instead

# @pytest.fixture
# def mock_comment():
#     """Fixture to create a mock comment object"""
#     mock_comment = MagicMock(spec=PostComment)
#     mock_comment.deleted = False  # Simulate an existing, active comment
#     return mock_comment


# def test_delete_comment_success(mock_comment):
#     """Test deleting a comment successfully marks it as deleted"""
#     with patch.object(db_session.session, "get", return_value=mock_comment) as mock_get, \
#          patch.object(db_session, "commit") as mock_commit:

#         delete_comment("user_123", "comment_456")

#         mock_get.assert_called_once_with(PostComment, {"account_id": "user_123", "id": "comment_456"})
#         assert mock_comment.deleted is True
#         mock_commit.assert_called_once()


# def test_delete_comment_not_found():
#     """Test raising an error when comment does not exist"""
#     with patch.object(db_session.session, "get", return_value=None):
#         with pytest.raises(HandledError, match="Comment not found"):
#             delete_comment("user_123", "comment_456")
