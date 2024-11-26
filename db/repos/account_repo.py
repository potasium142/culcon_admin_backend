from db.models.account import Account, EmployeeInfo
from typing_extensions import List
from db import DBSession
import sqlalchemy.orm

_session: sqlalchemy.orm.Session = DBSession()


def commit() -> None:
    try:
        _session.commit()
    except Exception as e:
        _session.rollback()
        raise e


def add_account(account: Account) -> None:
    _session.add(account)
    commit()


def update_token(id: str, token: str) -> None:
    acc: Account = _session\
        .query(Account)\
        .get(id)
    acc.token = token
    _session.commit()


def find_by_username(username: str) -> Account | None:
    return _session\
        .query(Account)\
        .filter_by(
            username=username,
        )\
        .first()


def find_by_token(token: str) -> Account | None:
    return _session\
        .query(Account)\
        .filter_by(
            token=token
        )\
        .first()


def get_all() -> List[Account]:
    return _session.query(Account).all()
