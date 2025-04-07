from typing import Any

import sqlalchemy as sqla
from sqlalchemy.ext.asyncio import AsyncSession
from ai.clip import OpenCLIP
from db.postgresql.models.blog import ProductDoc
from datetime import datetime
from db.postgresql.models import product as prod
from db.postgresql.models.order_history import OrderHistoryItems
from db.postgresql.models.order_history import OrderHistory
from dtos.request.product import (
    ProductUpdate,
    MealKitUpdate,
)
from etc.local_error import HandledError
from sqlalchemy import func
from db.postgresql.paging import Page, display_page, paging, table_size


async def update_info(
    prod_id: str,
    prod_info: ProductUpdate | MealKitUpdate,
    clip_model: OpenCLIP,
    ss: AsyncSession,
):
    async with ss.begin():
        prod_doc = await ss.get_one(ProductDoc, prod_id)

        prod_doc.day_before_expiry = prod_info.day_before_expiry
        prod_doc.description = prod_info.description
        prod_doc.instructions = prod_info.instructions
        prod_doc.article_md = prod_info.article_md
        prod_doc.infos = prod_info.infos

        embed = clip_model.encode_text(prod_info.description)[0]

        prod_embed = await ss.get_one(prod.ProductEmbedding, prod_id)

        prod_embed.description_embed = embed

        if type(prod_info) is MealKitUpdate:
            await ss.execute(
                sqla.delete(prod.MealkitIngredients).where(
                    prod.MealkitIngredients.mealkit_id == prod_id
                )
            )

            for ing, amount in prod_info.ingredients.items():
                ing_exist = (
                    await ss.scalar(
                        sqla.select(sqla.exists().where(prod.Product.id == ing))
                    )
                    or False
                )

                if not ing_exist:
                    raise HandledError(f"Product id {ing} is not exist")

                ingredient = prod.MealkitIngredients(
                    mealkit_id=prod_id, ingredient=ing, amount=amount
                )
                ss.add(ingredient)

        await ss.flush()

        doc_refetch = await ss.get_one(ProductDoc, prod_id)

        content: dict[str, Any] = {
            "id": doc_refetch.id,
            "description": doc_refetch.description,
            "infos": doc_refetch.infos,
            "article_md": doc_refetch.article_md,
        }

        if type(prod_info) is MealKitUpdate:
            ingredients = await ss.scalars(
                sqla.select(prod.MealkitIngredients.ingredient).filter(
                    prod.MealkitIngredients.mealkit_id == prod_id
                )
            )
            content["instructions"] = doc_refetch.instructions
            content["ingredients"] = ingredients.all()

    return content


async def update_price(
    prod_id: str,
    price: float,
    sale_percent: float,
    ss: AsyncSession,
):
    async with ss.begin():
        product_price = prod.ProductPriceHistory(
            price=price,
            sale_percent=sale_percent,
            date=datetime.now(),
            product_id=prod_id,
        )

        ss.add(product_price)

        product = await ss.get_one(prod.Product, prod_id)

        product.price = price
        product.sale_percent = sale_percent

        await ss.flush()

        price_refetch = await ss.scalar(
            sqla.select(prod.ProductPriceHistory)
            .order_by(prod.ProductPriceHistory.date.desc())
            .limit(1)
        )

        if not price_refetch:
            raise HandledError("Price failed to update")

        return {
            "id": price_refetch.product_id,
            "price": price_refetch.price,
            "sale_percent": price_refetch.sale_percent,
            "date": price_refetch.date,
        }


async def restock_product(
    prod_id: str,
    amount: int,
    import_price: float,
    ss: AsyncSession,
):
    async with ss.begin():
        product = await ss.get_one(prod.Product, prod_id)

        product_stock = prod.ProductStockHistory(
            product_id=product.id,
            date=datetime.now(),
            in_price=import_price,
            in_stock=amount,
        )
        product.available_quantity += amount
        product.product_status = prod.ProductStatus.IN_STOCK

        ss.add(product_stock)
        await ss.flush()

        r = await ss.scalars(
            sqla.select(prod.ProductStockHistory)
            .filter(prod.ProductStockHistory.product_id == product.id)
            .order_by(prod.ProductStockHistory.date.desc())
            .limit(1)
        )

        s = r.first()

        if not s:
            raise HandledError("Failed to update price")

        return {
            "in_date": s.date,
            "in_price": s.in_price,
            "in_stock": s.in_stock,
        }


async def update_status(
    prod_id: str,
    status: prod.ProductStatus,
    ss: AsyncSession,
):
    async with ss.begin():
        product = await ss.get_one(prod.Product, prod_id)

        match status:
            case prod.ProductStatus.IN_STOCK:
                if product.available_quantity == 0:
                    raise HandledError("Quantity is empty")

        product.product_status = status

        await ss.flush()

        refetch_prod = await ss.get_one(prod.Product, prod_id)

        return {
            "id": refetch_prod.id,
            "status": refetch_prod.product_status,
        }


async def get_list_product(
    pg: Page,
    session: AsyncSession,
    type: prod.ProductType | None = None,
    prod_name: str = "",
):
    async with session as ss, ss.begin():
        if type:
            filters = [
                prod.Product.product_types == type,
                prod.Product.product_name.ilike(f"%{prod_name}%"),
            ]
        else:
            filters = [
                prod.Product.product_name.ilike(f"%{prod_name}%"),
            ]

        products = await ss.scalars(
            paging(
                sqla.select(prod.Product).filter(*filters),
                pg,
            )
        )

        rtn_products = [
            {
                "id": prod.id,
                "name": prod.product_name,
                "price": prod.price,
                "type": prod.product_types,
                "status": prod.product_status,
                "image_url": prod.image_url,
                "available_quantity": prod.available_quantity,
            }
            for prod in products
        ]

        count = (
            await ss.scalar(
                sqla.select(sqla.func.count(prod.Product.id)).filter(*filters)
            )
            or 0
        )
        return display_page(rtn_products, count, pg)


