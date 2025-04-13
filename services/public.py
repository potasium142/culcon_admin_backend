from io import BytesIO
from typing import Any
from PIL import Image, ImageFile
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgresql.models.blog import Blog, BlogEmbedding
from db.postgresql.models.product import Product, ProductEmbedding, ProductType
from ai import clip, yolo
import sqlalchemy as sqla
from db.postgresql.paging import Page, display_page, paging
from etc.local_error import HandledError


def read_image(file: bytes) -> ImageFile.ImageFile:
    return Image.open(BytesIO(file))


async def __prod_dto(r) -> dict[str, Any]:
    product: Product = await r[0].awaitable_attrs.product
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
    type: ProductType | None,
    pg: Page,
    ss: AsyncSession,
    text_dist: float = 0.5,
    img_dist: float = 0.8,
):
    if type:
        filters = [ProductEmbedding.id.like(f"{type}%")]
    else:
        filters = []
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
                )
                .filter(
                    (dist_img < img_dist) | (dist_text < text_dist),
                    *filters,
                )
                .order_by(dist_text, dist_img)
                .limit(70),
                pg,
            )
        )

        count = (
            await ss.scalar(
                sqla.select(sqla.func.count(ProductEmbedding.id))
                .filter(
                    (dist_img < img_dist) | (dist_text < text_dist),
                    *filters,
                )
                .limit(70),
            )
            or 0
        )

        content = []

        for r in results.all():
            content.append(await __prod_dto(r))

    return display_page(content, count, pg)


async def vector_search_image_yolo(
    image_bytes: bytes,
    yolo_: yolo.YOLOEmbed,
    clip_model: clip.OpenCLIP,
    type: ProductType | None,
    pg: Page,
    ss: AsyncSession,
    yolo_dist: float = 1.4,
    clip_dist: float = 0.5,
):
    image = [read_image(image_bytes)]
    yp = yolo_.predict(image)[0].summary()[0]
    prompt_vec = yolo_.embed(image)[0]
    clip_vec = clip_model.encode_image(image)[0]

    if type:
        filters = [ProductEmbedding.id.like(f"{type}%")]
    else:
        filters = []

    predict_result = {
        "name": yp["name"],
        "confidence": f"{yp['confidence'] * 100:2.2f}",
    }

    async with ss.begin():
        dist_img_yolo = ProductEmbedding.images_embed_yolo.l2_distance(prompt_vec)
        dist_img_clip = ProductEmbedding.images_embed_clip.l2_distance(clip_vec)
        results = await ss.execute(
            paging(
                sqla.select(
                    ProductEmbedding,
                    dist_img_yolo,
                    dist_img_clip,
                )
                .filter(
                    (dist_img_yolo < yolo_dist) | (dist_img_clip < clip_dist),
                    *filters,
                )
                .order_by(dist_img_clip, dist_img_yolo)
                .limit(70),
                pg,
            )
        )

        content: list[dict[str, str | float]] = []

        for r in results.all():
            content.append(await __prod_dto(r))

        count = (
            await ss.scalar(
                sqla.select(sqla.func.count(ProductEmbedding.id))
                .filter(
                    (dist_img_yolo < yolo_dist) | (dist_img_clip < clip_dist),
                    *filters,
                )
                .limit(70),
            )
            or 0
        )

    page_content = display_page(content, count, pg)

    return {"predict": predict_result, "page": page_content}


async def vector_search_blog(
    prompt: str,
    clip_model: clip.OpenCLIP,
    pg: Page,
    ss: AsyncSession,
    text_dist: float = 0.5,
):
    async with ss.begin():
        prompt_vec = clip_model.encode_text(prompt)[0]
        dist_text = BlogEmbedding.description_embed.l2_distance(prompt_vec)
        results = await ss.execute(
            paging(
                sqla.select(
                    BlogEmbedding,
                    Blog.id,
                    Blog.title,
                    Blog.description,
                    Blog.thumbnail,
                    dist_text,
                )
                .filter(
                    (dist_text < text_dist),
                )
                .order_by(dist_text)
                .join(Blog, Blog.id == BlogEmbedding.id),
                pg,
            )
        )

        count = (
            await ss.scalar(
                sqla.select(sqla.func.count(BlogEmbedding.id)).filter(
                    (dist_text < text_dist),
                )
            )
            or 0
        )

        content = []

        for r in results.all():
            content.append({
                "id": r[1],
                "title": r[2],
                "description": r[3],
                "thumbnail": r[4],
                "dist_text": r[5],
            })

    return display_page(content, count, pg)
