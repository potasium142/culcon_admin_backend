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
    main_image: bytes,
) -> tuple[ndarray, ndarray, ndarray]:
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
            if product_doc is MealKitCreation:
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
        prod_doc.instructions = prod_info.instructions

        for ing in prod_info.ingredients:
            ingredient = prod.MealkitIngredients(
                mealkit_id=prod_id,
                ingredient=ing,
            )
            db_session.session.add(ingredient)

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


def restock_product(
    prod_id: str,
    amount: int,
    import_price: float,
):
    product: prod.Product = db_session.session.get(prod.Product, prod_id)

    if not product:
        raise Exception("Product not found")

    product_stock = prod.ProductStockHistory(
        product_id=product.id,
        date=datetime.now(),
        in_price=import_price,
        in_stock=amount,
    )
    product.available_quantity = amount
    product.product_status = prod.ProductStatus.IN_STOCK

    db_session.session.add(product_stock)
    db_session.commit()

    return (
        db_session.session.query(prod.ProductStockHistory)
        .filter_by(product_id=product.id)
        .order_by(prod.ProductStockHistory.date.desc())
        .first()
    )


def update_status(
    prod_id: str,
    status: prod.ProductStatus,
):
    product: prod.Product = db_session.session.get(prod.Product, prod_id)

    if not product:
        raise Exception("Product not found")

    product.product_status = status

    db_session.commit()


def get_list_mealkit():
    with db_session.session as session:
        products: list[prod.Product] = (
            session.query(prod.Product)
            .filter_by(product_types=prod.ProductType.MEALKIT)
            .all()
        )

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


def get_list_product():
    with db_session.session as session:
        products: list[prod.Product] = session.query(prod.Product).all()

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
    with db_session.session as session:
        product: prod.Product = session.get(prod.Product, prod_id)
        product_price: list[prod.ProductPriceHistory] = (
            session.query(prod.ProductPriceHistory).filter_by(product_id=prod_id).all()
        )

        product_doc = session.get(ProductDoc, prod_id)

        if not product:
            raise Exception("Product not found")
        if not product_doc:
            raise Exception("Product doc not found")

        base_info = {
            "id": product.id,
            "product_name": product.product_name,
            "description": product_doc.description,
            "available_quantity": product.available_quantity,
            "product_type": product.product_types,
            "product_status": product.product_status,
            "price_list": [price.to_list_instance() for price in product_price],
            "info": product_doc.infos,
            "images_url": product_doc.images_url,
            "article": product_doc.article_md,
            "day_before_expiry": product_doc.day_before_expiry,
        }

        if product_doc.ingredients and product_doc.instructions:
            base_info["instructions"] = product_doc.instructions
            base_info["ingredients"] = product_doc.ingredients

        return base_info
