from io import BytesIO
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
    async with ss.begin():
        img_dir = f"{IMG_DIR}/{prod_id}"
        main_image_url = cloudinary.upload(
            main_image,
            img_dir,
            "main",
        )
        # prod_tcker.update(ProdCrtStg.UPLOAD_IMAGE, 1)

        images_url = [main_image_url]

        for i, img in enumerate(additional_images):
            img_url = cloudinary.upload(
                img,
                img_dir,
                f"{i + 1}",
            )
            images_url.append(img_url)
            # prod_tcker.update(ProdCrtStg.UPLOAD_IMAGE, i + 1)

        product = await ss.get_one(prod.Product, prod_id)

        product.image_url = main_image_url

        product_doc = await ss.get_one(ProductDoc, prod_id)

        product_doc.images_url = images_url

        await ss.flush()


def __create_general_product(
    prod_id: str,
    prod_info: ProductCreation,
    # prod_tcker: ProgressTrackerManager,
):
    # description_embed, images_embed_clip, images_embed_yolo = __embed_data(
    #     yolo_model,
    #     clip_model,
    #     prod_info.description,
    #     main_image,
    #     prod_tcker,
    # )

    product = prod.Product(
        id=prod_id,
        product_name=prod_info.product_name,
        available_quantity=0,
        product_types=prod_info.product_type,
        product_status=prod.ProductStatus.IN_STOCK,
        image_url="",
    )
    # prod_tcker.update(ProdCrtStg.CREATE_PRODUCT, 1)

    # product_embedded = prod.ProductEmbedding(
    #     id=prod_id,
    #     images_embed_clip=images_embed_clip,
    #     images_embed_yolo=images_embed_yolo,
    #     description_embed=description_embed,
    # )

    return product


async def product_creation(
    prod_info: MealKitCreation | ProductCreation,
    additional_images: list[bytes],
    main_image: bytes,
    yolo_model: yolo.YOLOEmbed,
    clip_model: clip.OpenCLIP,
    ss: AsyncSession,
    prog_id: str,
    bg_task: BackgroundTasks,
    # ptm: dict[str, ProgressTrackerManager],
):
    # image_amount = len(additional_images) + 1

    prod_id = prog_id

    is_mealkit = type(prod_info) is MealKitCreation

    # ptm[prod_id] = ProgressTrackerManager(
    #     image_amount,
    #     len(prod_info.ingredients) if is_mealkit else 0,
    # )

    async with ss.begin():
        # try:

        exist = await ss.scalar(
            sqla.select(sqla.exists().where(prod.Product.id == prod_id))
        )

        if exist:
            # ptm[prod_id].halt("Product is already exist")
            raise HandledError("Product is already exists")

        # ptm[prod_id].update(ProdCrtStg.PREPARE, 1)

        product = __create_general_product(
            prod_id=prod_id,
            prod_info=prod_info,
            # main_image=main_image,
            # yolo_model=yolo_model,
            # clip_model=clip_model,
            # prod_tcker=ptm[prod_id],
        )

        product_doc = ProductDoc(
            id=prod_id,
            description=prod_info.description,
            infos=prod_info.infos,
            images_url=[""],
            article_md=prod_info.article_md,
            day_before_expiry=prod_info.day_before_expiry,
        )
        # ptm[prod_id].update(ProdCrtStg.CREATE_DOC, 1)

        if is_mealkit:
            product_doc.instructions = prod_info.instructions or [""]
        else:
            product_doc.instructions = [""]

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

    bg_task.add_task(
        product_create_bg,
        prod_id,
        prod_info,
        additional_images,
        main_image,
        yolo_model,
        clip_model,
        ss,
    )

    return {
        "id": p.id,
        "name": p.product_name,
    }

    # if ptm[prod_id].removable():
    #     del ptm[prod_id]


async def product_create_bg(
    prod_id: str,
    prod_info: MealKitCreation | ProductCreation,
    additional_images: list[bytes],
    main_image: bytes,
    yolo_model: yolo.YOLOEmbed,
    clip_model: clip.OpenCLIP,
    ss: AsyncSession,
):
    await __upload_images(
        prod_id,
        main_image,
        additional_images,
        ss,
        # ptm[prod_id],
    )

    await __embed_data(
        prod_id,
        yolo_model,
        clip_model,
        prod_info.description,
        main_image,
        ss,
    )


async def get_ingredients_list(search: str, pg: Page, ss: AsyncSession):
    async with ss.begin():
        r = await ss.scalars(
            paging(
                sqla.select(prod.Product).filter(
                    prod.Product.product_types != prod.ProductType.MEALKIT,
                    prod.Product.product_name.like(f"%{search}%"),
                ),
                pg,
            )
        )
        count = (
            await ss.scalar(
                sqla.select(
                    sqla.func.count(prod.Product.id).filter(
                        prod.Product.product_types != prod.ProductType.MEALKIT,
                        prod.Product.product_name.like(f"%{search}%"),
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
            }
            for p in r
        ]
    return display_page(content, count, pg)
