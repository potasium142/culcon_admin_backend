import asyncio
from datetime import date, time, datetime
import logging


from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sqla

from db.postgresql.models.order_history import (
    OrderHistory,
    OrderProcess,
    OrderStatus,
    PaymentMethod,
    ShippingStatus,
)
from db.postgresql.models.shipper import ShipperAvailbility
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
    occupied: bool | None = None,
    start_shift: time | None = None,
    end_shift: time | None = None,
):
    async with ss.begin():
        filter = []

        if occupied is not None:
            filter.append(
                ShipperAvailbility.occupied == occupied,
            )
        if start_shift:
            filter.append(
                ShipperAvailbility.start_shift < start_shift,
            )
        if end_shift:
            filter.append(
                ShipperAvailbility.end_shift > end_shift,
            )

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


async def fetch_shippment_from_range(
    pg: Page,
    ss: AsyncSession,
    start_date_confirm: date | None = None,
    end_date_confirm: date | None = None,
    start_date_shipping: date | None = None,
    end_date_shipping: date | None = None,
    shipper_id: str | None = None,
    staff_id: str | None = None,
):
    async with ss.begin():
        filter = []

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
            filter.append(OrderProcess.deliver_by == staff_id)

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
                "status": r.status,
            }
            for r in results
        ]

        return display_page(content, count, pg)


async def assign_shipper(
    order_id: str,
    shipper_id: str,
    ss: AsyncSession,
    bg: BackgroundTasks,
):
    async with ss.begin():
        shipment = await ss.get(OrderProcess, order_id)

        if not shipment:
            raise HandledError("Cannot find shipment")

        current_hr = datetime.now().time()

        shiper = await ss.get(ShipperAvailbility, shipper_id)

        if not shiper:
            raise HandledError("Cannot find shipper")

        if shipment.deliver_by == shipper_id:
            raise HandledError("Shipment already assign to this shipper")

        if shiper.occupied:
            raise HandledError("Shipper is occupied")

        if (shiper.start_shift is None) or (shiper.end_shift is None):
            raise HandledError("Shipper was not assign shift time")

        if (shiper.start_shift > current_hr) or (current_hr > shiper.end_shift):
            raise HandledError("Shipper is not in shift")

        shipment.deliver_by = shiper.id

        order_detail: OrderHistory = await shipment.awaitable_attrs.order

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

        if shipment.status:
            return

        shipper_detail = await ss.get_one(EmployeeInfo, shipper_id)

        order_detail: OrderHistory = await shipment.awaitable_attrs.order

        shipment.deliver_by = None

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

        shipment.status = ShippingStatus.REJECTED

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

        shipment.status = ShippingStatus.ON_SHIPPING

        await ss.commit()


async def complete_shipment(
    id: str,
    self_id: str,
    ss: AsyncSession,
):
    async with ss.begin():
        shipment = await ss.get_one(OrderProcess, id)

        if shipment.deliver_by != self_id:
            raise HandledError("Order does not deliver by you")

        shipment.status = ShippingStatus.DELIVERED

        shiper = await ss.get_one(ShipperAvailbility, self_id)
        shiper.occupied = False

        order: OrderHistory = await shipment.awaitable_attrs.order

        order.order_status = OrderStatus.SHIPPED

        await ss.flush()


async def accept_shipment(
    order_id: str,
    self_id: str,
    ss: AsyncSession,
):
    async with ss.begin():
        shipment = await ss.get_one(OrderProcess, order_id)

        if shipment.deliver_by != self_id:
            raise HandledError("Order does not deliver by you")

        shipment.status = ShippingStatus.ACCEPTED

        shiper = await ss.get_one(ShipperAvailbility, self_id)
        shiper.occupied = True

        await ss.commit()


async def set_shift_time(
    id: str,
    start_time: time,
    end_time: time,
    ss: AsyncSession,
):
    async with ss.begin():
        sa = ShipperAvailbility(
            id=id,
            start_shift=start_time,
            end_shift=end_time,
            occupied=False,
        )

        await ss.merge(sa)

        await ss.commit()


async def get_await_order(
    self_id: str,
    ss: AsyncSession,
):
    async with ss.begin():
        filter = [
            OrderProcess.deliver_by == self_id,
            OrderProcess.status.is_(None),
        ]
        o = await ss.scalar(
            sqla.select(OrderHistory)
            .select_from(OrderProcess)
            .filter(*filter)
            .join(OrderHistory, OrderHistory.id == OrderProcess.order_id)
            .order_by(OrderProcess.shipping_date.desc())
            .limit(1),
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
            OrderProcess.deliver_by == self_id,
            (OrderProcess.status == ShippingStatus.ACCEPTED)
            | (OrderProcess.status == ShippingStatus.ON_SHIPPING),
        ]
        o = await ss.scalar(
            sqla.select(OrderHistory)
            .select_from(OrderProcess)
            .filter(*filter)
            .join(OrderHistory, OrderHistory.id == OrderProcess.order_id)
            .order_by(OrderProcess.shipping_date.desc())
            .limit(1),
        )

        if not o:
            raise HandledError("Cannot found order")

        return {
            "id": o.id,
            "receiver": o.receiver,
            "address": o.delivery_address,
            "phone": o.phonenumber,
            "note": o.note,
            "pay": o.total_price if o.payment_method == PaymentMethod.COD else 0,
        }
