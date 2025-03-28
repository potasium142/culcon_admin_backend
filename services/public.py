from io import BytesIO
from typing import Any
from PIL import Image, ImageFile
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgresql.models.product import Product, ProductEmbedding, ProductType
from ai import clip, yolo
import sqlalchemy as sqla
from db.postgresql.paging import Page, display_page, paging
from etc.local_error import HandledError


def read_image(file: bytes) -> ImageFile.ImageFile:
    return Image.open(BytesIO(file))


async def __prod_dto(r, product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "product_name": product.product_name,
        "available_quantity": product.available_quantity,
        "product_types": product.product_types,
        "product_status": product.product_status,
        "image_url": product.image_url,
        "price": product.price,
        "sale_percent": product.sale_percent,
        "dist_1": r[1],
        "dist_2": r[2],
    }


async def vector_search_prompt(
    prompt: str,
    clip_model: clip.OpenCLIP,
    pg: Page,
    ss: AsyncSession,
):
    async with ss.begin():
        prompt_vec = clip_model.encode_text(prompt)[0]
        dist_text = ProductEmbedding.description_embed.l2_distance(prompt_vec)
        dist_img = ProductEmbedding.images_embed_clip.l2_distance(prompt_vec)
        results = await ss.execute(
            paging(
                sqla.select(
                    ProductEmbedding,
                    dist_text,
                    dist_img,
                ).filter(
                    (dist_img < 0.8) | (dist_text < 0.5),
                ),
                pg,
            )
        )

        count = (
            await ss.scalar(
                sqla.select(sqla.func.count(ProductEmbedding.id)).filter(
                    (dist_img < 0.8) | (dist_text < 0.5),
                )
            )
            or 0
        )

        content = []

        for r in results.all():
            product = await ss.get(Product, r[0].id)
            if not product:
                raise HandledError(f"Product {r[0].id} not found")
            content.append(await __prod_dto(r, product))

    return display_page(content, count, pg)


async def vector_search_image_yolo(
    image_bytes: bytes,
    yolo_: yolo.YOLOEmbed,
    clip_model: clip.OpenCLIP,
    pg: Page,
    ss: AsyncSession,
):
    image = [read_image(image_bytes)]
    prompt_vec = yolo_.embed(image)[0]
    clip_vec = clip_model.encode_image(image)[0]
    async with ss.begin():
        dist_img_yolo = ProductEmbedding.images_embed_yolo.l2_distance(prompt_vec)
        dist_img_clip = ProductEmbedding.images_embed_clip.l2_distance(clip_vec)
        results = await ss.execute(
            paging(
                sqla.select(
                    ProductEmbedding,
                    dist_img_yolo,
                    dist_img_clip,
                ).filter(dist_img_yolo < 1.4),
                pg,
            )
        )

        content: list[dict[str, str | float]] = []

        for r in results:
            product = await ss.get(Product, r[0].id)
            if not product:
                raise HandledError(f"Product {r[0].id} not found")
            if product.product_types != ProductType.MEALKIT:
                continue
            content.append(await __prod_dto(r, product))

        count = (
            await ss.scalar(
                sqla.select(sqla.func.count(ProductEmbedding.id)).filter(
                    dist_img_yolo < 1.4
                )
            )
            or 0
        )

    return display_page(content, count, pg)
