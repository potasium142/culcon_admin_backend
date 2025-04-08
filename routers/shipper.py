from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgresql.models.order_history import OrderStatus
from services import order as ord_ss

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


@router.post(
    "/order/shipped/{id}",
    tags=["Order"],
)
async def shipped_order(
    _: Permission,
    id: str,
    ss: Session,
):
    return await ord_ss.change_order_status(
        id,
        ss,
        OrderStatus.ON_SHIPPING,
        OrderStatus.SHIPPED,
    )
