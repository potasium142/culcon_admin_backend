from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import func
import sqlalchemy as sqla
from datetime import date, timedelta
from db.postgresql.models.transaction import PaymentTransaction


async def get_last_7_days_revenue(db: AsyncSession) -> list[dict[str, float]]:
    async with db.begin():
        today = date.today()
        revenues = []
        for i in range(7):
            target_date = today - timedelta(days=i)
            daily_revenue = (
                await db.scalar(
                    sqla.select(func.sum(PaymentTransaction.amount)).filter(
                        func.date(PaymentTransaction.create_time) == target_date
                    )
                )
                or 0.0
            )
            revenues.append({"date": target_date.isoformat(), "revenue": daily_revenue})
        return revenues


async def get_last_6_months_revenue(ss: AsyncSession) -> list[dict[str, float]]:
    async with ss.begin():
        today = date.today()
        revenues = []
        for i in range(6):
            target_month = (today.month - i - 1) % 12 + 1
            target_year = today.year - ((today.month - i - 1) // 12)
            monthly_revenue = (
                await ss.scalar(
                    sqla.select(func.sum(PaymentTransaction.amount))
                    .filter(
                        func.extract("year", PaymentTransaction.create_time)
                        == target_year
                    )
                    .filter(
                        func.extract("month", PaymentTransaction.create_time)
                        == target_month
                    )
                )
                or 0.0
            )
            revenues.append({
                "month": f"{target_year}-{target_month:02d}",
                "revenue": monthly_revenue,
            })
        return revenues
