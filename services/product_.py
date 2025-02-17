from db.postgresql.db_session import db_session
from db.postgresql.models.product import ProductStockHistory


def get_product_stock_history(id: str):
    stock_history = (
        db_session.session.query(ProductStockHistory).filter_by(product_id=id).all()
    )

    return [
        {
            "in_date": s.date,
            "in_price": s.in_price,
            "in_stock": s.in_stock,
        }
        for s in stock_history
    ]
