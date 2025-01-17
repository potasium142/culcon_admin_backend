import re

from numpy import ndarray
from db.postgresql.models.blog import ProductDoc
from datetime import datetime
from db.postgresql.models import product as prod
from db.postgresql.db_session import db_session
from io import BytesIO
from dtos.request.product import (
    ProductCreation,
    MealKitCreation,
    ProductUpdate,
    MealKitUpdate,
)
from ai import clip, yolo
from PIL import Image, ImageFile
from etc.progress_tracker import ProgressTracker
from etc import cloudinary


def read_image(file: bytes) -> ImageFile.ImageFile:
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
) -> None:
    embed_task_id = pp.new_subtask(prog_id, "Embedding")
    description_embed, images_embed_clip, images_embed_yolo = __embed_data(
        yolo_model,
        clip_model,
        prod_info.description,
        additional_images,
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

    db_session.commit()

    pp.close_subtask(prog_id, save_db_task)


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

        if (
            db_session.session.query(prod.Product).filter_by(id=prod_id).first()
            is not None
        ):
            raise Exception("Product exist")

        main_image_url, images_url = __upload_images(
            image_dir,
            main_image,
            additional_images,
            pp,
            prog_id,
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
            description=prod_info.description,
            infos=prod_info.infos,
            images_url=images_url,
            article_md=prod_info.article_md,
            day_before_expiry=prod_info.day_before_expiry,
        )

        match prod_info:
            case MealKitCreation():
                product_doc.ingredients = prod_info.ingredients
                product_doc.instructions = prod_info.instructions

        db_session.session.add(product_doc)

        pp.complete(
            prog_id,
            {"product_id": prod_id},
        )
        db_session.commit()
    except Exception as e:
        pp.halt(prog_id, str(e))


def update_info(
    prod_id: str,
    prod_info: ProductUpdate | MealKitUpdate,
) -> None:
    prod_doc = db_session.session.get(ProductDoc, prod_id)

    if not prod_doc:
        raise Exception("Product doc not found")

    prod_doc.day_before_expiry = prod_info.day_before_expiry
    prod_doc.description = prod_info.description
    prod_doc.article_md = prod_info.article_md
    prod_doc.infos = prod_info.infos

    if type(prod_info) is MealKitUpdate:
        prod_doc.ingredients = prod_info.ingredients
        prod_doc.instructions = prod_info.instructions

    db_session.commit()


def update_price(
    prod_id: str,
    price: float,
    sale_percent: float,
):
    product_price = prod.ProductPriceHistory(
        price=price,
        sale_percent=sale_percent,
        date=datetime.now(),
        product_id=prod_id,
    )

    db_session.session.add(product_price)

    product: prod.Product = db_session.session.get(prod.Product, prod_id)

    if not product:
        raise Exception("Product not found")

    product.price = price
    product.sale_percent = sale_percent

    db_session.commit()


def update_quantity(
    prod_id: str,
    amount: int,
):
    product: prod.Product = db_session.session.get(prod.Product, prod_id)

    if not product:
        raise Exception("Product not found")

    product.available_quantity = amount
    product.product_status = prod.ProductStatus.IN_STOCK

    db_session.commit()


def update_status(
    prod_id: str,
    status: prod.ProductStatus,
):
    product: prod.Product = db_session.session.get(prod.Product, prod_id)

    if not product:
        raise Exception("Product not found")

    product.product_status = status

    db_session.commit()


def get_list_product():
    products: list[prod.Product] = db_session.session.query(prod.Product).all()

    rtn_products: list[
        dict[str, str | float | int | prod.ProductStatus | prod.ProductType]
    ] = list(
        map(
            lambda prod: {
                "id": prod.id,
                "name": prod.product_name,
                "price": prod.price,
                "type": prod.product_types,
                "status": prod.product_status,
                "image_url": prod.image_url,
                "available_quantity": prod.available_quantity,
            },
            products,
        )
    )

    return rtn_products


def get_product(prod_id: str):
    product: prod.Product = db_session.session.get(prod.Product, prod_id)
    product_price: list[prod.ProductPriceHistory] = (
        db_session.session.query(prod.ProductPriceHistory)
        .filter_by(product_id=prod_id)
        .all()
    )

    product_doc = db_session.session.get(ProductDoc, prod_id)

    if not product:
        raise Exception("Product not found")
    if not product_doc:
        raise Exception("Product doc not found")

    base_info = {
        "id": product.id,
        "product_name": product.product_name,
        "available_quantity": product.available_quantity,
        "product_type": product.product_types,
        "product_status": product.product_status,
        "price_list": [price.to_list_instance() for price in product_price],
        "info": product_doc.infos,
        "images_url": product_doc.images_url,
        "article": product_doc.article_md,
    }

    if product_doc.ingredients and product_doc.instructions:
        base_info["instructions"] = product_doc.instructions
        base_info["ingredients"] = product_doc.ingredients

    return base_info
