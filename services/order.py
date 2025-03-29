import sqlalchemy as sqla
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgresql.models.product import Product, ProductPriceHistory
from db.postgresql.paging import Page, display_page, paging, table_size
from db.postgresql.models.order_history import (
    Coupon,
    OrderHistory,
    OrderHistoryItems,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from etc.local_error import HandledError


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


async def get_all_orders(pg: Page, ss: AsyncSession):
    async with ss.begin():
        orders = await ss.scalars(
            paging(
                sqla.select(OrderHistory).order_by(
                    OrderHistory.order_date.desc(),
                    OrderHistory.order_status.asc(),
                ),
                pg,
            )
        )

        content = [order_list_item(o) for o in orders]
        count = await table_size(OrderHistory.id, ss)
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
    check_payment: bool = True,
):
    async with ss.begin():
        order = await ss.get_one(OrderHistory, id)

        if order.order_status != prev_status:
            raise HandledError(f"Status of order must be {prev_status}")

        if check_payment:
            payment_received = order.payment_status == PaymentStatus.RECEIVED
            cod = order.payment_method == PaymentMethod.COD

            if cod:
                if order.payment_status != PaymentStatus.PENDING:
                    raise HandledError(
                        "Illegal payment status (Payment should be PENDING on COD)"
                    )

            if not payment_received:
                raise HandledError("Order has not paid")

        order.order_status = status

        await ss.flush()

        order_refetch = await ss.get_one(OrderHistory, id)

        return order.order_status == order_refetch.order_status


async def cancel_order(id: str, ss: AsyncSession):
    async with ss.begin():
        order = await ss.get_one(OrderHistory, id)

        if order.order_status in (OrderStatus.ON_SHIPPING, OrderStatus.SHIPPED):
            raise HandledError("Order already in delivering or delivered")

        if order.order_status is OrderStatus.CANCELLED:
            raise HandledError("Order already cancelled")

        order.order_status = OrderStatus.CANCELLED

        items = await ss.scalars(
            sqla.select(OrderHistoryItems).filter(
                OrderHistoryItems.order_history_id == id
            )
        )

        # TODO:refund
        for i in items:
            amount = i.quantity
            prod_price: ProductPriceHistory = await i.awaitable_attrs.item
            prod = await prod_price.awaitable_attrs.product
            prod.available_quantity += amount

        await ss.flush()

        order_refetch = await ss.get_one(OrderHistory, id)

        return order.order_status == order_refetch.order_status
