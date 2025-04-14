import asyncio
from datetime import date, time, datetime
import logging
import pytz


from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from services import order as ord_sv
import sqlalchemy as sqla

from db.postgresql.models.order_history import (
    DeliveryStatus,
    OrderHistory,
    OrderProcess,
    OrderStatus,
    PaymentMethod,
)
from db.postgresql.models.shipper import ShipperAvailbility, ShipperStatus
from db.postgresql.models.staff_account import EmployeeInfo
from db.postgresql.paging import Page, display_page, paging
from etc import smtp
from etc.local_error import HandledError


logger = logging.getLogger("uvicorn.info")


async def fetch_non_assign_shifttime(
    ss: AsyncSession,
    pg: Page,
):
    async with ss.begin():
        filter = [
            ShipperAvailbility.start_shift.is_(None)
            | ShipperAvailbility.end_shift.is_(None)
        ]

        shippers = await ss.execute(
            paging(
                sqla.select(
                    ShipperAvailbility.id,
                    ShipperAvailbility.start_shift,
                    ShipperAvailbility.end_shift,
                    EmployeeInfo.realname,
                    EmployeeInfo.email,
                )
                .filter(*filter)
                .join(
                    EmployeeInfo,
                    EmployeeInfo.account_id == ShipperAvailbility.id,
                ),
                pg,
            )
        )
        count = (
            await ss.scalar(
                sqla.select(sqla.func.count(ShipperAvailbility.id).filter(*filter))
            )
            or 0
        )
        content = [
            {
                "id": s[0],
                "start_ship": s[1],
                "end_shift": s[2],
                "name": s[3],
                "email": s[4],
            }
            for s in shippers.all()
        ]
        return display_page(content, count, pg)


async def fetch_shipper(
    ss: AsyncSession,
    pg: Page,
    status: ShipperStatus | None = None,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    start_shift: time | None = None,
    end_shift: time | None = None,
):
    async with ss.begin():
        filter = []

        if status:
            filter.append(ShipperAvailbility.status == status)
        if start_shift:
            filter.append(
                ShipperAvailbility.start_shift < start_shift,
            )
        if end_shift:
            filter.append(
                ShipperAvailbility.end_shift > end_shift,
            )

        if name:
            filter.append(EmployeeInfo.realname.ilike(f"%{name}%"))
        if email:
            filter.append(EmployeeInfo.realname.ilike(f"%{email}%"))
        if phone:
            filter.append(EmployeeInfo.realname.ilike(f"%{phone}%"))

        shippers = await ss.execute(
            paging(
                sqla.select(
                    ShipperAvailbility,
                    EmployeeInfo.realname,
                    EmployeeInfo.email,
                )
                .filter(*filter)
                .join(
                    EmployeeInfo,
                    EmployeeInfo.account_id == ShipperAvailbility.id,
                ),
                pg,
            )
        )
        count = (
            await ss.scalar(
                sqla.select(sqla.func.count(ShipperAvailbility.id).filter(*filter))
            )
            or 0
        )
        content = [
            {
                "id": s[0].id,
                "name": s[1],
                "email": s[2],
                "start_shift": s[0].start_shift,
                "end_shift": s[0].end_shift,
                "current_order": s[0].current_order,
                "status": s[0].status,
            }
            for s in shippers.all()
        ]
        return display_page(content, count, pg)


async def fetch_shippment_from_range(
    pg: Page,
    ss: AsyncSession,
    delivery_status: DeliveryStatus | None = None,
    start_date_confirm: date | None = None,
    end_date_confirm: date | None = None,
    start_date_shipping: date | None = None,
    end_date_shipping: date | None = None,
    shipper_id: str | None = None,
    staff_id: str | None = None,
):
    async with ss.begin():
        filter = []

        if delivery_status:
            filter.append(OrderProcess.delivery_status == delivery_status)

        if start_date_confirm:
            filter.append(OrderProcess.shipping_date > start_date_confirm)
        if end_date_confirm:
            filter.append(OrderProcess.shipping_date < end_date_confirm)

        if start_date_shipping:
            filter.append(OrderProcess.shipping_date > start_date_shipping)
        if end_date_shipping:
            filter.append(OrderProcess.shipping_date < end_date_shipping)

        if shipper_id:
            filter.append(OrderProcess.deliver_by == shipper_id)
        if staff_id:
            filter.append(OrderProcess.process_by == staff_id)

        results = await ss.scalars(
            paging(sqla.select(OrderProcess).filter(*filter), pg)
        )

        count = (
            await ss.scalar(
                sqla.select(
                    sqla.func.count(OrderProcess.order_id).filter(*filter),
                )
            )
            or 0
        )

        content = [
            {
                "id": r.order_id,
                "shipping_date": r.shipping_date,
                "confirm_date": r.confirm_date,
                "process_by": r.process_by,
                "shipping_by": r.deliver_by,
            }
            for r in results
        ]

        return display_page(content, count, pg)


