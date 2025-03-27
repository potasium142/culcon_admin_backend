import sqlalchemy as sqla
from db.postgresql.paging import Page, display_page, paging, table_size
from db.postgresql.db_session import db_session
from db.postgresql.models.order_history import (
    OrderHistory,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from etc.local_error import HandledError


def __order_detail_json(o: OrderHistory):
    cp = o.coupon_detail
    if cp:
        coupon_detail = {
            "id": cp.id,
            "sale_percent": cp.sale_percent,
        }
    else:
        coupon_detail = {}

    return {
        "id": o.id,
        "user_id": o.user.id,
        "user_pfp": o.user.profile_pic_uri,
        "order_date": o.order_date,
        "delivery_address": o.delivery_address,
        "receiver": o.receiver,
        "phonenumber": o.phonenumber,
        "order_status": o.order_status,
        "payment_status": o.payment_status,
        "payment_method": o.payment_method,
        "total_price": o.total_price,
        "note": o.note,
        "coupon": coupon_detail,
        "items": [
            {
                "id": i.product_id,
                "price": i.item.price,
                "price_date": i.item.date,
                "sale_percent": i.item.sale_percent,
                "image": i.item.product.image_url,
                "name": i.item.product.product_name,
                "type": i.item.product.product_types,
                "amount": i.quantity,
            }
            for i in o.order_history_items
        ],
    }


def order_list_item(o: OrderHistory):
    if o.coupon_detail:
        coupon_sale = o.coupon_detail.sale_percent
    else:
        coupon_sale = ""

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
        "coupon_sale": coupon_sale,
    }


def get_all_orders(pg: Page):
    with db_session.session as ss:
        orders = ss.scalars(
            paging(
                sqla.select(OrderHistory).order_by(
                    OrderHistory.order_date.desc(),
                    OrderHistory.order_status.asc(),
                ),
                pg,
            )
        )

        content = [order_list_item(o) for o in orders]
        count = table_size(OrderHistory.id)
        return display_page(content, count, pg)


def get_orders_with_status(status: OrderStatus, pg: Page):
    with db_session.session as ss:
        orders = ss.scalars(
            paging(
                sqla.select(OrderHistory)
                .order_by(
                    OrderHistory.order_status.asc(),
                )
                .filter(
                    OrderHistory.order_status == status,
                ),
                pg,
            )
        )

        content = [order_list_item(o) for o in orders]
        count = (
            ss.scalar(
                sqla.select(
                    sqla.func.count(OrderHistory.order_status == status)
                ).filter(OrderHistory.order_status == status)
            )
            or 0
        )

        return display_page(content, count, pg)


def get_order_detail(id: str):
    with db_session.session as ss:
        order = ss.get(OrderHistory, id)

        if not order:
            raise HandledError("Order does not exist")

        return __order_detail_json(order)


def change_order_status(
    id: str,
    prev_status: OrderStatus,
    status: OrderStatus,
    check_payment: bool = True,
):
    with db_session.session as ss:
        order = ss.get(OrderHistory, id)

        if not order:
            raise HandledError("Order does not exist")

        if order.order_status != prev_status:
            raise HandledError(f"Status of order must be {prev_status}")

        if check_payment:
            payment_received = order.payment_status == PaymentStatus.RECEIVED
            cod = order.payment_method == PaymentMethod.COD
            if not (payment_received or cod):
                raise HandledError("Order has not paid")

        order.order_status = status

        db_session.commit()

        order_refetch = ss.get(OrderHistory, id)

        if not order_refetch:
            raise HandledError("Failed to refetch order")

        return order.order_status == order_refetch.order_status


def cancel_order(id: str):
    with db_session.session as ss:
        order = ss.get(OrderHistory, id)

        if not order:
            raise HandledError("Order does not exist")

        if order.order_status in (OrderStatus.ON_SHIPPING, OrderStatus.SHIPPED):
            raise HandledError("Order already in delivering or delivered")

        if order.order_status is OrderStatus.CANCELLED:
            raise HandledError("Order already cancelled")

        order.order_status = OrderStatus.CANCELLED

        # TODO:refund
        for i in order.order_history_items:
            amount = i.quantity
            i.item.product.available_quantity += amount

        db_session.commit()

        order_refetch = ss.get(OrderHistory, id)

        if not order_refetch:
            raise HandledError("Failed to refetch order")

        return order.order_status == order_refetch.order_status