async def get_product(
    prod_id: str,
    session: AsyncSession,
):
    async with session as ss, ss.begin():
        product = await ss.get(prod.Product, prod_id)

        if not product:
            raise HandledError("Product not found")

        product_doc = await ss.get(ProductDoc, prod_id)

        if not product_doc:
            raise HandledError("Product doc not found")

        base_info: dict[str, Any] = {
            "id": product.id,
            "product_name": product.product_name,
            "description": product_doc.description,
            "available_quantity": product.available_quantity,
            "product_type": product.product_types,
            "product_status": product.product_status,
            "info": product_doc.infos,
            "images_url": product_doc.images_url,
            "article": product_doc.article_md,
            "day_before_expiry": product_doc.day_before_expiry,
            "instructions": product_doc.instructions,
        }

    return base_info


async def get_ingredients(prod_id: str, ss: AsyncSession, pg: Page):
    async with ss.begin():
        is_mealkit = await ss.scalar(
            sqla.select(
                sqla.exists().where(
                    (prod.Product.id == prod_id)
                    & (prod.Product.product_types == prod.ProductType.MEALKIT)
                )
            )
        )

        if not is_mealkit:
            raise HandledError("Product is not a mealkit")

        ingredients = await ss.execute(
            paging(
                sqla.select(
                    prod.MealkitIngredients.ingredient,
                    prod.Product.product_name,
                    prod.Product.image_url,
                    prod.MealkitIngredients.amount,
                )
                .filter(prod.MealkitIngredients.mealkit_id == prod_id)
                .join(
                    prod.Product,
                    prod.Product.id == prod.MealkitIngredients.ingredient,
                ),
                pg,
            )
        )

        count = (
            await ss.scalar(
                sqla.select(
                    sqla.func.count(prod.MealkitIngredients.ingredient).filter(
                        prod.MealkitIngredients.mealkit_id == prod_id
                    )
                )
            )
            or 0
        )

        content = []

        for i in ingredients:
            content.append({
                "id": i[0],
                "name": i[1],
                "image": i[2],
                "amount": i[3],
            })

        return display_page(content, count, pg)


async def get_top_10_products_month(
    ss: AsyncSession, year: int, month: int
) -> list[dict[str, int]]:
    async with ss.begin():
        r = await ss.execute(
            sqla.select(
                prod.Product.product_name.label("product_name"),
                func.sum(OrderHistoryItems.quantity).label("total_quantity"),
            )
            .join(
                OrderHistoryItems,
                prod.Product.id == OrderHistoryItems.product_id,
            )
            .join(
                OrderHistory,
                OrderHistory.id == OrderHistoryItems.order_history_id,
            )
            .filter(func.extract("year", OrderHistory.order_date) == year)
            .filter(func.extract("month", OrderHistory.order_date) == month)
            .group_by(prod.Product.product_name)
            .order_by(func.sum(OrderHistoryItems.quantity).desc())
            .limit(10)
        )

        results = r.all()

        return [
            {"product_name": row.product_name, "total_quantity": row.total_quantity}
            for row in results
        ]


async def get_top_10_products_all_time(ss: AsyncSession):
    async with ss.begin():
        r = await ss.execute(
            sqla.select(
                prod.Product.product_name.label("product_name"),
                func.sum(OrderHistoryItems.quantity).label("total_quantity"),
            )
            .join(
                OrderHistoryItems,
                prod.Product.id == OrderHistoryItems.product_id,
            )
            .join(
                OrderHistory,
                OrderHistory.id == OrderHistoryItems.order_history_id,
            )
            .group_by(prod.Product.product_name)
            .order_by(func.sum(OrderHistoryItems.quantity).desc())
            .limit(10)
        )
        results = r.all()

        return [
            {"product_name": row.product_name, "total_quantity": row.total_quantity}
            for row in results
        ]


async def get_product_stock_history(id: str, pg: Page, ss: AsyncSession):
    async with ss.begin():
        stock_history = await ss.scalars(
            paging(
                sqla.select(prod.ProductStockHistory)
                .filter(prod.ProductStockHistory.product_id == id)
                .order_by(prod.ProductStockHistory.date.desc()),
                pg,
            )
        )

        content = [
            {
                "in_date": s.date,
                "in_price": s.in_price,
                "in_stock": s.in_stock,
            }
            for s in stock_history
        ]

        count = (
            await ss.scalar(
                sqla.select(
                    sqla.func.count(prod.ProductStockHistory.product_id)
                ).filter(prod.ProductStockHistory.product_id == id)
            )
            or 0
        )
    return display_page(content, count, pg)


async def get_product_price_history(id: str, pg: Page, ss: AsyncSession):
    async with ss.begin():
        stock_history = await ss.scalars(
            paging(
                sqla.select(prod.ProductPriceHistory)
                .filter(prod.ProductPriceHistory.product_id == id)
                .order_by(prod.ProductPriceHistory.date.desc()),
                pg,
            )
        )

        content = [s.to_list_instance() for s in stock_history]

        count = (
            await ss.scalar(
                sqla.select(
                    sqla.func.count(prod.ProductPriceHistory.product_id)
                ).filter(prod.ProductPriceHistory.product_id == id)
            )
            or 0
        )
        return display_page(content, count, pg)
