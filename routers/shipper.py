from datetime import date
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services import shipper as sp

import auth
from db.postgresql.db_session import get_session
from db.postgresql.paging import Page, page_param


router = APIRouter(
    prefix="/api/shipper",
    tags=["Shipper"],
)


Paging = Annotated[Page, Depends(page_param)]
Permission = Annotated[bool, Depends(auth.shipper_permission)]
Session = Annotated[AsyncSession, Depends(get_session)]
Id = Annotated[str, Depends(auth.staff_id)]


@router.get("/permission_test")
async def test_permission(_: Permission):
    return "ok"


@router.post(
    "/order/shipped/{id}",
    tags=["Order"],
)
async def shipped_order(
    _: Permission,
    id: str,
    self_id: Id,
    ss: Session,
):
    return await sp.complete_shipment(id, self_id, ss)


@router.delete(
    "/order/reject/{id}",
    tags=["Order", "Shipper"],
)
async def reject_shipping_order(
    _: Permission,
    id: str,
    self_id: Id,
    ss: Session,
):
    return await sp.reject_shipment(id, self_id, ss)


@router.put(
    "/order/accept/{id}",
    tags=["Order", "Shipper"],
)
async def accept_shipping_order(
    _: Permission,
    id: str,
    self_id: Id,
    ss: Session,
):
    return await sp.accept_shipment(id, self_id, ss)


@router.get(
    "/order/fetch",
    tags=["Order", "Shipper"],
)
async def fetch_order(
    _: Permission,
    pg: Paging,
    self_id: Id,
    ss: Session,
    start_date_confirm: date | None = None,
    end_date_confirm: date | None = None,
    start_date_shipping: date | None = None,
    end_date_shipping: date | None = None,
):
    return await sp.fetch_shippment_from_range(
        pg,
        ss,
        start_date_confirm,
        end_date_confirm,
        start_date_shipping,
        end_date_shipping,
        shipper_id=self_id,
    )


@router.get(
    "/order/fetch_current",
    tags=["Order", "Shipper"],
)
async def get_latest_order(
    _: Permission,
    self_id: Id,
    ss: Session,
):
    return await sp.get_current_order(self_id, ss)


@router.get(
    "/order/fetch_await",
    tags=["Order", "Shipper"],
)
async def get_await_order(
    _: Permission,
    self_id: Id,
    ss: Session,
):
    return await sp.get_await_order(self_id, ss)
