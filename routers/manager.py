from datetime import date
from typing import Annotated
from fastapi import APIRouter, Depends

from dtos.request.account import AccountCreateDto
from dtos.request.coupon import CouponCreation

from services import account_service as acc_sv
from services import coupon as coupon_sv

import auth

Permission = Annotated[bool, Depends(auth.manager_permission)]

router = APIRouter(prefix="/api/manager", tags=["Manager"])

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
)
async def create_coupon(
    _permission: Permission,
    coupon: CouponCreation,
) -> dict[str, str | int | date | float]:
    return coupon_sv.create_coupon(coupon)


@router.delete("/coupon/disable")
async def disable_coupon(
    _permission: Permission,
    coupon_id: str,
) -> None:
    coupon_sv.disable_coupon(coupon_id)
