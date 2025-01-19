from db.postgresql.db_session import db_session
from db.postgresql.models.staff_account import AccountStatus, AccountType, StaffAccount


def get_all_staff():
    return (
        db_session.session.query(StaffAccount).filter_by(type=AccountType.STAFF).all()
    )


def get_staff_profile(id: str):
    return db_session.session.query(StaffAccount).get(id)


def edit_staff_profile():
    pass


def edit_employee_info():
    pass


def set_staff_status(
    id: str,
    status: AccountStatus,
):
    staff: StaffAccount = db_session.session.get(StaffAccount, id)

    if not staff:
        raise Exception("Staff account not found")

    staff.status = status

    db_session.commit()