async def assign_shipper(
    order_id: str,
    shipper_id: str,
    ss: AsyncSession,
    bg: BackgroundTasks,
    current_hr: time | None = None,
):
    async with ss.begin():
        is_free = await ss.scalar(
            sqla.select(
                sqla.exists().where(
                    (ShipperAvailbility.status == ShipperStatus.IDLE)
                    | (ShipperAvailbility.status == ShipperStatus.REJECTED),
                )
            )
        )

        if not is_free:
            raise HandledError("Shipper already assign to another order")

        shipment = await ss.get(OrderProcess, order_id)

        if not shipment:
            raise HandledError("Cannot find shipment")

        if not current_hr:
            current_hr = datetime.now(pytz.timezone("Asia/Saigon")).time()

        shiper = await ss.get(ShipperAvailbility, shipper_id)

        match shipment.delivery_status:
            case DeliveryStatus.ACCEPTED | DeliveryStatus.AWAIT:
                if str(shipment.deliver_by) == shipper_id:
                    raise HandledError("Shipment already assign to this shipper")

                prev_shipper = await ss.get(
                    ShipperAvailbility,
                    shipment.deliver_by,
                )

                if prev_shipper:
                    prev_shipper.current_order = None
                    prev_shipper.status = ShipperStatus.IDLE
            case DeliveryStatus.DELIVERED:
                raise HandledError("Shipment is delivered")
            case DeliveryStatus.DELIVERING:
                raise HandledError("Shipment is delivering")
            case DeliveryStatus.CANCELLED:
                raise HandledError("Delivery for this shippment is cancelled")
            case _:
                pass

        order_detail: OrderHistory = await shipment.awaitable_attrs.order

        if order_detail.order_status != OrderStatus.ON_PROCESSING:
            raise HandledError("Order is not suitable for shipping")

        if not shiper:
            raise HandledError("Cannot find shipper")

        if (shiper.start_shift is None) or (shiper.end_shift is None):
            raise HandledError("Shipper was not assign shift time")

        if (shiper.start_shift > current_hr) or (current_hr > shiper.end_shift):
            raise HandledError("Shipper is not in shift")

        shiper.status = ShipperStatus.ASSIGN
        shiper.current_order = order_id

        shipment.deliver_by = shipper_id

        shipper_detail = await ss.get_one(EmployeeInfo, shipper_id)

        bg.add_task(
            smtp.send_template_email,
            shipper_detail.email,
            "New Delivery Request",
            "shipping_notice",
            {
                "shipper_name": shipper_detail.realname,
                "order_id": order_detail.id,
                "order_date": order_detail.order_date,
                "customer_name": order_detail.receiver,
                "customer_phone": order_detail.phonenumber,
                "delivery_address": order_detail.delivery_address,
                "note": order_detail.note,
                "cod_amount": order_detail.total_price
                if order_detail.payment_method == PaymentMethod.COD
                else 0,
            },
        )

        await ss.commit()

    bg.add_task(
        __delivery_timeout,
        order_id,
        shipper_id,
        ss,
    )

    return True


async def __delivery_timeout(
    order_id: str,
    shipper_id: str,
    ss: AsyncSession,
):
    logger.info(f"Set delivery timeout for {order_id}")
    await asyncio.sleep(60 * 15)
    async with ss.begin():
        shipment = await ss.get_one(OrderProcess, order_id)

        shipper_ = await ss.get_one(ShipperAvailbility, shipper_id)

        if shipper_.status != ShipperStatus.ASSIGN:
            return

        shipper_.current_order = None
        shipper_.status = ShipperStatus.IDLE

        shipper_detail = await ss.get_one(EmployeeInfo, shipper_id)

        order_detail: OrderHistory = await shipment.awaitable_attrs.order

        shipment.deliver_by = None
        shipment.delivery_status = DeliveryStatus.TIMEOUT

        await ss.flush()

        smtp.send_template_email(
            shipper_detail.email,
            "Delivery Request Cancelled",
            "delivery_cancellation",
            {
                "shipper_name": shipper_detail.realname,
                "order_id": order_detail.id,
                "order_date": order_detail.order_date,
                "customer_name": order_detail.receiver,
                "customer_phone": order_detail.phonenumber,
                "delivery_address": order_detail.delivery_address,
                "note": order_detail.note,
                "cod_amount": order_detail.total_price
                if order_detail.payment_method == PaymentMethod.COD
                else 0,
            },
        )


