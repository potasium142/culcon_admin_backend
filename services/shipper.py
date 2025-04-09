from datetime import date, time, datetime


from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sqla

from db.postgresql.models.order_history import OrderProcess, ShippingStatus
from db.postgresql.models.shipper import ShipperAvailbility
from db.postgresql.paging import Page, display_page, paging
from etc.local_error import HandledError


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

        shippers = await ss.scalars(
            paging(
                sqla.select(ShipperAvailbility).filter(*filter),
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
                "id": s.id,
                "start_ship": s.start_shift,
                "end_shift": s.end_shift,
            }
            for s in shippers
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
):
    async with ss.begin():
        shipment = await ss.get_one(OrderProcess, order_id)

        current_hr = datetime.now().time()

        shiper = await ss.get_one(ShipperAvailbility, shipper_id)

        if shiper.occupied:
            raise HandledError("Shipper is occupied")

        if (shiper.start_shift > current_hr) or (shiper.end_shift < current_hr):
            raise HandledError("Shipper is not in shift")

        shipment.deliver_by = shiper.id

        await ss.commit()


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

        await ss.commit()


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
