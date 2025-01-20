from auth import encryption
from db.postgresql.db_session import db_session
from db.postgresql.models.staff_account import (
    AccountStatus,
    AccountType,
    EmployeeInfo,
    StaffAccount,
)
from dtos.request.staff import EditEmployeeInfo, EditStaffAccount


def map_staff_output(s: StaffAccount):
    return {
        "id": s.id,
        "username": s.username,
        "type": "MANAGER" if s.type == AccountType.MANAGER else "STAFF",
        "status": s.status,
    }


def get_all_staff():
    with db_session.session as session:
        data = (
            session.query(StaffAccount)
            .filter_by(
                type=AccountType.STAFF,
            )
            .all()
        )

        data = list(
            map(
                map_staff_output,
                data,
            )
        )

        return data


def get_staff_profile(id: str):
    with db_session.session as session:
        s: StaffAccount = session.get(StaffAccount, id)

        if not s:
            raise Exception("Staff not found")

        return {
            "id": s.id,
            "username": s.username,
            "type": "MANAGER" if s.type == AccountType.MANAGER else "STAFF",
            "status": s.status,
            "ssn": s.employee_info.ssn,
            "phonenumber": s.employee_info.phonenumber,
            "realname": s.employee_info.realname,
            "email": s.employee_info.email,
            "dob": s.employee_info.dob,
        }


def edit_staff_account(
    staff_id: str,
    info: EditStaffAccount,
):
    staff: StaffAccount = db_session.session.get(StaffAccount, staff_id)

    if not staff:
        raise Exception("Staff account not found")

    new_password = encryption.hash(info.password)

    staff.password = new_password
    staff.username = info.username
    staff.status = info.status

    db_session.commit()

    return get_staff_profile(staff_id)


def edit_employee_info(
    emp_info: EditEmployeeInfo,
    staff_id: str,
):
    staff: EmployeeInfo = db_session.session.get(EmployeeInfo, staff_id)

    if not staff:
        raise Exception("Staff account not found")

    staff.ssn = emp_info.ssn
    staff.email = emp_info.email
    staff.phonenumber = emp_info.phonenumber
    staff.dob = emp_info.dob
    staff.realname = emp_info.realname

    return get_staff_profile(staff_id)


def set_staff_status(
    id: str,
    status: AccountStatus,
):
    staff: StaffAccount = db_session.session.get(StaffAccount, id)

    if not staff:
        raise Exception("Staff account not found")

    staff.status = status

    db_session.commit()

    return get_staff_profile(id)
