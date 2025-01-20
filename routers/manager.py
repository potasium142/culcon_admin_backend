from datetime import date
from typing import Annotated
from fastapi import APIRouter, Depends

from db.postgresql.models.staff_account import AccountStatus
from dtos.request.account import AccountCreateDto
from dtos.request.coupon import CouponCreation

from dtos.request.staff import EditEmployeeInfo, EditStaffAccount
from services import account_service as acc_sv
from services import coupon as coupon_sv
from services import staff as staff_sv

import auth

Permission = Annotated[bool, Depends(auth.manager_permission)]

router = APIRouter(prefix="/api/manager", tags=["Manager function"])

oauth2_scheme = auth.oauth2_scheme


@router.get("/permission_test")
async def test(_permission: Permission):
    return "ok"


@router.post(
    "/create/account",
    response_model=None,
)
async def create(
    _permission: Permission,
    account: AccountCreateDto,
) -> dict[str, str]:
    token = acc_sv.create_account(account)
    return {"access_token": token}


@router.post(
    "/coupon/create",
    tags=["Coupon"],
)
async def create_coupon(
    _permission: Permission,
    coupon: CouponCreation,
) -> dict[str, str | int | date | float]:
    return coupon_sv.create_coupon(coupon)


@router.delete(
    "/coupon/disable",
    tags=["Coupon"],
)
async def disable_coupon(
    _permission: Permission,
    coupon_id: str,
) -> None:
    coupon_sv.disable_coupon(coupon_id)


@router.get(
    "/staff/fetch/all",
)
def read_all_staff(
    _: Permission,
):
    staff = staff_sv.get_all_staff()
    return staff


@router.get(
    "/staff/fetch/{id}",
)
def read_staff_profile(
    _: Permission,
    id: str,
):
    staff_profile = staff_sv.get_staff_profile(id)
    return staff_profile


@router.post("/staff/edit/account")
def edit_staff_account(
    id: str,
    info: EditStaffAccount,
    _: Permission,
):
    return staff_sv.edit_staff_account(id, info)


@router.post("/staff/edit/info")
def edit_staff_info(
    id: str,
    info: EditEmployeeInfo,
    _: Permission,
):
    return staff_sv.edit_employee_info(info, id)


@router.post("/staff/edit/status")
def edit_staff_status(
    id: str,
    status: AccountStatus,
    _: Permission,
):
    return staff_sv.set_staff_status(id, status)