async def reject_shipment(
    id: str,
    self_id: str,
    ss: AsyncSession,
):
    async with ss.begin():
        shipment = await ss.get_one(OrderProcess, id)

        if shipment.deliver_by != self_id:
            raise HandledError("Order does not deliver by you")

        shipment.deliver_by = None
        shipment.delivery_status = DeliveryStatus.REJECTED

        shipper_ = await ss.scalar(
            sqla.select(ShipperAvailbility).filter(
                ShipperAvailbility.id == self_id,
                ShipperAvailbility.current_order == id,
            )
        )

        if not shipper_:
            raise HandledError("Record for this shipment was not found on shipper")

        shipper_.status = ShipperStatus.IDLE
        shipper_.current_order = None

        await ss.commit()


async def shipping(
    id: str,
    shipper_id: str,
    ss: AsyncSession,
):
    async with ss.begin():
        shipment = await ss.get_one(OrderProcess, id)

        if shipment.deliver_by != shipper_id:
            raise HandledError("Order does not deliver by you")

        if shipment.delivery_status != DeliveryStatus.ACCEPTED:
            raise HandledError("Shipment was not accepted by shipper")

        order: OrderHistory = await shipment.awaitable_attrs.order

        if order.order_status != OrderStatus.ON_PROCESSING:
            raise HandledError("Order is not suitable for shipping")

        order.order_status = OrderStatus.ON_SHIPPING

        shipment.shipping_date = datetime.now()
        shipment.delivery_status = DeliveryStatus.DELIVERING

        shipper_ = await ss.scalar(
            sqla.select(ShipperAvailbility).filter(
                ShipperAvailbility.id == shipper_id,
                ShipperAvailbility.current_order == id,
            )
        )

        if not shipper_:
            raise HandledError(
                "Desync in database, U SHOULD NOT SEE THIS MSG AT ALL, GOD HELP US"
            )

        shipper_.status = ShipperStatus.ON_SHIPPING

        await ss.commit()


async def __receive_timeout(
    order_id: str,
    ss: AsyncSession,
):
    logger.info(f"Set receive timeout for {order_id}")
    await asyncio.sleep(60 * 60)
    async with ss.begin():
        shipment = await ss.get_one(OrderHistory, order_id)

        shipment.order_status = OrderStatus.DELIVERED

        logger.info(f"Order {order_id} is set to delivered")
        await ss.flush()


async def complete_shipment(
    id: str,
    self_id: str,
    ss: AsyncSession,
    bg: BackgroundTasks,
):
    async with ss.begin():
        shipment = await ss.get_one(OrderProcess, id)

        if shipment.deliver_by != self_id:
            raise HandledError("Order does not deliver by you")

        if shipment.delivery_status != DeliveryStatus.DELIVERING:
            raise HandledError("Shippment was not delivering")

        order: OrderHistory = await shipment.awaitable_attrs.order

        if order.order_status != OrderStatus.ON_SHIPPING:
            raise HandledError("Order is not suitable for complete shipment")

        shipment.shipping_date = datetime.now()
        order.order_status = OrderStatus.SHIPPED

        shipper_ = await ss.scalar(
            sqla.select(ShipperAvailbility).filter(
                ShipperAvailbility.id == self_id,
                ShipperAvailbility.current_order == id,
            )
        )

        if not shipper_:
            raise HandledError(
                "Desync in database, U SHOULD NOT SEE THIS MSG AT ALL, GOD HELP US"
            )

        shipper_.status = ShipperStatus.IDLE
        shipper_.current_order = None

        await ss.commit()
    bg.add_task(
        __receive_timeout,
        id,
        ss,
    )


