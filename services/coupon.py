from typing import Any
from db.postgresql.db_session import db_session
from db.postgresql.models.order_history import Coupon

import uuid
import sqlalchemy as sqla

from db.postgresql.paging import Page, paging
from dtos.request.coupon import CouponCreation
from etc.local_error import HandledError


def create_coupon(c: CouponCreation):
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

    db_session.session.add(coupon)
    db_session.commit()

    return {
        "id": id,
        "expire_time": c.expire_date,
        "usage_amount": c.usage_amount,
        "sale_percent": c.sale_percent,
        "minimum_price": c.minimum_price,
    }


def get_all_coupons(pg: Page) -> list[dict[str, Any]]:
    with db_session.session as ss:
        coupons = ss.scalars(
            paging(
                sqla.select(Coupon),
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

        return coupon_dicts


def get_coupon(id: str) -> dict[str, Any]:
    with db_session.session as ss:
        coupon: Coupon = ss.get(Coupon, id)
        if not coupon:
            return {"error": "Coupon not found"}

        return {
            "id": coupon.id,
            "usage_left": coupon.usage_left,
            "expire_time": coupon.expire_time,
            "sale_percent": coupon.sale_percent,
            "minimum_price": coupon.minimum_price,
        }


def disable_coupon(
    id: str,
):
    coupon: Coupon = db_session.session.get(Coupon, id)

    if not coupon:
        raise HandledError("Coupon not found")
    coupon.usage_left = -1

    db_session.commit()
