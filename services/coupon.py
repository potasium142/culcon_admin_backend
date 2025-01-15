from db.postgresql.db_session import db_session
from db.postgresql.models.order_history import Coupon

import uuid

from dtos.request.coupon import CouponCreation


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
    )

    db_session.session.add(coupon)
    db_session.commit()

    return {
        "id": id,
        "expire_time": c.expire_date,
        "usage_amount": c.usage_amount,
        "sale_percent": c.sale_percent,
    }


def disable_coupon(
    id: str,
):
    coupon: Coupon = db_session.session.query(Coupon).get(id)
    coupon.usage_left = -1

    db_session.commit()
