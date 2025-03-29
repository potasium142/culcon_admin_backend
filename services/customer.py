from sqlalchemy.ext.asyncio import AsyncSession
from auth import encryption
from db.postgresql.models.order_history import OrderHistory
from db.postgresql.models.user_account import (
    Cart,
    UserAccount,
    UserAccountStatus,
)
from dtos.request.user_account import EditCustomerAccount, EditCustomerInfo

from etc.local_error import HandledError
from db.postgresql.paging import display_page, paging, Page, table_size
import sqlalchemy as sqla


async def set_account_status(
    id: str,
    status: UserAccountStatus,
    ss: AsyncSession,
):
    async with ss.begin():
        account = await ss.get_one(UserAccount, id)

        account.status = status

        await ss.flush()

        acc_refetch = await ss.get_one(UserAccount, id)

        return {
            "id": acc_refetch.id,
            "status": acc_refetch.status,
        }


async def get_all_customer(pg: Page, ss: AsyncSession):
    async with ss.begin():
        customers = await ss.scalars(
            paging(
                sqla.select(UserAccount),
                pg,
            )
        )

        content = [
            {
                "id": str(c.id),
                "username": c.username,
                "profile_name": c.profile_name,
                "status": c.status,
                "profile_pic": c.profile_pic_uri,
            }
            for c in customers
        ]

        count = await table_size(UserAccount.id, ss)

        return display_page(content, count, pg)


async def get_customer(id: str, ss: AsyncSession):
    async with ss as session, session.begin():
        c = await session.get_one(UserAccount, id)

        return {
            "id": str(c.id),
            "email": c.email,
            "username": c.username,
            "profile_name": c.profile_name,
            "address": c.address,
            "phone": c.phone,
            "profile_pic": c.profile_pic_uri,
        }


async def get_customer_order_history(id: str, ss: AsyncSession, pg: Page):
    async with ss.begin():
        usr_chk = await ss.scalar(
            sqla.select(sqla.exists().where(UserAccount.id == id))
        )

        if not usr_chk:
            raise HandledError("User not exist")

        orders = await ss.scalars(
            paging(
                sqla.select(OrderHistory).filter(OrderHistory.user_id == id),
                pg,
            )
        )

        content = [
            {
                "id": o.id,
                "order_date": o.order_date,
                "payment_method": o.payment_method,
                "payment_status": o.payment_status,
                "order_status": o.order_status,
            }
            for o in orders
        ]

        count = (
            await ss.scalar(
                sqla.select(
                    sqla.func.count(
                        OrderHistory.id,
                    )
                ).filter(
                    OrderHistory.user_id == id,
                ),
            )
            or 0
        )

        return display_page(content, count, pg)


async def edit_customer_info(
    id: str,
    info: EditCustomerInfo,
    ss: AsyncSession,
):
    async with ss.begin():
        c = await ss.get_one(UserAccount, id)

        c.email = info.email
        c.address = info.address
        c.phone = info.phone
        c.profile_description = info.profile_description
        c.profile_name = info.profile_name

        await ss.flush()

        c_rf = await ss.get_one(UserAccount, id)

        return {
            "email": c_rf.email,
            "address": c_rf.address,
            "phone": c_rf.phone,
            "profile_description": c_rf.profile_description,
            "profile_name": c_rf.profile_name,
        }


async def edit_customer_account(
    id: str,
    info: EditCustomerAccount,
    ss: AsyncSession,
):
    async with ss.begin():
        c = await ss.get_one(UserAccount, id)

        c.username = info.username

        hashed_password = encryption.hash(info.password)

        c.password = hashed_password

        await ss.flush()

        c_rft = await ss.get_one(UserAccount, id)

        return {
            "username": c_rft.username,
            "password_match": c_rft.password == hashed_password,
        }


async def get_customer_cart(id, pg: Page, ss: AsyncSession):
    async with ss.begin():
        usr_chk = await ss.scalar(
            sqla.select(sqla.exists().where(UserAccount.id == id))
        )

        if not usr_chk:
            raise HandledError("User not exist")

        cart = await ss.scalars(
            paging(
                sqla.select(Cart).filter(
                    Cart.account_id == id,
                ),
                pg,
            )
        )

        content = [
            {
                "id": i.product_id.id,
                "name": i.product_id.product_name,
                "type": i.product_id.product_types,
                "status": i.product_id.product_status,
                "image_url": i.product_id.image_url,
                "price": i.product_id.price,
                "sale_percent": i.product_id.sale_percent,
                "incart": i.amount,
            }
            for i in cart
        ]
        count = (
            await ss.scalar(
                sqla.select(sqla.func.count(Cart.product_id)).filter(
                    Cart.account_id == id
                )
            )
            or 0
        )
        return display_page(content, count, pg)
