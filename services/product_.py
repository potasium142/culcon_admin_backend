from datetime import datetime
from io import BytesIO
import re
from PIL import Image, ImageFile
from ai import clip, yolo
from db.postgresql.db_session import db_session
from db.postgresql.models.blog import ProductDoc
import db.postgresql.models.product as prod
import sqlalchemy as sqla

from dtos.request.product import MealKitCreation, ProductCreation
from etc import cloudinary
from etc.local_error import HandledError
from etc.progress_tracker import ProgressTracker


def read_image(file: bytes) -> ImageFile.ImageFile:
    return Image.open(BytesIO(file))


IMG_DIR = "prod_dir"


def __embed_data(
    yolo_model: yolo.YOLOEmbed,
    clip_model: clip.OpenCLIP,
    description: str,
    main_image: bytes,
):
    images_bytes = [read_image(main_image)]

    description_embed = clip_model.encode_text(description)[0]

    images_embed_clip = clip_model.encode_image(images_bytes)[0]

    images_embed_yolo = yolo_model.embed(images_bytes)[0]

    return description_embed, images_embed_clip, images_embed_yolo


def __upload_images(
    img_dir: str,
    main_image: bytes,
    additional_images: list[bytes],
    pp: ProgressTracker,
    prog_id: int,
) -> tuple[str, list[str]]:
    upload_img_task = pp.new_subtask(prog_id, "Upload image")
    main_image_url = cloudinary.upload(
        main_image,
        img_dir,
        "main",
    )

    images_url = [main_image_url]

    for i, img in enumerate(additional_images):
        img_url = cloudinary.upload(
            img,
            img_dir,
            f"{i + 1}",
        )
        images_url.append(img_url)
        pp.update_subtask(
            prog_id,
            upload_img_task,
            progress=i,
        )

    pp.close_subtask(prog_id, upload_img_task)
    return main_image_url, images_url


def __create_general_product(
    prod_id: str,
    prod_info: ProductCreation,
    additional_images: list[bytes] | None,
    main_image: bytes,
    main_image_url: str,
    yolo_model: yolo.YOLOEmbed,
    clip_model: clip.OpenCLIP,
    pp: ProgressTracker,
    prog_id: int,
):
    embed_task_id = pp.new_subtask(prog_id, "Embedding")
    description_embed, images_embed_clip, images_embed_yolo = __embed_data(
        yolo_model,
        clip_model,
        prod_info.description,
        main_image,
    )
    pp.close_subtask(
        prog_id,
        embed_task_id,
    )

    save_db_task = pp.new_subtask(prog_id, "Save to db")
    product = prod.Product(
        id=prod_id,
        product_name=prod_info.product_name,
        available_quantity=0,
        product_types=prod_info.product_type,
        product_status=prod.ProductStatus.IN_STOCK,
        price=prod_info.price,
        sale_percent=prod_info.sale_percent,
        image_url=main_image_url,
    )

    product_price = prod.ProductPriceHistory(
        price=prod_info.price,
        sale_percent=prod_info.sale_percent,
        date=datetime.now(),
        product_id=prod_id,
    )

    product_embedded = prod.ProductEmbedding(
        id=prod_id,
        images_embed_clip=images_embed_clip,
        images_embed_yolo=images_embed_yolo,
        description_embed=description_embed,
    )

    pp.close_subtask(prog_id, save_db_task)

    return product, product_price, product_embedded


def product_creation(
    prod_info: MealKitCreation | ProductCreation,
    additional_images: list[bytes],
    main_image: bytes,
    yolo_model: yolo.YOLOEmbed,
    clip_model: clip.OpenCLIP,
    pp: ProgressTracker,
    prog_id: int,
) -> None:
    try:
        name = re.sub(r"\s+", "", prod_info.product_name)
        prod_id = f"{prod_info.product_type}_{name}"
        image_dir = f"{IMG_DIR}/{prod_id}"

        if db_session.session.get(prod.Product, prod_id) is not None:
            raise HandledError("Product exist")

        main_image_url, images_url = __upload_images(
            image_dir,
            main_image,
            additional_images,
            pp,
            prog_id,
        )

        product, product_price, product_embedded = __create_general_product(
            prod_id=prod_id,
            prod_info=prod_info,
            additional_images=additional_images,
            main_image=main_image,
            main_image_url=main_image_url,
            yolo_model=yolo_model,
            clip_model=clip_model,
            pp=pp,
            prog_id=prog_id,
        )

        product_doc = ProductDoc(
            id=prod_id,
            description=prod_info.description,
            infos=prod_info.infos,
            images_url=images_url,
            article_md=prod_info.article_md,
            day_before_expiry=prod_info.day_before_expiry,
        )

        with db_session.session as ss:
            if type(prod_info) is MealKitCreation:
                product_doc.instructions = prod_info.instructions

                for ing in prod_info.ingredients:
                    ingredient = prod.MealkitIngredients(
                        mealkit_id=prod_id,
                        ingredient=ing,
                    )
                    ss.add(ingredient)

            product.doc = product_doc

            ss.add(product)
            ss.add(product_price)
            ss.add(product_embedded)

            ss.commit()

        pp.complete(
            prog_id,
            {"product_id": prod_id},
        )
    except Exception as e:
        pp.halt(prog_id, str(e))
