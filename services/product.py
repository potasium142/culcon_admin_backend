import re

from db.mongodb.models.product_doc import ProductDoc
from datetime import datetime
from db.postgresql.models import product as prod
from db.postgresql.db_session import db_session
from db.mongodb import db as mongo_session
from io import BytesIO
from fastapi import UploadFile
from dtos.request.product import ProductCreation
from ai import clip, yolo
from PIL import Image
from etc.progress_tracker import ProgressTracker
from etc import cloudinary


def read_image(file: bytes) -> Image:
    return Image.open(BytesIO(file))


IMG_DIR = "prod_dir"


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

        pp.update(prog_id, "Uploading images")

        image_dir = f"{IMG_DIR}/{prod_id}"

        main_image_url = cloudinary.upload(
            main_image,
            image_dir,
            "0",
        )

        images_bytes = []
        images_url = [main_image_url]

        for i, img in enumerate(additional_images):
            img_url = cloudinary.upload(
                img,
                image_dir,
                f"{i + 1}",
            )
            images_url.append(img_url)
            images_bytes.append(read_image(img))

        pp.update(prog_id, "Images uploaded")

        images_bytes.append(read_image(main_image))

        description_embed = clip_model.encode_text(prod_info.description)[0]
        pp.update(prog_id, "Description embed")

        images_embed_clip = clip_model.encode_image(images_bytes)
        pp.update(prog_id, "Images embed [CLIP]")

        images_embed_yolo = yolo_model.embed(images_bytes)
        pp.update(prog_id, "Images embed [YOLO]")

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

        pp.update(prog_id, "Saved to local database")

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

        pp.update(prog_id, "Saved to local mongodb")

        pp.complete(prog_id)
    except Exception as e:
        pp.halt(prog_id)
        raise e
