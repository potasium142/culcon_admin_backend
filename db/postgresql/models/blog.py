from pgvector.sqlalchemy import Vector
from db.postgresql.models import Base
from sqlalchemy.dialects import postgresql as psql
from sqlalchemy import orm
from db.postgresql.models import product as prod

import sqlalchemy as sqla


class ProductDoc(Base):
    __tablename__: str = "product_doc"
    id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey(prod.Product.id),
        primary_key=True,
    )
    description: orm.Mapped[str] = orm.mapped_column(
        psql.VARCHAR(255),
    )
    images_url: orm.Mapped[list[str]] = orm.mapped_column(
        psql.ARRAY(psql.VARCHAR(255)),
    )
    infos: orm.Mapped[dict[str, str]] = orm.mapped_column(
        psql.JSONB(),
    )
    instructions: orm.Mapped[list[str] | None] = orm.mapped_column(
        psql.ARRAY(psql.VARCHAR(255)),
    )
    article_md: orm.Mapped[str] = orm.mapped_column(psql.TEXT())
    day_before_expiry: orm.Mapped[int]

    product: orm.Mapped[prod.Product] = orm.relationship(back_populates="doc")


class Blog(Base):
    __tablename__: str = "blog"
    id: orm.Mapped[str] = orm.mapped_column(
        psql.VARCHAR(255),
        primary_key=True,
    )
    title: orm.Mapped[str] = orm.mapped_column(
        psql.VARCHAR(255),
    )
    description: orm.Mapped[str] = orm.mapped_column(
        psql.TEXT(),
    )
    article: orm.Mapped[str] = orm.mapped_column(
        psql.TEXT(),
    )
    thumbnail: orm.Mapped[str] = orm.mapped_column(
        psql.VARCHAR(255),
    )
    infos: orm.Mapped[dict[str, str]] = orm.mapped_column(
        psql.JSONB(),
    )
    embed: orm.Mapped["BlogEmbedding"] = orm.relationship(back_populates="doc")


class BlogEmbedding(Base):
    __tablename__: str = "blog_embedding"
    id: orm.Mapped[str] = orm.mapped_column(
        sqla.ForeignKey(Blog.id),
        primary_key=True,
    )
    description_embed: orm.Mapped[Vector] = orm.mapped_column(Vector(768))
    doc: orm.Mapped[Blog] = orm.relationship(back_populates="embed")
