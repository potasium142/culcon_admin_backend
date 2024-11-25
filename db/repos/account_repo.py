from db.models.account import Account, EmployeeInfo
from typing_extensions import List
from db import DBSession
import sqlalchemy.orm

from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError

_session: sqlalchemy.orm.Session = DBSession()


def commit() -> None:
    try:
        _session.commit()
    except Exception as e:
        print(e)
        _session.rollback()


def add_account(account: Account) -> None:
    _session.add(account)
    commit()
    # try:
    #     _session.add(account)
    #     _session.commit()
    # except (UniqueViolation, IntegrityError) as e:
    #     _session.rollback()
    #     return {"error": e}


def add_employee_info(employee_info: EmployeeInfo) -> None | dict:
    try:
        _session.add(employee_info)
    except (UniqueViolation, IntegrityError) as e:
        _session.rollback()
        return {"error": e.pgerror}


def add_employee(account: Account,
                 employee_info: EmployeeInfo) -> None:
    try:
        _session.add_all(account, employee_info)
        _session.commit()
    except (UniqueViolation, IntegrityError) as e:
        _session.rollback()
        return {"error": e.pgerror}


def authen_user(username: str, password: str) -> Account | None:
    return _session\
        .query(Account)\
        .filter_by(
            username=username,
            password=password
        )


def get_all() -> List[Account]:
    return _session.query(Account).all()
