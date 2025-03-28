from datetime import date
from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from services.predict import (
    load_product_model,
    predict_top_selling_products,
    load_revenue_model,
    predict_next_month_revenue,
)
from db.postgresql.db_session import get_session
from db.postgresql.models.staff_account import AccountStatus
from dtos.request.account import AccountCreateDto
from dtos.request.coupon import CouponCreation

from services.product import (
    get_top_10_products_month,
    get_top_10_products_all_time,
)

from dtos.request.staff import EditEmployeeInfo, EditStaffAccount
from services import account as acc_sv
from services import coupon as coupon_sv
from services import staff as staff_sv

from services.revenue import get_last_7_days_revenue, get_last_6_months_revenue

import auth

from db.postgresql.paging import page_param, Page

Paging = Annotated[Page, Depends(page_param)]
Permission = Annotated[bool, Depends(auth.manager_permission)]
Session = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(prefix="/api/manager", tags=["Manager function"])

oauth2_scheme = auth.oauth2_scheme

product_model = load_product_model("product_prediction_linear.pkl")
revenue_model = load_revenue_model("revenue_prediction_xgb.pkl")


class DailyRevenue(BaseModel):
    date: str
    revenue: float


class MonthlyRevenue(BaseModel):
    month: str
    revenue: float


class RevenueResponse(BaseModel):
    last_7_days_revenue: list[DailyRevenue]
    last_6_months_revenue: list[MonthlyRevenue]


class TopProduct(BaseModel):
    product_name: str
    total_quantity: int


class TopProductsResponse(BaseModel):
    top_10_products_month: list[TopProduct]
    top_10_products_all_time: list[TopProduct]


class CombinedRevenueAndProductsResponse(BaseModel):
    revenue: RevenueResponse
    top_products: TopProductsResponse


class PredictedProduct(BaseModel):
    product_id: str
    product_name: str


class PredictedProductsResponse(BaseModel):
    top_predicted_products: list[PredictedProduct]


class RevenuePredictionResponse(BaseModel):
    predicted_revenue: float


@router.get("/permission_test")
async def test(_: Permission):
    return "ok"


@router.post(
    "/create/account",
    response_model=None,
)
async def create(
    _: Permission,
    account: AccountCreateDto,
    ss: Session,
) -> dict[str, str]:
    token = await acc_sv.create_account(account, ss)
    return {"access_token": token}


@router.post(
    "/coupon/create",
    tags=["Coupon"],
)
async def create_coupon(
    _: Permission,
    coupon: CouponCreation,
    ss: Session,
):
    return await coupon_sv.create_coupon(coupon, ss)


@router.delete(
    "/coupon/disable",
    tags=["Coupon"],
)
async def disable_coupon(
    _: Permission,
    coupon_id: str,
    ss: Session,
) -> None:
    await coupon_sv.disable_coupon(coupon_id, ss)


@router.get(
    "/staff/fetch/all",
    tags=["Staff Managment"],
)
async def read_all_staff(
    _: Permission,
    pg: Paging,
    ss: Session,
):
    staff = await staff_sv.get_all_staff(pg, ss)
    return staff


@router.get(
    "/staff/fetch/{id}",
    tags=["Staff Managment"],
)
async def read_staff_profile(
    _: Permission,
    id: str,
    ss: Session,
):
    staff_profile = await staff_sv.get_staff_profile(id, ss)
    return staff_profile


@router.post(
    "/staff/edit/account",
    tags=["Staff Managment"],
)
async def edit_staff_account(
    id: str,
    info: EditStaffAccount,
    _: Permission,
    ss: Session,
):
    return await staff_sv.edit_staff_account(id, info, ss)


@router.post(
    "/staff/edit/info",
    tags=["Staff Managment"],
)
async def edit_staff_info(
    id: str,
    info: EditEmployeeInfo,
    _: Permission,
    ss: Session,
):
    return await staff_sv.edit_employee_info(info, id, ss)


@router.post(
    "/staff/edit/status",
    tags=["Staff Managment"],
)
async def edit_staff_status(
    id: str,
    status: AccountStatus,
    _: Permission,
    ss: Session,
):
    return await staff_sv.set_staff_status(id, status, ss)


@router.get(
    "/revenue",
    response_model=CombinedRevenueAndProductsResponse,
)
async def get_revenue_and_top_products(
    _: Permission,
    ss: Session,
) -> CombinedRevenueAndProductsResponse:
    daily_revenues = await get_last_7_days_revenue(ss)
    monthly_revenues = await get_last_6_months_revenue(ss)

    today = date.today()
    top_products_month = await get_top_10_products_month(ss, today.year, today.month)
    top_products_all_time = await get_top_10_products_all_time(ss)

    return CombinedRevenueAndProductsResponse(
        revenue=RevenueResponse(
            last_7_days_revenue=daily_revenues,
            last_6_months_revenue=monthly_revenues,
        ),
        top_products=TopProductsResponse(
            top_10_products_month=top_products_month,
            top_10_products_all_time=top_products_all_time,
        ),
    )


@router.get(
    "/revenue/predicted-products",
    response_model=PredictedProductsResponse,
)
async def get_predicted_top_products(
    _: Permission,
    ss: Session,
) -> PredictedProductsResponse:
    today = date.today()
    last_month = today.month - 1 if today.month > 1 else 12
    last_year = today.year if today.month > 1 else today.year - 1

    predicted_products = await predict_top_selling_products(
        ss, product_model, last_year, last_month
    )

    return PredictedProductsResponse(top_predicted_products=predicted_products)


@router.get(
    "/revenue/predict-next-month",
    response_model=RevenuePredictionResponse,
)
async def get_next_month_revenue_prediction(
    _: Permission,
    ss: Session,
) -> RevenuePredictionResponse:
    today = date.today()
    next_month = today.month + 1 if today.month < 12 else 1
    next_year = today.year if today.month < 12 else today.year + 1

    predicted_revenue = await predict_next_month_revenue(
        ss, revenue_model, next_year, next_month
    )

    return RevenuePredictionResponse(predicted_revenue=predicted_revenue)
