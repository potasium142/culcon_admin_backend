import pickle
import pandas as pd
import sqlalchemy as sqla
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.postgresql.models.product import Product
from db.postgresql.models.order_history import OrderHistoryItems, OrderHistory
from db.postgresql.models.user_account import Cart


def load_product_model(file_path_product: str):
    file_path_product = r"./ai/weights/linear_regression_product_model.pkl"
    with open(file_path_product, "rb") as f:
        model = pickle.load(f)
    return model


def load_revenue_model(file_path_revenue: str):
    file_path_revenue = r"./ai/weights/xgb_revenue.pkl"
    with open(file_path_revenue, "rb") as f:
        model = pickle.load(f)
    return model


async def prepare_data_for_prediction(ss: AsyncSession, year: int, month: int):
    r = await ss.execute(
        sqla.select(
            OrderHistoryItems.product_id.label("product_id"),
            func.sum(OrderHistoryItems.quantity).label(
                "total_quantity_sold_last_month"
            ),
            func.sum(Cart.amount).label("cart_add_count"),
            Product.price.label("price"),
            Product.sale_percent.label("sale_percent"),
        )
        .join(OrderHistory, OrderHistory.id == OrderHistoryItems.order_history_id)
        .join(Product, Product.id == OrderHistoryItems.product_id)
        .outerjoin(Cart, Cart.product_id == Product.id)
        .filter(func.extract("year", OrderHistory.order_date) == year)
        .filter(func.extract("month", OrderHistory.order_date) == month)
        .group_by(OrderHistoryItems.product_id, Product.price, Product.sale_percent)
    )

    results = r.all()

    data = pd.DataFrame(
        results,
        columns=[
            "product_id",
            "total_quantity_sold_last_month",
            "cart_add_count",
            "price",
            "sale_percent",
        ],
    )

    data["cart_add_count"] = data["cart_add_count"].fillna(0)

    return data


async def predict_top_selling_products(
    ss: AsyncSession, model, year: int, month: int, top_n: int = 10
):
    async with ss.begin():
        data = await prepare_data_for_prediction(ss, year, month)

        if data.empty:
            return []

        features = [
            "total_quantity_sold_last_month",
            "price",
            "sale_percent",
            "cart_add_count",
        ]
        data["predicted_quantity"] = model.predict(data[features])

        data = data.sort_values(by="predicted_quantity", ascending=False)

        product_ids = data["product_id"].tolist()
        product_raw = await ss.execute(
            sqla.select(Product.id, Product.product_name).filter(
                Product.id.in_(product_ids)
            )
        )

        products = product_raw.all()

        product_info = {p.id: p.product_name for p in products}

        data["product_name"] = data["product_id"].map(product_info)

    return (
        data[["product_id", "product_name", "predicted_quantity"]]
        .head(top_n)
        .to_dict(orient="records")
    )


async def prepare_data_for_revenue_prediction(
    ss: AsyncSession,
    year: int,
    month: int,
):
    async with ss.begin():
        order_count = (
            await ss.scalar(
                sqla.select(func.count(OrderHistory.id))
                .filter(func.extract("year", OrderHistory.order_date) == year)
                .filter(func.extract("month", OrderHistory.order_date) == month)
            )
            or 0
        )

        total_quantity_sold = (
            await ss.scalar(
                sqla.select(func.sum(OrderHistoryItems.quantity))
                .join(
                    OrderHistory, OrderHistory.id == OrderHistoryItems.order_history_id
                )
                .filter(func.extract("year", OrderHistory.order_date) == year)
                .filter(func.extract("month", OrderHistory.order_date) == month)
            )
            or 0
        )

        total_price = (
            await ss.scalar(
                sqla.select(func.sum(OrderHistory.total_price))
                .filter(func.extract("year", OrderHistory.order_date) == year)
                .filter(func.extract("month", OrderHistory.order_date) == month)
            )
            or 0
        )

        avg_order_value = total_price / order_count if order_count > 0 else 0

        avg_discount_rate = await ss.scalar(
            sqla.select(func.avg(Product.sale_percent))
            .join(OrderHistoryItems, Product.id == OrderHistoryItems.product_id)
            .join(OrderHistory, OrderHistory.id == OrderHistoryItems.order_history_id)
            .filter(func.extract("year", OrderHistory.order_date) == year)
            .filter(func.extract("month", OrderHistory.order_date) == month)
        )

        data = {
            "order_count": order_count or 0,
            "total_quantity_sold": total_quantity_sold or 0,
            "avg_order_value": avg_order_value or 0,
            "avg_discount_rate": avg_discount_rate or 0,
        }

        return data


async def predict_next_month_revenue(db: AsyncSession, model, year: int, month: int):
    data = await prepare_data_for_revenue_prediction(db, year, month)

    features = [
        data["order_count"],
        data["total_quantity_sold"],
        data["avg_order_value"],
        data["avg_discount_rate"],
    ]
    features = [features]

    predicted_revenue = model.predict(features)

    return predicted_revenue[0]
