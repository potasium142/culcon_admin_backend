from typing import Any
from auth import encryption
from db.postgresql.db_session import db_session
from db.postgresql.models.user_account import (
    Cart,
    PostComment,
    UserAccount,
    UserAccountStatus,
)
from dtos.request.user_account import EditCustomerAccount, EditCustomerInfo

from etc.local_error import HandledError
from services.order import order_list_item
from db.postgresql.paging import display_page, paging, Page, table_size
import sqlalchemy as sqla


def set_account_status(id: str, status: UserAccountStatus):
    account = db_session.session.get(UserAccount, id)

    if not account:
        raise HandledError("Customer account not found")

    account.status = status

    db_session.commit()


def get_all_customer(pg: Page):
    with db_session.session as ss:
        customers = ss.scalars(
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

        count = table_size(UserAccount.id)

        return display_page(content, count, pg)


def get_customer(id: str):
    with db_session.session as session:
        c = session.get(UserAccount, id)

        if not c:
            raise HandledError("Customer not found")

        return {
            "id": str(c.id),
            "email": c.email,
            "username": c.username,
            "profile_name": c.profile_name,
            "address": c.address,
            "phone": c.phone,
            "profile_pic": c.profile_pic_uri,
            "order_history": [order_list_item(o) for o in c.order_history],
        }


def edit_customer_info(id: str, info: EditCustomerInfo):
    with db_session.session as ss:
        c = ss.get(UserAccount, id)

        if not c:
            raise HandledError("Customer not found")

        c.email = info.email
        c.address = info.address
        c.phone = info.phone
        c.profile_description = info.profile_description
        c.profile_name = info.profile_name

        db_session.commit()


def edit_customer_account(id: str, info: EditCustomerAccount):
    with db_session.session as ss:
        c = ss.get(UserAccount, id)

        if not c:
            raise HandledError("Customer not found")

        c.username = info.username
        c.password = encryption.hash(info.password)

        db_session.commit()


def get_customer_cart(id, pg: Page):
    with db_session.session as ss:
        cart = ss.scalars(
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
            ss.scalar(
                sqla.select(sqla.func.count(Cart.product_id)).filter(
                    Cart.account_id == id
                )
            )
            or 0
        )
        return display_page(content, count, pg)
