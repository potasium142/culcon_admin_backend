import pickle
import pandas as pd
from sqlalchemy.orm import Session
from db.postgresql.db_session import db_session
from sqlalchemy import func
from db.postgresql.models.product import Product
from sqlalchemy import Table, MetaData
from db.postgresql.models.order_history import OrderHistoryItems, OrderHistory

metadata = MetaData()
Cart = Table("cart", metadata, autoload_with=db_session.session.bind)


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


def prepare_data_for_prediction(db: Session, year: int, month: int):
    results = (
        db.query(
            OrderHistoryItems.c.product_id_product_id.label("product_id"),
            func.sum(OrderHistoryItems.c.quantity).label(
                "total_quantity_sold_last_month"),
            func.sum(Cart.c.amount).label("cart_add_count"),
            Product.price.label("price"),
            Product.sale_percent.label("sale_percent")
        )
        .join(OrderHistory, OrderHistory.id == OrderHistoryItems.c.order_history_id)
        .join(Product, Product.id == OrderHistoryItems.c.product_id_product_id)
        .outerjoin(Cart, Cart.c.product_id == Product.id)
        .filter(func.extract("year", OrderHistory.order_date) == year)
        .filter(func.extract("month", OrderHistory.order_date) == month)
        .group_by(
            OrderHistoryItems.c.product_id_product_id,
            Product.price,
            Product.sale_percent
        )
        .all()
    )

    data = pd.DataFrame(results, columns=[
        "product_id", "total_quantity_sold_last_month", "cart_add_count", "price", "sale_percent"
    ])

    data["cart_add_count"] = data["cart_add_count"].fillna(0)

    return data


def predict_top_selling_products(db: Session, model, year: int, month: int, top_n: int = 10):
    data = prepare_data_for_prediction(db, year, month)

    if data.empty:
        return []

    features = ["total_quantity_sold_last_month",
                "price", "sale_percent", "cart_add_count"]
    data["predicted_quantity"] = model.predict(data[features])

    data = data.sort_values(by="predicted_quantity", ascending=False)

    product_ids = data["product_id"].tolist()
    products = (
        db.query(Product.id, Product.product_name)
        .filter(Product.id.in_(product_ids))
        .all()
    )
    product_info = {p.id: p.product_name for p in products}

    data["product_name"] = data["product_id"].map(product_info)

    return data[["product_id", "product_name", "predicted_quantity"]].head(top_n).to_dict(orient="records")


def prepare_data_for_revenue_prediction(db: Session, year: int, month: int):
    order_count = (
        db.query(func.count(OrderHistory.id))
        .filter(func.extract("year", OrderHistory.order_date) == year)
        .filter(func.extract("month", OrderHistory.order_date) == month)
        .scalar()
    )

    total_quantity_sold = (
        db.query(func.sum(OrderHistoryItems.c.quantity))
        .join(OrderHistory, OrderHistory.id == OrderHistoryItems.c.order_history_id)
        .filter(func.extract("year", OrderHistory.order_date) == year)
        .filter(func.extract("month", OrderHistory.order_date) == month)
        .scalar()
    )

    total_price = (
        db.query(func.sum(OrderHistory.total_price))
        .filter(func.extract("year", OrderHistory.order_date) == year)
        .filter(func.extract("month", OrderHistory.order_date) == month)
        .scalar()
    )
    avg_order_value = total_price / order_count if order_count > 0 else 0

    avg_discount_rate = (
        db.query(func.avg(Product.sale_percent))
        .join(OrderHistoryItems, Product.id == OrderHistoryItems.c.product_id_product_id)
        .join(OrderHistory, OrderHistory.id == OrderHistoryItems.c.order_history_id)
        .filter(func.extract("year", OrderHistory.order_date) == year)
        .filter(func.extract("month", OrderHistory.order_date) == month)
        .scalar()
    )

    data = {
        "order_count": order_count or 0,
        "total_quantity_sold": total_quantity_sold or 0,
        "avg_order_value": avg_order_value or 0,
        "avg_discount_rate": avg_discount_rate or 0,
    }

    return data


def predict_next_month_revenue(db: Session, model, year: int, month: int):
    data = prepare_data_for_revenue_prediction(db, year, month)

    features = [
        data["order_count"],
        data["total_quantity_sold"],
        data["avg_order_value"],
        data["avg_discount_rate"],
    ]
    features = [features]

    predicted_revenue = model.predict(features)

    return predicted_revenue[0]
