from db.postgresql.db_session import db_session
from db.postgresql.models.product import ProductPriceHistory, ProductStockHistory
from db.postgresql.paging import paging, Page
import sqlalchemy as sqla


def get_product_stock_history(id: str, pg: Page):
    with db_session.session as ss:
        stock_history = ss.scalars(
            paging(
                sqla.select(ProductStockHistory).filter(
                    ProductStockHistory.product_id == id
                ),
                pg,
            )
        )

        return [
            {
                "in_date": s.date,
                "in_price": s.in_price,
                "in_stock": s.in_stock,
            }
            for s in stock_history
        ]


def get_product_price_history(id: str, pg: Page):
    with db_session.session as ss:
        stock_history = ss.scalars(
            paging(
                sqla.select(ProductPriceHistory).filter(
                    ProductPriceHistory.product_id == id
                ),
                pg,
            )
        )

        return [s.to_list_instance() for s in stock_history]
