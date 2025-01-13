import re

from numpy import ndarray
from db.mongodb.models.product_doc import ProductDoc
from db.mongodb.models.mealkit_doc import MealkitDoc
from datetime import datetime
from db.postgresql.models import product as prod
from db.postgresql.db_session import db_session
from db.mongodb import db as mongo_session
from io import BytesIO
from dtos.request.product import ProductCreation, MealKitCreation
from ai import clip, yolo
from PIL import Image
from etc.progress_tracker import ProgressTracker
from etc import cloudinary


def read_image(file: bytes) -> Image:
    return Image.open(BytesIO(file))


IMG_DIR = "prod_dir"


def __embed_data(
    yolo_model: yolo.YOLOEmbed,
    clip_model: clip.OpenCLIP,
    description: str,
    additional_images: list[bytes] | None,
    main_image: bytes,
) -> tuple[ndarray, ndarray, ndarray]:
    if additional_images is None:
        images_bytes = []
    else:
        images_bytes = [read_image(f) for f in additional_images]

    images_bytes.append(read_image(main_image))

    description_embed = clip_model.encode_text(description)[0]

    images_embed_clip = clip_model.encode_image(images_bytes)

    images_embed_yolo = yolo_model.embed(images_bytes)

    return description_embed, images_embed_clip, images_embed_yolo


def __upload_images(
    img_dir: str,
    main_image: bytes,
    additional_images: list[bytes],
) -> tuple[str, list[str]]:
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
) -> None:
    pp.update(prog_id, "Embedding data")
    description_embed, images_embed_clip, images_embed_yolo = __embed_data(
        yolo_model,
        clip_model,
        prod_info.description,
        additional_images,
        main_image,
    )
    pp.update(prog_id, "Embedded data")

    product = prod.Product(
        id=prod_id,
        product_name=prod_info.product_name,
        available_quantity=prod_info.available_quantity,
        product_types=prod_info.product_type,
        product_status=prod.ProductStatus.IN_STOCK,
        price=prod_info.price,
        sale_percent=prod_info.sale_percent,
        image_url=main_image_url,
    )

    db_session.session.add(product)

    product_price = prod.ProductPriceHistory(
        price=prod_info.price,
        sale_percent=prod_info.sale_percent,
        date=datetime.now(),
        product_id=prod_id,
    )
    db_session.session.add(product_price)

    product_embedded = prod.ProductEmbedding(
        id=prod_id,
        images_embed_clip=images_embed_clip,
        images_embed_yolo=images_embed_yolo,
        description_embed=description_embed,
    )

    db_session.session.add(product_embedded)

    pp.update(prog_id, "Saved to local database")

    db_session.commit()


def create_product(
    prod_info: ProductCreation,
    additional_images: list[bytes] | None,
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

        pp.update(prog_id, "Uploading images")
        main_image_url, images_url = __upload_images(
            image_dir,
            main_image,
            additional_images,
        )

        __create_general_product(
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
            name=prod_info.product_name,
            description=prod_info.description,
            infos=prod_info.infos,
            images_url=images_url,
            article_md=prod_info.article_md,
            type=prod_info.product_type,
        )

        mongo_session["ProductInfo"].insert_one(
            product_doc.model_dump(
                by_alias=True,
            )
        )
        pp.update(prog_id, "Saved to mongodb")

        pp.complete(prog_id)
    except Exception as e:
        pp.halt(prog_id)
        raise e


def mealkit_creation(
    prod_info: MealKitCreation,
    additional_images: list[bytes] | None,
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

        if (
            db_session.session.query(prod.Product).filter_by(id=prod_id).first()
            is not None
        ):
            raise Exception("Product exist")

        pp.update(prog_id, "Uploading images")
        main_image_url, images_url = __upload_images(
            image_dir,
            main_image,
            additional_images,
        )

        __create_general_product(
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

        product_doc = MealkitDoc(
            id=prod_id,
            name=prod_info.product_name,
            description=prod_info.description,
            infos=prod_info.infos,
            images_url=images_url,
            article_md=prod_info.article_md,
            type=prod_info.product_type,
            ingredients=prod_info.ingredients,
            instructions=prod_info.instructions,
        )

        mongo_session["MealKitInfo"].insert_one(
            product_doc.model_dump(
                by_alias=True,
            )
        )
        pp.update(prog_id, "Saved to mongodb")

        pp.complete(prog_id)
    except Exception as e:
        pp.halt(prog_id)
        raise e
