from datetime import datetime
from enum import Enum
from typing import Any

import sqlalchemy as sqla
from sqlalchemy import orm
from sqlalchemy.sql import sqltypes

from db.postgresql.models import Base

from pgvector.sqlalchemy import Vector


class ProductType(str, Enum):
    VEGETABLE = "VEG"
    MEAT = "MEAT"
    SEASON = "SS"
    MEALKIT = "MK"


class ProductStatus(str, Enum):
    IN_STOCK = "IN_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    NO_LONGER_IN_SALE = "NO_LONGER_IN_SALE"


class Product(Base):
    __tablename__: str = "product"
    id: orm.Mapped[str] = orm.mapped_column(
        sqltypes.VARCHAR(255),
        primary_key=True,
    )
    product_name: orm.Mapped[str]
    available_quantity: orm.Mapped[int]
    product_types: orm.Mapped[ProductType]
    product_status: orm.Mapped[ProductStatus]
    image_url: orm.Mapped[str]
    price: orm.Mapped[float] = orm.mapped_column(sqltypes.REAL)
    sale_percent: orm.Mapped[float] = orm.mapped_column(sqltypes.REAL)
    embed: orm.Mapped["ProductEmbedding"] = orm.relationship(
        back_populates="product",
    )
    doc: orm.Mapped["ProductDoc"] = orm.relationship(
        back_populates="product",
    )


class ProductPriceHistory(Base):
    __tablename__: str = "product_price_history"
    price: orm.Mapped[float] = orm.mapped_column(sqltypes.REAL)
    sale_percent: orm.Mapped[float] = orm.mapped_column(sqltypes.REAL)
    date: orm.Mapped[datetime] = orm.mapped_column(
        sqltypes.TIMESTAMP,
        primary_key=True,
    )
    product_id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey("product.id"),
        primary_key=True,
    )
    __table_args__ = (
        sqla.UniqueConstraint(
            "date",
            "product_id",
            name="product_price_history_pk",
        ),
    )

    def to_list_instance(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "price": self.price,
            "sale_percent": self.sale_percent,
        }


class MealkitIngredients(Base):
    __tablename__: str = "mealkit_ingredients"
    mealkit_id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey(Product.id),
        primary_key=True,
    )
    ingredient: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey(Product.id),
        primary_key=True,
    )


class ProductEmbedding(Base):
    __tablename__: str = "product_embedding"
    id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey(Product.id),
        primary_key=True,
    )
    images_embed_yolo: orm.Mapped[Vector] = orm.mapped_column(Vector(512))
    images_embed_clip: orm.Mapped[Vector] = orm.mapped_column(Vector(768))
    description_embed: orm.Mapped[Vector] = orm.mapped_column(Vector(768))
    product: orm.Mapped[Product] = orm.relationship(back_populates="embed")


class ProductStockHistory(Base):
    __tablename__: str = "product_stock_history"
    product_id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey(Product.id),
        primary_key=True,
    )
    date: orm.Mapped[datetime] = orm.mapped_column(
        sqltypes.TIMESTAMP,
        primary_key=True,
    )
    in_price: orm.Mapped[float] = orm.mapped_column(
        sqltypes.REAL,
    )
    in_stock: orm.Mapped[int]

    __table_args__ = (
        sqla.UniqueConstraint(
            "date",
            "product_id",
            name="product_stock_history_pk",
        ),
    )
