from datetime import date
from pydantic.dataclasses import dataclass


@dataclass
class CouponCreation:
    expire_date: date
    sale_percent: float
    usage_amount: int
    id: str | None = None
