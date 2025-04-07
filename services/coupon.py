from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from db.postgresql.db_session import db_session
from db.postgresql.models.order_history import Coupon

import uuid
import sqlalchemy as sqla

from db.postgresql.paging import Page, display_page, paging, table_size
from dtos.request.coupon import CouponCreation
from etc.local_error import HandledError


async def create_coupon(c: CouponCreation, ss: AsyncSession):
    async with ss.begin():
        if not c.id:
            id = str(uuid.uuid4()).replace("-", "")[:14]
        else:
            id = c.id

        coupon = Coupon(
            id=id,
            expire_time=c.expire_date,
            usage_amount=c.usage_amount,
            usage_left=c.usage_amount,
            sale_percent=c.sale_percent,
            minimum_price=c.minimum_price,
        )

        ss.add(coupon)
        await ss.commit()

        return {
            "id": id,
            "expire_time": c.expire_date,
            "usage_amount": c.usage_amount,
            "sale_percent": c.sale_percent,
            "minimum_price": c.minimum_price,
        }


async def get_all_coupons(pg: Page, ss: AsyncSession, id: str = ""):
    async with ss.begin():
        coupons = await ss.scalars(
            paging(
                sqla.select(Coupon).filter(Coupon.id.ilike(f"%{id}%")),
                pg,
            )
        )

        coupon_dicts = [
            {
                "id": c.id,
                "usage_left": c.usage_left,
                "expire_time": c.expire_time,
                "sale_percent": c.sale_percent,
                "minimum_price": c.minimum_price,
            }
            for c in coupons
        ]

        count = (
            await ss.scalar(
                sqla.select(sqla.func.count(Coupon.id)).filter(
                    Coupon.id.ilike(f"%{id}%"),
                )
            )
            or 0
        )

        return display_page(
            coupon_dicts,
            count,
            pg,
        )


async def get_coupon(id: str, ss: AsyncSession) -> dict[str, Any]:
    async with ss.begin():
        coupon = await ss.get(Coupon, id)
        if not coupon:
            return {"error": "Coupon not found"}

        return {
            "id": coupon.id,
            "usage_left": coupon.usage_left,
            "expire_time": coupon.expire_time,
            "sale_percent": coupon.sale_percent,
            "minimum_price": coupon.minimum_price,
        }


async def disable_coupon(
    id: str,
    ss: AsyncSession,
):
    async with ss.begin():
        coupon = await ss.get(Coupon, id)

        if not coupon:
            raise HandledError("Coupon not found")

        coupon.usage_left = -1

        await ss.commit()
