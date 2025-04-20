import pytest
from unittest.mock import MagicMock, AsyncMock, patch, Mock
from db.postgresql.db_session import db_session
from db.postgresql.models.staff_account import *
from etc.local_error import HandledError
from db.postgresql.paging import Page
from services.staff import *

from auth import encryption
from datetime import datetime

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from db.postgresql.models import Base

from uuid import UUID
import uuid
from auth import encryption

from .set_up.test_user_account_data import *
from .set_up.test_account_data import *

# Test database URL
DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"

engine = create_async_engine(DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def create_test_db():
    async with engine.begin() as conn:
        # Enable pgvector extension if not already
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


# -----------------------------------------------------------


@pytest.mark.asyncio
async def test_get_all_staff_success(db_session):
    # Arrange: create staff accounts
    staff1 = preb_staff_account_1()
    staff2 = preb_staff_account_2()
    db_session.add_all([staff1, staff2])
    await db_session.commit()

    # Act: call the function to retrieve all staff (no filter)
    page = Page(number=1, size=10)
    result = await get_all_staff(page, db_session)

    # Assert
    assert result["total_element"] == 2
    assert len(result["content"]) == 2
    usernames = [s["username"] for s in result["content"]]
    assert "staff_user_001" in usernames
    assert "staff_user_002" in usernames


@pytest.mark.asyncio
async def test_get_all_staff_success_filter_by_username(db_session):
    # Arrange
    staff = preb_staff_account_1()
    db_session.add(staff)
    await db_session.commit()

    # Act: apply username filter
    page = Page(number=1, size=10)
    result = await get_all_staff(page, db_session, id="staff_user_001")

    # Assert
    assert result["total_element"] == 1
    assert len(result["content"]) == 1
    usernames = [s["username"] for s in result["content"]]
    assert "staff_user_001" in usernames


@pytest.mark.asyncio
async def test_get_all_staff_success_filter_by_type(db_session):
    # Arrange
    staff_admin = preb_manager_account_1()
    staff_editor = preb_staff_account_1()
    db_session.add_all([staff_admin, staff_editor])
    await db_session.commit()

    # Act: filter by AccountType.ADMIN
    page = Page(number=1, size=10)
    result = await get_all_staff(page, db_session, type=AccountType.MANAGER)

    # Assert
    assert result["total_element"] == 1
    assert len(result["content"]) == 1
    usernames = [s["username"] for s in result["content"]]
    assert "manager_user_001" in usernames


@pytest.mark.asyncio
async def test_get_all_staff_empty(db_session):
    # Act: call the function to retrieve all staff (no filter)
    page = Page(number=1, size=10)
    result = await get_all_staff(page, db_session)

    # Assert
    assert result["total_element"] == 0
    assert len(result["content"]) == 0


# -----------------------------------------------------------


@pytest.mark.asyncio
async def test_get_staff_profile_success(db_session):
    # Arrange
    staff = preb_staff_account_1()
    db_session.add(staff)
    await db_session.commit()

    # Act
    result = await get_staff_profile(staff.id, db_session)

    # Assert
    assert result["id"] == UUID(staff.id)
    assert result["username"] == staff.username
    assert result["type"] == "STAFF"
    assert result["status"] == staff.status
    assert result["ssn"] == staff.employee_info.ssn
    assert result["phonenumber"] == staff.employee_info.phonenumber
    assert result["realname"] == staff.employee_info.realname
    assert result["email"] == staff.employee_info.email
    assert result["dob"] == staff.employee_info.dob


@pytest.mark.asyncio
async def test_get_staff_profile_fail_invalid_uuid(db_session):
    # Act & Assert
    with pytest.raises(HandledError, match="UUID invalid"):
        await get_staff_profile("not-a-uuid", db_session)


@pytest.mark.asyncio
async def test_get_staff_profile_fail_staff_not_found(db_session):
    # Use a valid UUID that does not exist
    fake_id = str(uuid4())
    with pytest.raises(HandledError, match="Staff not found"):
        await get_staff_profile(fake_id, db_session)


@pytest.mark.asyncio
async def test_get_staff_profile_fail_employee_info_missing(db_session):
    # Arrange: create StaffAccount without EmployeeInfo
    staff = preb_staff_account_1()
    staff.employee_info = None  # detach employee info
    db_session.add(staff)
    await db_session.commit()

    # Act & Assert
    with pytest.raises(HandledError, match="Employee info not found"):
        await get_staff_profile(staff.id, db_session)


# -----------------------------------------------------------


@pytest.mark.asyncio
async def test_edit_staff_account_success(db_session):
    # Arrange
    staff = preb_staff_account_1()
    db_session.add(staff)
    await db_session.commit()

    new_password = "new_secure_password"
    payload = EditStaffAccount(
        username=staff.username,
        password=new_password,
    )

    staff_id = staff.id
    staff_username = staff.username  # store before expire_all
    staff_oldpass = staff.password

    # Act
    result = await edit_staff_account(staff_id, payload, db_session)

    # Assert
    assert result["id"] == UUID(staff_id)
    assert result["username"] == staff_username

    db_session.expire_all()

    updated = await db_session.get(type(staff), staff_id)
    assert updated is not None
    assert updated.password != staff_oldpass  # assuming you hash it


@pytest.mark.asyncio
async def test_edit_staff_account_fail_empty_password_raises(db_session):
    # Arrange
    staff = preb_staff_account_1()
    db_session.add(staff)
    await db_session.commit()

    payload = EditStaffAccount(
        username="new_name",
        password="",  # empty password
    )

    # Act & Assert
    with pytest.raises(HandledError, match="Password cannot be empty"):
        await edit_staff_account(staff.id, payload, db_session)


@pytest.mark.asyncio
async def test_edit_staff_account_fail_invalid_uuid_raises(db_session):
    staff = preb_staff_account_1()
    db_session.add(staff)
    await db_session.commit()

    payload = EditStaffAccount(
        username="new_name",
        password="abc123",
    )

    invalid_id = "123214324234235345345345345345123"

    # Act & Assert
    with pytest.raises(HandledError, match="UUID invalid"):
        await edit_staff_account(invalid_id, payload, db_session)


@pytest.mark.asyncio
async def test_edit_staff_account_fail_not_found_raises(db_session):
    staff = preb_staff_account_1()
    db_session.add(staff)
    await db_session.commit()

    payload = EditStaffAccount(
        username="new_name",
        password="abc123",
    )

    # random UUID
    missing_id = str(uuid.uuid4())

    # Act & Assert
    with pytest.raises(HandledError, match="Staff account not found"):
        await edit_staff_account(missing_id, payload, db_session)


# -----------------------------------------------------------


@pytest.mark.asyncio
async def test_edit_employee_info_success(db_session):
    # Arrange
    staff = (
        preb_staff_account_1()
    )  # Assuming a function to pre-build staff with necessary info
    db_session.add(staff)
    await db_session.commit()

    valid_ssn = "123456789012"
    payload = EditEmployeeInfo(
        ssn=valid_ssn,
        email="newemail@example.com",
        phonenumber="0234967890",
        dob="1990-01-01",
        realname="New Realname",
    )

    # Act
    result = await edit_employee_info(payload, str(staff.id), db_session)

    # Assert
    assert result["id"] == UUID(staff.id)
    assert result["ssn"] == valid_ssn
    assert result["email"] == "newemail@example.com"
    assert result["phonenumber"] == "0234967890"
    expected_dob = datetime.strptime("1990-01-01", "%Y-%m-%d").date()
    assert result["dob"] == expected_dob
    assert result["realname"] == "New Realname"


@pytest.mark.asyncio
async def test_edit_employee_info_fail_invalid_ssn(db_session):
    # Arrange
    staff = preb_staff_account_1()  # Assuming a function to pre-build staff
    db_session.add(staff)
    await db_session.commit()

    invalid_ssn = "12345"  # SSN length should be 12
    payload = EditEmployeeInfo(
        ssn=invalid_ssn,
        email="new_email@example.com",
        phonenumber="0234567890",
        dob="1990-01-01",
        realname="New Realname",
    )

    # Act & Assert
    with pytest.raises(HandledError, match="SSN must be 12 numbers"):
        await edit_employee_info(payload, str(staff.id), db_session)


@pytest.mark.asyncio
async def test_edit_employee_info_fail_invalid_uuid(db_session):
    # Arrange
    staff = preb_staff_account_1()  # Assuming a function to pre-build staff
    db_session.add(staff)
    await db_session.commit()

    invalid_uuid = "123214324234235345345345345345123"
    payload = EditEmployeeInfo(
        ssn="123456789012",
        email="newemail@example.com",
        phonenumber="0234567890",
        dob="1990-01-01",
        realname="New Realname",
    )

    # Act & Assert
    with pytest.raises(HandledError, match="UUID invalid"):
        await edit_employee_info(payload, invalid_uuid, db_session)


@pytest.mark.asyncio
async def test_edit_employee_info_fail_not_found(db_session):
    # Arrange
    staff = preb_staff_account_1()  # Assuming a function to pre-build staff
    db_session.add(staff)
    await db_session.commit()

    missing_uuid = str(uuid.uuid4())  # This ID doesn't exist in the DB
    payload = EditEmployeeInfo(
        ssn="123456789012",
        email="newemail@example.com",
        phonenumber="0234567890",
        dob="1990-01-01",
        realname="New Realname",
    )

    # Act & Assert
    with pytest.raises(HandledError, match="Staff account not found"):
        await edit_employee_info(payload, missing_uuid, db_session)


# -----------------------------------------------------------


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

    with patch(
        "services.staff.get_staff_profile", new_callable=AsyncMock
    ) as mock_get_profile:
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
