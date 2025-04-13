import pytest
from unittest.mock import patch, MagicMock
from db.postgresql.db_session import db_session
from db.postgresql.models.staff_account import StaffAccount, AccountType, EmployeeInfo
from etc.local_error import HandledError
from db.postgresql.paging import Page
from services.staff import get_all_staff, get_staff_profile  


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