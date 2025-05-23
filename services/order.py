from datetime import datetime
import sqlalchemy as sqla
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgresql.models.product import (
    MealkitIngredients,
    Product,
    ProductPriceHistory,
    ProductStatus,
)
from db.postgresql.models.transaction import PaymentTransaction
from db.postgresql.paging import Page, display_page, paging
from db.postgresql.models.order_history import (
    Coupon,
    OrderHistory,
    OrderHistoryItems,
    OrderProcess,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from etc.local_error import HandledError
from etc.paypal import payment_controller


async def __order_detail_json(
    o: OrderHistory,
):
    user = await o.awaitable_attrs.user
    coupon: Coupon = await o.awaitable_attrs.coupon_detail
    if o.coupon_detail:
        coupon_sale = coupon.sale_percent
    else:
        coupon_sale = ""
    return {
        "id": o.id,
        "user_id": user.id,
        "user_pfp": user.profile_pic_uri,
        "order_date": o.order_date,
        "delivery_address": o.delivery_address,
        "receiver": o.receiver,
        "phonenumber": o.phonenumber,
        "order_status": o.order_status,
        "payment_status": o.payment_status,
        "payment_method": o.payment_method,
        "total_price": o.total_price,
        "note": o.note,
        "coupon_sale": coupon_sale,
    }


def order_list_item(o: OrderHistory):
    return {
        "id": o.id,
        "order_date": o.order_date,
        "delivery_address": o.delivery_address,
        "receiver": o.receiver,
        "phonenumber": o.phonenumber,
        "order_status": o.order_status,
        "payment_status": o.payment_status,
        "payment_method": o.payment_method,
        "total_price": o.total_price,
    }


async def get_all_orders(
    pg: Page,
    ss: AsyncSession,
    id: str = "",
    status: OrderStatus | None = None,
):
    if status:
        filter_list = [
            OrderHistory.id.ilike(f"%{id}%"),
            OrderHistory.order_status == status,
        ]
    else:
        filter_list = [OrderHistory.id.ilike(f"%{id}%")]

    async with ss.begin():
        orders = await ss.scalars(
            paging(
                sqla.select(OrderHistory)
                .filter(*filter_list)
                .order_by(
                    OrderHistory.order_date.desc(),
                    OrderHistory.order_status.asc(),
                ),
                pg,
            )
        )

        content = [order_list_item(o) for o in orders]
        count = (
            await ss.scalar(
                sqla.select(sqla.func.count(OrderHistory.id)).filter(*filter_list)
            )
            or 0
        )
    return display_page(content, count, pg)


async def get_orders_with_status(
    status: OrderStatus,
    pg: Page,
    ss: AsyncSession,
):
    async with ss.begin():
        orders = await ss.scalars(
            paging(
                sqla.select(OrderHistory)
                .order_by(
                    OrderHistory.order_date.desc(),
                )
                .filter(
                    OrderHistory.order_status == status,
                ),
                pg,
            )
        )

        content = [order_list_item(o) for o in orders]
        count = (
            await ss.scalar(
                sqla.select(
                    sqla.func.count(OrderHistory.order_status == status)
                ).filter(OrderHistory.order_status == status)
            )
            or 0
        )

        return display_page(content, count, pg)


async def get_order_detail(id: str, ss: AsyncSession):
    async with ss.begin():
        order = await ss.get_one(OrderHistory, id)

        return await __order_detail_json(order)


async def get_order_items(id: str, pg: Page, ss: AsyncSession):
    async with ss.begin():
        items = await ss.scalars(
            paging(
                sqla.select(OrderHistoryItems).filter(
                    OrderHistoryItems.order_history_id == id,
                ),
                pg,
            )
        )
        count = (
            await ss.scalar(
                sqla.select(sqla.func.count(OrderHistoryItems.product_id)).filter(
                    OrderHistoryItems.order_history_id == id
                )
            )
            or 0
        )

        content = []
        for i in items:
            p = await ss.get_one(Product, i.product_id)
            price: ProductPriceHistory = await i.awaitable_attrs.item
            content.append({
                "id": p.id,
                "image_url": p.image_url,
                "name": p.product_name,
                "type": p.product_types,
                "price": price.price,
                "price_date": price.date,
                "sale_percent": price.sale_percent,
            })

        return display_page(content, count, pg)


async def change_order_status(
    id: str,
    ss: AsyncSession,
    prev_status: OrderStatus,
    status: OrderStatus,
):
    async with ss.begin():
        order = await ss.get_one(OrderHistory, id)

        if order.order_status != prev_status:
            raise HandledError(f"Status of order must be {prev_status}")

        order.order_status = status

        await ss.flush()

        order_refetch = await ss.get_one(OrderHistory, id)

        return order.order_status == order_refetch.order_status


async def check_mealkit_availability(id: str, ss: AsyncSession):
    ings = await ss.scalars(
        sqla.select(MealkitIngredients).filter(MealkitIngredients.mealkit_id == id)
    )

    oft_prod = []

    for i in ings:
        p: Product = await i.awaitable_attrs.ingredient
        if p.available_quantity < i.amount:
            continue

        oft_prod.append({
            "id": p.id,
            "name": p.product_name,
        })

    return oft_prod


async def accept_order(id: str, ss: AsyncSession, self_id: str):
    async with ss.begin():
        order = await ss.get_one(OrderHistory, id)

        items = await ss.scalars(
            sqla.select(OrderHistoryItems).filter(
                OrderHistoryItems.order_history_id == id
            )
        )

        for i in items:
            p_price: ProductPriceHistory = await i.awaitable_attrs.item
            prod: Product = await p_price.awaitable_attrs.product

            if prod.available_quantity == 0:
                prod.product_status = ProductStatus.OUT_OF_STOCK
            elif prod.available_quantity < i.quantity:
                raise HandledError(f"{prod.product_name} does not have enough stock")

        if order.order_status != OrderStatus.ON_CONFIRM:
            raise HandledError("Status of order must be ON_CONFIRM")

        payment_received = order.payment_status == PaymentStatus.RECEIVED
        cod = order.payment_method == PaymentMethod.COD

        if cod:
            if order.payment_status != PaymentStatus.PENDING:
                raise HandledError(
                    "Illegal payment status (Payment should be PENDING on COD)"
                )
        else:
            if not payment_received:
                raise HandledError("Order has not paid")

        order.order_status = OrderStatus.ON_PROCESSING

        order_process = OrderProcess(
            order_id=order.id,
            confirm_date=datetime.now(),
            process_by=self_id,
        )

        ss.add(order_process)

        await ss.flush()

        order_refetch = await ss.get_one(OrderHistory, id)

        return order.order_status == order_refetch.order_status


async def cancel_order(id: str, ss: AsyncSession):
    async with ss.begin():
        order = await ss.get_one(OrderHistory, id)

        if order.order_status is OrderStatus.ON_SHIPPING:
            raise HandledError("Order already in delivering")
        return await cancel(id, ss)


async def cancel(id: str, ss: AsyncSession):
    order = await ss.get_one(OrderHistory, id)

    if order.order_status is OrderStatus.SHIPPED:
        raise HandledError("Order already  delivered")

    if order.order_status is OrderStatus.CANCELLED:
        raise HandledError("Order already cancelled")

    order.order_status = OrderStatus.CANCELLED

    items = await ss.scalars(
        sqla.select(OrderHistoryItems).filter(OrderHistoryItems.order_history_id == id)
    )

    if order.payment_method == PaymentMethod.PAYPAL:
        payment_record = await ss.get_one(PaymentTransaction, id)

        refund_capture = payment_controller.refund_captured_payment({
            "capture_id": payment_record.payment_id,
            "prefer": "return=minimal",
        })

        payment_record.refund_id = refund_capture.body.id  # type: ignore

        payment_record.status = PaymentStatus.REFUNDED

    for i in items:
        amount = i.quantity
        prod_price: ProductPriceHistory = await i.awaitable_attrs.item
        prod = await prod_price.awaitable_attrs.product
        prod.available_quantity += amount

    await ss.flush()

    order_refetch = await ss.get_one(OrderHistory, id)

    return order.order_status == order_refetch.order_status
