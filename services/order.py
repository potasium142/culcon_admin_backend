import sqlalchemy as sqla
from db.postgresql.paging import Page, paging
from db.postgresql.db_session import db_session
from db.postgresql.models.order_history import (
    OrderHistory,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from etc.local_error import HandledError


def __order_detail_json(o: OrderHistory):
    cp = o.coupon
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
                "price": i.price,
                "price_date": i.date,
                "sale_percent": i.sale_percent,
                "image": i.product.image_url,
                "name": i.product.product_name,
                "type": i.product.product_types,
            }
            for i in o.order_history_items
        ],
    }


def order_list_item(o: OrderHistory):
    coupon_sale = ""
    if o.coupon:
        coupon_sale = o.coupon.sale_percent
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
                sqla.select(OrderHistory),
                pg,
            )
        )

        return [order_list_item(o) for o in orders]


def get_orders_with_status(status: OrderStatus, pg: Page):
    with db_session.session as ss:
        orders = ss.scalars(
            paging(
                sqla.select(OrderHistory).filter(
                    OrderHistory.order_status == status,
                ),
                pg,
            )
        )

        return [order_list_item(o) for o in orders]


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

        db_session.commit()

        # TODO:refund

        order_refetch = ss.get(OrderHistory, id)

        if not order_refetch:
            raise HandledError("Failed to refetch order")

        return order.order_status == order_refetch.order_status
