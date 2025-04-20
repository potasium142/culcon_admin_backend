# test_data.py
from datetime import date
from dtos.request.account import AccountCreateDto, AccountInfoForm
from db.postgresql.models.staff_account import *

def get_sample_account_dto():
    return AccountCreateDto.model_construct(
        username="testuser2",
        password="testpassword2",
        type=AccountType.STAFF,
        account_status=AccountStatus.ACTIVE,
        employee_info=AccountInfoForm.model_construct(
            ssn="129999999",
            phonenumber="0919999999",
            realname="Test Userrrrrrr",
            email="test2@example.com",
            dob=date(1990, 1, 1)
        )
    )

def ex_account_dto_1():
    return AccountCreateDto.model_construct(
        username="testuser1",
        password="testpassword1",
        type=AccountType.STAFF,
        account_status=AccountStatus.ACTIVE,
        employee_info=AccountInfoForm.model_construct(
            ssn="123456799",
            phonenumber="0912345699",
            realname="Test Userr",
            email="test1@example.com",
            dob=date(1990, 1, 1)
        )
    )

def ex_account_dto_2_shipper():
    return AccountCreateDto.model_construct(
        username="testuser1",
        password="testpassword1",
        type=AccountType.SHIPPER,
        account_status=AccountStatus.ACTIVE,
        employee_info=AccountInfoForm.model_construct(
            ssn="123456799",
            phonenumber="0912345699",
            realname="Test Userr",
            email="test1@example.com",
            dob=date(1990, 1, 1)
        )
    )

def ex_account_dto_1_null01():
    return AccountCreateDto.model_construct(
        username=None,
        password="testpassword1",
        type=AccountType.STAFF,
        account_status=AccountStatus.ACTIVE,
        employee_info=AccountInfoForm.model_construct(
            ssn=None,
            phonenumber=None,
            realname=None,
            email=None,
            dob=date(1990, 1, 1)
        )
    )

def ex_account_dto_1_null02():
    return AccountCreateDto.model_construct(
        username=None,
        password=None,
        type=AccountType.STAFF,
        account_status=AccountStatus.ACTIVE,
        employee_info=AccountInfoForm.model_construct(
            ssn=None,
            phonenumber=None,
            realname=None,
            email=None,
            dob=date(1990, 1, 1)
        )
    )


def preb_staff_account_1() -> StaffAccount:
    # Create a staff account
    staff_account = StaffAccount(
        id="12345678-9012-3456-7890-123456789012",
        username="staff_user_001",
        password="secure_password",  # You should hash the password before storing it
        type=AccountType.STAFF,
        status=AccountStatus.ACTIVE,
        token=str(uuid4())  # Example token, replace with a valid token generation method
    )

    # Create associated employee info
    employee_info = EmployeeInfo(
        account_id=staff_account.id,
        ssn="123-45-6789",  # Replace with a valid SSN
        phonenumber="1234567890",  # Replace with valid phone number
        realname="John Doe",
        email="johndoe@example.com",  # Replace with valid email
        dob=date(1990, 1, 1)  # Replace with a valid date of birth
    )

    # Attach employee info to staff account
    staff_account.employee_info = employee_info

    return staff_account

def preb_staff_account_2() -> StaffAccount:
    # Create a staff account
    staff_account = StaffAccount(
        id="87654321-4321-6789-4321-987654321098",
        username="staff_user_002",
        password="secure_password",  # You should hash the password before storing it
        type=AccountType.STAFF,
        status=AccountStatus.ACTIVE,
        token=str(uuid4())  # Example token, replace with a valid token generation method
    )

    # Create associated employee info
    employee_info = EmployeeInfo(
        account_id=staff_account.id,
        ssn="123-45-6999",  # Replace with a valid SSN
        phonenumber="1234567899",  # Replace with valid phone number
        realname="John Two",
        email="johntwo@example.com",  # Replace with valid email
        dob=date(1990, 1, 1)  # Replace with a valid date of birth
    )

    # Attach employee info to staff account
    staff_account.employee_info = employee_info

    return staff_account

def preb_manager_account_1() -> StaffAccount:
    # Create a staff account
    staff_account = StaffAccount(
        id="f48cce55-8a67-4e02-87e7-298efb0d93c1",
        username="manager_user_001",
        password="secure_password",  # You should hash the password before storing it
        type=AccountType.MANAGER,
        status=AccountStatus.ACTIVE,
        token=str(uuid4())  # Example token, replace with a valid token generation method
    )

    # Create associated employee info
    employee_info = EmployeeInfo(
        account_id=staff_account.id,
        ssn="999-45-6999",  # Replace with a valid SSN
        phonenumber="1234569999",  # Replace with valid phone number
        realname="John Manager",
        email="johnmanager@example.com",  # Replace with valid email
        dob=date(1990, 1, 1)  # Replace with a valid date of birth
    )

    # Attach employee info to staff account
    staff_account.employee_info = employee_info

    return staff_account