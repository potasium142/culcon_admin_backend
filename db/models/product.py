from datetime import datetime
from enum import Enum

import sqlalchemy as sqla
from sqlalchemy import orm
from sqlalchemy.sql import sqltypes

from db.models import Base


class ProductType(Enum):
    VEGETABLE = 1
    MEAT = 2
    SEASON = 3
    MEALKIT = 4


class ProductStatus(Enum):
    IN_STOCK = 1
    OUT_OF_STOCK = 2
    NO_LONGER_IN_SALE = 3


class Product(Base):
    __tablename__: str = "product"
    id: orm.Mapped[str] = orm.mapped_column(sqltypes.VARCHAR(255), primary_key=True)
    product_name: orm.Mapped[str]
    available_quantity: orm.Mapped[int]
    product_type: orm.Mapped[ProductType]
    image_url: orm.Mapped[str]
    price: orm.Mapped[float] = orm.mapped_column(sqltypes.REAL)
    sale_percent: orm.Mapped[float] = orm.mapped_column(sqltypes.REAL)
    product_price: orm.Mapped[list["ProductPriceHistory"]] = orm.relationship()


class ProductPriceHistory(Base):
    __tablename__: str = "product_price_history"
    price: orm.Mapped[float] = orm.mapped_column(sqltypes.REAL)
    sale_percent: orm.Mapped[float] = orm.mapped_column(sqltypes.REAL)
    date: orm.Mapped[datetime] = orm.mapped_column(sqltypes.TIMESTAMP)
    product_id: orm.Mapped[str] = orm.mapped_column(sqla.ForeignKey("product.id"))
