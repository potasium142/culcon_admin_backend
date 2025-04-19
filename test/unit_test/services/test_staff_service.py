import pytest
from unittest.mock import  MagicMock, AsyncMock, patch, Mock
from db.postgresql.db_session import db_session
from db.postgresql.models.staff_account import *
from etc.local_error import HandledError
from db.postgresql.paging import Page
from services.staff import * 

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from db.postgresql.models import Base

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

@pytest.fixture
def mock_staff_list():
    """Fixture to create a mock list of StaffAccount objects"""
    staff1 = MagicMock(spec=StaffAccount, id="staff_001", username="staff1", type=AccountType.STAFF, status="ACTIVE")
    staff2 = MagicMock(spec=StaffAccount, id="staff_002", username="staff2", type=AccountType.STAFF, status="INACTIVE")
    return [staff1, staff2]


def test_get_all_staff_success(mock_staff_list):
    """Test fetching all staff accounts successfully"""
    with patch.object(db_session.session, "scalars", return_value=mock_staff_list) as mock_scalars:
        pg = Page(limit=10, offset=0)  # Example paging params
        result = get_all_staff(pg)

        expected_output = [
            {"id": "staff_001", "username": "staff1", "type": "STAFF", "status": "ACTIVE"},
            {"id": "staff_002", "username": "staff2", "type": "STAFF", "status": "INACTIVE"},
        ]

        assert result == expected_output
        mock_scalars.assert_called_once()


def test_get_all_staff_empty():
    """Test handling case where no staff accounts exist"""
    with patch.object(db_session.session, "scalars", return_value=[]) as mock_scalars:
        pg = Page(limit=10, offset=0)
        result = get_all_staff(pg)

        assert result == []  # Should return an empty list
        mock_scalars.assert_called_once()



@pytest.fixture
def mock_staff():
    """Fixture to create a mock StaffAccount object with EmployeeInfo"""
    mock_employee = MagicMock(
        spec=EmployeeInfo,
        ssn="123-45-6789",
        phonenumber="555-1234",
        realname="John Doe",
        email="johndoe@example.com",
        dob="1990-01-01",
    )

    mock_staff = MagicMock(
        spec=StaffAccount,
        id="staff_001",
        username="staffuser",
        type=AccountType.STAFF,
        status="ACTIVE",
        employee_info=mock_employee,
    )

    return mock_staff


def test_get_staff_profile_success(mock_staff):
    """Test successfully retrieving a staff profile"""
    with patch.object(db_session.session, "get", return_value=mock_staff) as mock_get:
        result = get_staff_profile("staff_001")

        expected_output = {
            "id": "staff_001",
            "username": "staffuser",
            "type": "STAFF",
            "status": "ACTIVE",
            "ssn": "123-45-6789",
            "phonenumber": "555-1234",
            "realname": "John Doe",
            "email": "johndoe@example.com",
            "dob": "1990-01-01",
        }

        assert result == expected_output
        mock_get.assert_called_once_with(StaffAccount, "staff_001")


def test_get_staff_profile_not_found():
    """Test handling case where the staff account doesn't exist"""
    with patch.object(db_session.session, "get", return_value=None) as mock_get:
        with pytest.raises(HandledError, match="Staff not found"):
            get_staff_profile("invalid_id")

        mock_get.assert_called_once_with(StaffAccount, "invalid_id")


@pytest.mark.asyncio
async def test_edit_staff_account_success():
    # Arrange
    staff_id = str(uuid4())
    mock_info = MagicMock(spec=EditStaffAccount)
    mock_info.username = "updated_username"
    mock_info.password = "new_password"

    mock_ss = MagicMock()
    mock_staff = MagicMock(spec=StaffAccount)

    mock_ss.get = AsyncMock(return_value=mock_staff)
    mock_ss.commit = AsyncMock()

    # Create an async context manager for ss.begin
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = None
    mock_context_manager.__aexit__.return_value = None
    mock_ss.begin.return_value = mock_context_manager

    hashed_password = "hashed_new_password"

    with patch("services.staff.encryption.hash", return_value=hashed_password), \
         patch("services.staff.get_staff_profile", new_callable=AsyncMock) as mock_get_profile:

        mock_get_profile.return_value = {"id": staff_id, "username": mock_info.username}

        # Act
        result = await edit_staff_account(staff_id, mock_info, mock_ss)

        # Assert
        mock_ss.get.assert_awaited_once()
        assert mock_staff.password == hashed_password
        assert mock_staff.username == mock_info.username
        mock_ss.commit.assert_awaited_once()
        mock_get_profile.assert_awaited_once_with(staff_id, mock_ss)

        assert result == {"id": staff_id, "username": mock_info.username}

