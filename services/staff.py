from auth import encryption
from db.postgresql.db_session import db_session
from db.postgresql.models.staff_account import (
    AccountStatus,
    AccountType,
    EmployeeInfo,
    StaffAccount,
)
from db.postgresql.paging import Page, display_page, paging
from dtos.request.staff import EditEmployeeInfo, EditStaffAccount
from etc.local_error import HandledError
import sqlalchemy as sqla


def map_staff_output(s: StaffAccount):
    return {
        "id": s.id,
        "username": s.username,
        "type": "MANAGER" if s.type == AccountType.MANAGER else "STAFF",
        "status": s.status,
    }


def get_all_staff(pg: Page):
    with db_session.session as ss:
        data = ss.scalars(
            paging(
                sqla.select(StaffAccount).filter(
                    StaffAccount.type == AccountType.STAFF,
                ),
                pg,
            )
        )

        data = list(
            map(
                map_staff_output,
                data,
            )
        )

        count = (
            ss.scalar(
                sqla.select(sqla.func.count(StaffAccount.id)).filter(
                    StaffAccount.type == AccountType.STAFF
                )
            )
            or 0
        )
        return display_page(data, count, pg)


def get_staff_profile(id: str):
    with db_session.session as session:
        s: StaffAccount = session.get(StaffAccount, id)

        if not s:
            raise HandledError("Staff not found")

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
        raise HandledError("Staff account not found")

    new_password = encryption.hash(info.password)

    staff.password = new_password
    staff.username = info.username

    db_session.commit()

    return get_staff_profile(staff_id)


def edit_employee_info(
    emp_info: EditEmployeeInfo,
    staff_id: str,
):
    staff: EmployeeInfo = db_session.session.get(EmployeeInfo, staff_id)

    if not staff:
        raise HandledError("Staff account not found")

    staff.ssn = emp_info.ssn
    staff.email = emp_info.email
    staff.phonenumber = emp_info.phonenumber
    staff.dob = emp_info.dob
    staff.realname = emp_info.realname

    db_session.commit()

    return get_staff_profile(staff_id)


def set_staff_status(
    id: str,
    status: AccountStatus,
):
    staff: StaffAccount = db_session.session.get(StaffAccount, id)

    if not staff:
        raise HandledError("Staff account not found")

    staff.status = status

    db_session.commit()

    return get_staff_profile(id)
