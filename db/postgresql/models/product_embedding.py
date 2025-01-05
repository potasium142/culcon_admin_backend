from pgvector.sqlalchemy import Vector

import sqlalchemy as sqla
from sqlalchemy import orm
from sqlalchemy.dialects import postgresql

from db.postgresql.models import Base
from db.postgresql.models.product import Product


class ProductEmbedding(Base):
    __tablename__: str = "product_embedding"
    id: orm.Mapped[Product] = orm.mapped_column(
        sqla.ForeignKey(Product.id), primary_key=True
    )
    images_embed: orm.Mapped[list[Vector]] = orm.mapped_column(
        postgresql.ARRAY(Vector(512))
    )
