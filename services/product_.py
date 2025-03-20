from db.postgresql.db_session import db_session
from db.postgresql.models.product import ProductPriceHistory, ProductStockHistory
from db.postgresql.paging import display_page, paging, Page
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

        content = [
            {
                "in_date": s.date,
                "in_price": s.in_price,
                "in_stock": s.in_stock,
            }
            for s in stock_history
        ]

        count = (
            ss.scalar(
                sqla.select(sqla.func.count(ProductStockHistory.product_id)).filter(
                    ProductStockHistory.product_id == id
                )
            )
            or 0
        )
        return display_page(content, count, pg)


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

        content = [s.to_list_instance() for s in stock_history]

        count = (
            ss.scalar(
                sqla.select(sqla.func.count(ProductPriceHistory.product_id)).filter(
                    ProductPriceHistory.product_id == id
                )
            )
            or 0
        )
        return display_page(content, count, pg)
