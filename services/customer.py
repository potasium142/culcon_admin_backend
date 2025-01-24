from typing import Any
from db.postgresql.db_session import db_session
from db.postgresql.models.user_account import (
    Cart,
    PostComment,
    UserAccount,
    UserAccountStatus,
)


def set_account_status(id: str, status: UserAccountStatus):
    account = db_session.session.get(UserAccount, id)

    if not account:
        raise Exception("Customer account not found")

    account.status = status

    db_session.commit()


def delete_comment(id: str, comment_id: str):
    comment = db_session.session.get(PostComment, {"account_id": id, "id": id})

    if not comment:
        raise Exception("Comment not found")

    comment.account_id = None

    db_session.commit()


def get_all_customer() -> list[dict[str, Any]]:
    customers = db_session.session.query(UserAccount).all()
    return [
        {
            "id": str(c.id),
            "username": c.username,
            "status": c.status,
            "profile_pic": c.profile_pic_uri,
        }
        for c in customers
    ]


def get_customer(id: str):
    with db_session.session as session:
        c = session.get(UserAccount, id)

        if not c:
            raise Exception("Customer not found")

        return {
            "id": str(c.id),
            "email": c.email,
            "username": c.username,
            "address": c.address,
            "phone": c.phone,
            "profile_pic": c.profile_pic_uri,
        }


def get_customer_cart(id):
    with db_session.session as session:
        cart = session.query(Cart).filter_by(account_id=id)

        return [
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
