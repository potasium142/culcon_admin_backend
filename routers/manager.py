from datetime import date
from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from services.predict import load_product_model, predict_top_selling_products, load_revenue_model, predict_next_month_revenue
from db.postgresql.models.staff_account import AccountStatus
from dtos.request.account import AccountCreateDto
from dtos.request.coupon import CouponCreation
from services.product import (
    get_top_10_products_month,
    get_top_10_products_all_time,
)
from dtos.request.staff import EditEmployeeInfo, EditStaffAccount
from services import account_service as acc_sv
from services import coupon as coupon_sv
from services import staff as staff_sv
from services.revenue import get_last_7_days_revenue, get_last_6_months_revenue
from db.postgresql.db_session import db_session
import auth

Permission = Annotated[bool, Depends(auth.manager_permission)]

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
    last_7_days_revenue: List[DailyRevenue]
    last_6_months_revenue: List[MonthlyRevenue]


class TopProduct(BaseModel):
    product_name: str
    total_quantity: int


class TopProductsResponse(BaseModel):
    top_10_products_month: List[TopProduct]
    top_10_products_all_time: List[TopProduct]


class CombinedRevenueAndProductsResponse(BaseModel):
    revenue: RevenueResponse
    top_products: TopProductsResponse


class PredictedProduct(BaseModel):
    product_id: str
    product_name: str


class PredictedProductsResponse(BaseModel):
    top_predicted_products: List[PredictedProduct]


class RevenuePredictionResponse(BaseModel):
    predicted_revenue: float


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


@router.get("/revenue", response_model=CombinedRevenueAndProductsResponse)
def get_revenue_and_top_products(_: Permission) -> CombinedRevenueAndProductsResponse:
    daily_revenues = get_last_7_days_revenue(db_session.session)
    monthly_revenues = get_last_6_months_revenue(db_session.session)

    today = date.today()
    top_products_month = get_top_10_products_month(
        db_session.session, today.year, today.month
    )
    top_products_all_time = get_top_10_products_all_time(db_session.session)

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


@router.get("/revenue/predicted-products", response_model=PredictedProductsResponse)
def get_predicted_top_products(_: Permission) -> PredictedProductsResponse:
    today = date.today()
    last_month = today.month - 1 if today.month > 1 else 12
    last_year = today.year if today.month > 1 else today.year - 1

    predicted_products = predict_top_selling_products(
        db_session.session, product_model, last_year, last_month
    )

    return PredictedProductsResponse(top_predicted_products=predicted_products)


@router.get("/revenue/predict-next-month", response_model=RevenuePredictionResponse)
def get_next_month_revenue_prediction() -> RevenuePredictionResponse:
    today = date.today()
    next_month = today.month + 1 if today.month < 12 else 1
    next_year = today.year if today.month < 12 else today.year + 1

    predicted_revenue = predict_next_month_revenue(
        db_session.session, revenue_model, next_year, next_month)

    return RevenuePredictionResponse(predicted_revenue=predicted_revenue)
