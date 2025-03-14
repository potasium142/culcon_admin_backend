from io import BytesIO
from typing import Any
from PIL import Image, ImageFile
from db.postgresql.db_session import db_session
from db.postgresql.models.product import Product, ProductEmbedding, ProductType
from ai import clip, yolo


def read_image(file: bytes) -> ImageFile.ImageFile:
    return Image.open(BytesIO(file))


def __prod_dto(r: tuple[Product, float, float]) -> dict[str, Any]:
    return {
        "id": r[0].product.id,
        "product_name": r[0].product.product_name,
        "available_quantity": r[0].product.available_quantity,
        "product_types": r[0].product.product_types,
        "product_status": r[0].product.product_status,
        "image_url": r[0].product.image_url,
        "price": r[0].product.price,
        "sale_percent": r[0].product.sale_percent,
        "dist_1": r[1],
        "dist_2": r[2],
    }


def vector_search_prompt(
    prompt: str,
    clip_model: clip.OpenCLIP,
):
    prompt_vec = clip_model.encode_text(prompt)[0]
    with db_session.session as ss:
        dist_text = ProductEmbedding.description_embed.l2_distance(prompt_vec)
        dist_img = ProductEmbedding.images_embed_clip.l2_distance(prompt_vec)
        results = (
            ss.query(
                ProductEmbedding,
                dist_text,
                dist_img,
            )
            .filter(
                (dist_img < 0.8) | (dist_text < 0.8),
            )
            .limit(70)
        )

        return [__prod_dto(r) for r in results]


def vector_search_image_yolo(
    image_bytes: bytes,
    yolo_: yolo.YOLOEmbed,
    clip_model: clip.OpenCLIP,
):
    image = [read_image(image_bytes)]
    prompt_vec = yolo_.embed(image)[0]
    clip_vec = clip_model.encode_image(image)[0]
    with db_session.session as ss:
        dist_img_yolo = ProductEmbedding.images_embed_yolo.l2_distance(prompt_vec)
        dist_img_clip = ProductEmbedding.images_embed_clip.l2_distance(clip_vec)
        results = (
            ss.query(
                ProductEmbedding,
                dist_img_clip,
                dist_img_yolo,
            )
            .filter((dist_img_yolo < 1.4))
            .limit(70)
        )

        r_results: list[dict[str, str | float]] = []

        for r in results:
            if r[0].product.product_types != ProductType.MEALKIT:
                continue
            r_results.append(__prod_dto(r))

        return r_results