async def accept_shipment(
    order_id: str,
    self_id: str,
    ss: AsyncSession,
):
    async with ss.begin():
        shipper_ = await ss.scalar(
            sqla.select(ShipperAvailbility).filter(
                ShipperAvailbility.id == self_id,
                ShipperAvailbility.current_order == order_id,
            )
        )

        shipment = await ss.get(OrderProcess, order_id)

        if not shipment:
            raise HandledError("Cannot find shipment")

        if not shipper_:
            raise HandledError("This order was not assigned to you")

        if shipper_.status != ShipperStatus.ASSIGN:
            raise HandledError("You already deliver this order")

        if shipment.deliver_by != self_id:
            raise HandledError("This order was to assigned to you")

        shipment.deliver_by = self_id
        shipment.delivery_status = DeliveryStatus.ACCEPTED

        shipper_.status = ShipperStatus.ACCEPTED

        await ss.commit()


async def cancel_shipment(
    order_id: str,
    self_id: str,
    ss: AsyncSession,
):
    async with ss.begin():
        shipment = await ss.get_one(OrderProcess, order_id)

        if shipment.deliver_by != self_id:
            raise HandledError("Order does not deliver by you")

        if shipment.delivery_status != DeliveryStatus.DELIVERING:
            raise HandledError("Shippment was not delivering")

        order: OrderHistory = await shipment.awaitable_attrs.order

        if order.order_status != OrderStatus.ON_SHIPPING:
            raise HandledError("Order is not suitable for complete shipment")

        shipper_ = await ss.scalar(
            sqla.select(ShipperAvailbility).filter(
                ShipperAvailbility.id == self_id,
                ShipperAvailbility.current_order == order_id,
            )
        )

        if not shipper_:
            raise HandledError(
                "Desync in database, U SHOULD NOT SEE THIS MSG AT ALL, GOD HELP US"
            )

        shipper_.status = ShipperStatus.IDLE
        shipper_.current_order = None

        await ss.flush()

        return await ord_sv.cancel(order_id, ss)


async def set_shift_time(
    id: str,
    start_time: time,
    end_time: time,
    ss: AsyncSession,
):
    if start_time > end_time:
        raise HandledError("Start time must be before end time")

    if start_time < time(8):
        raise HandledError("Start shift had to be after 8 AM")

    if end_time > time(23):
        raise HandledError("End shift had to be before 11 PM")

    async with ss.begin():
        sa = ShipperAvailbility(
            id=id,
            start_shift=start_time,
            end_shift=end_time,
            status=ShipperStatus.IDLE,
        )

        await ss.merge(sa)

        await ss.flush()

        rf = await ss.get_one(ShipperAvailbility, id)

    return {
        "id": rf.id,
        "start_time": rf.start_shift,
        "end_time": rf.end_shift,
    }


async def get_await_order(
    self_id: str,
    ss: AsyncSession,
):
    async with ss.begin():
        filter = [
            ShipperAvailbility.id == self_id,
            ShipperAvailbility.status == ShipperStatus.ASSIGN,
        ]

        o = await ss.scalar(
            sqla.select(OrderHistory)
            .select_from(ShipperAvailbility)
            .filter(*filter)
            .join(
                OrderHistory,
                OrderHistory.id == ShipperAvailbility.current_order,
            )
            .limit(1)
        )

        if not o:
            raise HandledError("Your shipping queue is empty")

        return {
            "id": o.id,
            "receiver": o.receiver,
            "address": o.delivery_address,
            "phone": o.phonenumber,
            "note": o.note,
            "pay": o.total_price if o.payment_method == PaymentMethod.COD else 0,
        }


async def get_current_order(
    self_id: str,
    ss: AsyncSession,
):
    async with ss.begin():
        filter = [
            ShipperAvailbility.id == self_id,
            (ShipperAvailbility.status == ShipperStatus.ACCEPTED)
            | (ShipperAvailbility.status == ShipperStatus.ON_SHIPPING)
            | (ShipperAvailbility.status == ShipperStatus.DELIVERED),
        ]

        o = (
            await ss.execute(
                sqla.select(OrderHistory, ShipperAvailbility.status)
                .select_from(ShipperAvailbility)
                .filter(*filter)
                .join(
                    OrderHistory,
                    OrderHistory.id == ShipperAvailbility.current_order,
                )
                .limit(1)
            )
        ).one()

        if not o:
            raise HandledError("Cannot found order")

        return {
            "id": o[0].id,
            "receiver": o[0].receiver,
            "address": o[0].delivery_address,
            "phone": o[0].phonenumber,
            "note": o[0].note,
            "pay": o[0].total_price if o[0].payment_method == PaymentMethod.COD else 0,
            "status": o[1],
        }