@pytest.mark.asyncio
async def test_edit_staff_account_invalid_uuid():
    # Arrange
    invalid_uuid = "not-a-valid-uuid"
    mock_info = MagicMock(spec=EditStaffAccount)
    mock_ss = MagicMock()

    # Act & Assert
    with pytest.raises(HandledError) as exc_info:
        await edit_staff_account(invalid_uuid, mock_info, mock_ss)

    assert str(exc_info.value) == "UUID invalid"



@pytest.mark.asyncio
async def test_edit_employee_info_success():
    # Arrange
    staff_id = str(uuid4())
    mock_info = MagicMock(spec=EditEmployeeInfo)
    mock_info.ssn = "123-45-6789"
    mock_info.email = "test@example.com"
    mock_info.phonenumber = "1234567890"
    mock_info.dob = "2000-01-01"
    mock_info.realname = "John Doe"

    mock_staff = MagicMock(spec=EmployeeInfo)
    mock_ss = MagicMock()
    mock_ss.get = AsyncMock(return_value=mock_staff)

    # Setup async context manager
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = None
    mock_context.__aexit__.return_value = None
    mock_ss.begin.return_value = mock_context

    mock_ss.commit = AsyncMock()

    with patch("services.staff.get_staff_profile", new_callable=AsyncMock) as mock_get_profile:
        mock_get_profile.return_value = {"id": staff_id, "realname": mock_info.realname}

        # Act
        result = await edit_employee_info(mock_info, staff_id, mock_ss)

        # Assert
        mock_ss.get.assert_awaited_once()
        assert mock_staff.realname == mock_info.realname
        assert mock_staff.email == mock_info.email
        assert mock_staff.ssn == mock_info.ssn
        assert result == {"id": staff_id, "realname": mock_info.realname}

@pytest.mark.asyncio
async def test_edit_employee_info_staff_not_found():
    # Arrange
    staff_id = str(uuid4())
    mock_info = MagicMock(spec=EditEmployeeInfo)

    mock_ss = MagicMock()
    mock_ss.get = AsyncMock(return_value=None)

    # Setup async context manager
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = None
    mock_context.__aexit__.return_value = None
    mock_ss.begin.return_value = mock_context

    # Act & Assert
    with pytest.raises(HandledError) as exc_info:
        await edit_employee_info(mock_info, staff_id, mock_ss)

    assert str(exc_info.value) == "Staff account not found"

@pytest.mark.asyncio
async def test_set_staff_status_success():
    staff_id = str(uuid4())
    mock_status = AccountStatus.DISABLE  # ✅ Use correct enum member

    mock_ss = MagicMock()
    mock_staff = MagicMock()
    mock_ss.get = AsyncMock(return_value=mock_staff)

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = None
    mock_cm.__aexit__.return_value = None
    mock_ss.begin.return_value = mock_cm

    mock_ss.commit = AsyncMock()

    with patch("services.staff.get_staff_profile", new_callable=AsyncMock) as mock_get_profile:
        mock_get_profile.return_value = {"id": staff_id, "status": mock_status}

        result = await set_staff_status(staff_id, mock_status, mock_ss)

        mock_ss.get.assert_awaited_once()
        mock_ss.commit.assert_awaited_once()
        mock_get_profile.assert_awaited_once_with(staff_id, mock_ss)
        assert result == {"id": staff_id, "status": mock_status}

@pytest.mark.asyncio
async def test_set_staff_status_staff_not_found():
    staff_id = str(uuid4())
    mock_ss = MagicMock()
    mock_ss.get = AsyncMock(return_value=None)  # Simulating no staff account found

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = None
    mock_cm.__aexit__.return_value = None
    mock_ss.begin.return_value = mock_cm

    mock_status = AccountStatus.DISABLE  # Updated to use the correct enum value

    with pytest.raises(HandledError) as exc_info:
        await set_staff_status(staff_id, mock_status, mock_ss)

    # Assert that the exception message is as expected
    assert str(exc_info.value) == "Staff account not found"
