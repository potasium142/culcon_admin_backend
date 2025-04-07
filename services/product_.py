from io import BytesIO
import logging
import re
from PIL import Image, ImageFile
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from ai import clip, yolo
from db.postgresql.models.blog import ProductDoc
import db.postgresql.models.product as prod
import sqlalchemy as sqla

from db.postgresql.paging import Page, display_page, paging
from dtos.request.product import MealKitCreation, ProductCreation
from etc import cloudinary
from etc.local_error import HandledError
# from etc.prog_tracker import ProdCrtStg, ProgressTrackerManager


def read_image(file: bytes) -> ImageFile.ImageFile:
    return Image.open(BytesIO(file))


IMG_DIR = "prod_dir"

logger = logging.getLogger("uvicorn.info")

prod_regex = re.compile(r"^[A-Za-z0-9 ]+$")


async def __embed_data(
    prod_id: str,
    yolo_model: yolo.YOLOEmbed,
    clip_model: clip.OpenCLIP,
    description: str,
    main_image: bytes,
    ss: AsyncSession,
    # prod_tcker: ProgressTrackerManager,
):
    async with ss.begin():
        images_bytes = [read_image(main_image)]

        description_embed = clip_model.encode_text(description)[0]
        # prod_tcker.update(ProdCrtStg.EMBED_DATA, 1)

        images_embed_clip = clip_model.encode_image(images_bytes)[0]
        # prod_tcker.update(ProdCrtStg.EMBED_DATA, 2)

        images_embed_yolo = yolo_model.embed(images_bytes)[0]
        # prod_tcker.update(ProdCrtStg.EMBED_DATA, 3)

        product_embedded = prod.ProductEmbedding(
            id=prod_id,
            images_embed_clip=images_embed_clip,
            images_embed_yolo=images_embed_yolo,
            description_embed=description_embed,
        )

        ss.add(product_embedded)
        await ss.flush()


async def __upload_images(
    prod_id: str,
    main_image: bytes,
    additional_images: list[bytes],
    ss: AsyncSession,
    # prod_tcker: ProgressTrackerManager,
):
    logger.info(f"Being upload image of product : {prod_id}")
    async with ss.begin():
        img_dir = f"{IMG_DIR}/{prod_id}"
        main_image_url = cloudinary.upload(
            main_image,
            img_dir,
            f"main_{prod_id}",
        )
        # prod_tcker.update(ProdCrtStg.UPLOAD_IMAGE, 1)

        images_url = [main_image_url]

        for i, img in enumerate(additional_images):
            img_url = cloudinary.upload(
                img,
                img_dir,
                f"{i + 1}_{prod_id}",
            )
            images_url.append(img_url)
            # prod_tcker.update(ProdCrtStg.UPLOAD_IMAGE, i + 1)

        product = await ss.get_one(prod.Product, prod_id)

        logger.info(f"Writing image to product: {product.id}")

        product.image_url = main_image_url

        product_doc = await ss.get_one(ProductDoc, prod_id)

        logger.info(f"Writing additional images to product doc: {product_doc.id}")
        product_doc.images_url = images_url

        await ss.flush()


def __create_general_product(
    prod_id: str,
    prod_info: ProductCreation,
):
    product = prod.Product(
        id=prod_id,
        product_name=prod_info.product_name,
        available_quantity=0,
        product_types=prod_info.product_type,
        product_status=prod.ProductStatus.OUT_OF_STOCK,
        image_url="",
    )

    return product


async def product_creation(
    prod_info: MealKitCreation | ProductCreation,
    additional_images: list[bytes],
    main_image: bytes,
    yolo_model: yolo.YOLOEmbed,
    clip_model: clip.OpenCLIP,
    ss: AsyncSession,
    bg_task: BackgroundTasks,
):
    valid_name = prod_regex.match(prod_info.product_name)

    if not valid_name:
        raise HandledError("Product name is not valid")

    prod_id = re.sub(r"\s+", "", prod_info.product_name)

    is_mealkit = type(prod_info) is MealKitCreation

    async with ss.begin():
        exist = await ss.scalar(
            sqla.select(sqla.exists().where(prod.Product.id == prod_id))
        )

        if exist:
            raise HandledError("Product is already exists")

        product = __create_general_product(
            prod_id=prod_id,
            prod_info=prod_info,
        )

        product_doc = ProductDoc(
            id=prod_id,
            description=prod_info.description,
            infos=prod_info.infos,
            images_url=[""],
            article_md=prod_info.article_md,
            day_before_expiry=prod_info.day_before_expiry,
            instructions=prod_info.instructions,
        )

        ss.add(product)
        ss.add(product_doc)
        # ss.add(product_embedded)

        await ss.flush()

        if is_mealkit:
            for i, (ing, amt) in enumerate(prod_info.ingredients.items()):
                ingredient = prod.MealkitIngredients(
                    mealkit_id=prod_id,
                    ingredient=ing,
                    amount=amt,
                )
                ss.add(ingredient)

                # ptm[prod_id].update(ProdCrtStg.SAVING_INGREDIENT, i)

        await ss.flush()

        p = await ss.get_one(prod.Product, prod_id)

        # ptm[prod_id].done()

    # except Exception as e:
    #     ptm[prod_id].halt(e.__str__())

    logger.info(f"Running backgroud task for product : {prod_id}")
    bg_task.add_task(
        __upload_images,
        prod_id,
        main_image,
        additional_images,
        ss,
        # ptm[prod_id],
    )

    bg_task.add_task(
        __embed_data,
        prod_id,
        yolo_model,
        clip_model,
        prod_info.description,
        main_image,
        ss,
    )

    return {
        "id": p.id,
        "name": p.product_name,
    }

    # if ptm[prod_id].removable():
    #     del ptm[prod_id]


async def get_ingredients_list(search: str, pg: Page, ss: AsyncSession):
    async with ss.begin():
        r = await ss.scalars(
            paging(
                sqla.select(prod.Product).filter(
                    prod.Product.product_types != prod.ProductType.MEALKIT,
                    prod.Product.product_name.ilike(f"%{search}%"),
                ),
                pg,
            )
        )
        count = (
            await ss.scalar(
                sqla.select(
                    sqla.func.count(prod.Product.id).filter(
                        prod.Product.product_types != prod.ProductType.MEALKIT,
                        prod.Product.product_name.ilike(f"%{search}%"),
                    )
                )
            )
            or 0
        )
        content = [
            {
                "id": p.id,
                "name": p.product_name,
                "price": p.price,
                "sale_percent": p.sale_percent,
                "stock": p.available_quantity,
                "type": p.product_types,
                "image": p.image_url,
            }
            for p in r
        ]
    return display_page(content, count, pg)
