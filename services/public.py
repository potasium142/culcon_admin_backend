from io import BytesIO
from typing import Any
from PIL import Image, ImageFile
from sqlalchemy import select
from db.postgresql.db_session import db_session
from db.postgresql.models.product import Product, ProductEmbedding
from ai import clip, yolo


def read_image(file: bytes) -> ImageFile.ImageFile:
    return Image.open(BytesIO(file))


def __prod_dto(r: Product) -> dict[str, Any]:
    return {
        "id": r.product.id,
        "product_name": r.product.product_name,
        "available_quantity": r.product.available_quantity,
        "product_types": r.product.product_types,
        "product_status": r.product.product_status,
        "image_url": r.product.image_url,
        "price": r.product.price,
        "sale_percent": r.product.sale_percent,
    }


def vector_search_prompt(
    prompt: str,
    clip_model: clip.OpenCLIP,
):
    prompt_vec = clip_model.encode_text(prompt)[0]
    with db_session.session as ss:
        results = ss.scalars(
            select(ProductEmbedding)
            .order_by(
                ProductEmbedding.description_embed.l2_distance(
                    prompt_vec,
                )
            )
            .limit(142)
        )

        return [__prod_dto(r) for r in results]


def vector_search_image_clip(
    prompt: str,
    clip_model: clip.OpenCLIP,
):
    prompt_vec = clip_model.encode_text(prompt)[0]
    with db_session.session as ss:
        results = ss.scalars(
            select(ProductEmbedding)
            .order_by(
                ProductEmbedding.images_embed_clip.l2_distance(
                    prompt_vec,
                )
            )
            .limit(142)
        )

        return [__prod_dto(r) for r in results]


def vector_search_image_yolo(
    image_bytes: bytes,
    yolo_: yolo.YOLOEmbed,
):
    image = read_image(image_bytes)
    prompt_vec = yolo_.embed(image)[0]
    with db_session.session as ss:
        results = ss.scalars(
            select(ProductEmbedding)
            .order_by(
                ProductEmbedding.images_embed_yolo.l2_distance(
                    prompt_vec,
                )
            )
            .limit(142)
        )

        return [__prod_dto(r) for r in results]
