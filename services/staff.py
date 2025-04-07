from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
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


async def get_all_staff(
    pg: Page,
    ss: AsyncSession,
    id: str = "",
):
    async with ss.begin():
        data = await ss.scalars(
            paging(
                sqla.select(StaffAccount).filter(
                    StaffAccount.type == AccountType.STAFF,
                    StaffAccount.username.ilike(f"%{id}%"),
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
            await ss.scalar(
                sqla.select(sqla.func.count(StaffAccount.id)).filter(
                    StaffAccount.type == AccountType.STAFF,
                    StaffAccount.username.ilike(f"%{id}%"),
                )
            )
            or 0
        )
        return display_page(data, count, pg)


async def get_staff_profile(id: str, ss: AsyncSession):
    async with ss.begin():
        try:
            uid = UUID(id.strip())
        except ValueError as _:
            raise HandledError("UUID invalid")

        s = await ss.get(StaffAccount, uid)

        if not s:
            raise HandledError("Staff not found")

        employee_info = await ss.get(EmployeeInfo, uid)

        if not employee_info:
            raise HandledError("Employee info not found")

        return {
            "id": s.id,
            "username": s.username,
            "type": "MANAGER" if s.type == AccountType.MANAGER else "STAFF",
            "status": s.status,
            "ssn": employee_info.ssn,
            "phonenumber": employee_info.phonenumber,
            "realname": employee_info.realname,
            "email": employee_info.email,
            "dob": employee_info.dob,
        }


async def edit_staff_account(
    staff_id: str,
    info: EditStaffAccount,
    ss: AsyncSession,
):
    async with ss.begin():
        try:
            uid = UUID(staff_id.strip())
        except ValueError as _:
            raise HandledError("UUID invalid")

        staff = await ss.get(StaffAccount, uid)

        if not staff:
            raise HandledError("Staff account not found")

        new_password = encryption.hash(info.password)

        staff.password = new_password
        staff.username = info.username

        await ss.commit()

    return await get_staff_profile(staff_id, ss)


async def edit_employee_info(
    emp_info: EditEmployeeInfo,
    staff_id: str,
    ss: AsyncSession,
):
    async with ss.begin():
        try:
            uid = UUID(staff_id.strip())
        except ValueError as _:
            raise HandledError("UUID invalid")

        staff = await ss.get(EmployeeInfo, uid)

        if not staff:
            raise HandledError("Staff account not found")

        staff.ssn = emp_info.ssn
        staff.email = emp_info.email
        staff.phonenumber = emp_info.phonenumber
        staff.dob = emp_info.dob
        staff.realname = emp_info.realname

        await ss.commit()

    return await get_staff_profile(staff_id, ss)


async def set_staff_status(
    id: str,
    status: AccountStatus,
    ss: AsyncSession,
):
    async with ss.begin():
        try:
            uid = UUID(id.strip())
        except ValueError as _:
            raise HandledError("UUID invalid")

        staff = await ss.get(StaffAccount, uid)

        if not staff:
            raise HandledError("Staff account not found")

        staff.status = status

        await ss.commit()

    return await get_staff_profile(id, ss)
