from typing import Type

import sqlalchemy.orm

from db import DBSession
from db.models.staff_account import StaffAccount

_session: sqlalchemy.orm.Session = DBSession()


def commit() -> None:
    try:
        _session.commit()
    except Exception as e:
        _session.rollback()
        raise e


def add_account(account: StaffAccount) -> None:
    _session.add(account)
    commit()


def update_token(id: str, token: str) -> None:
    acc: StaffAccount = _session.query(StaffAccount).get(id)
    acc.token = token
    _session.commit()


def find_by_username(username: str) -> StaffAccount | None:
    return (
        _session.query(StaffAccount)
        .filter_by(
            username=username,
        )
        .first()
    )


def find_by_token(token: str) -> StaffAccount | None:
    return _session.query(StaffAccount).filter_by(token=token).first()


def get_all() -> list[Type[StaffAccount]]:
    return _session.query(StaffAccount).all()
