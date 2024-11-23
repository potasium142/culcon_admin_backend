from db.models.account import Account, EmployeeInfo
from typing_extensions import List
from db import DBSession
import sqlalchemy.orm


_session: sqlalchemy.orm.Session = DBSession()


def commit() -> None:
    _session.commit()


def add_account(account: Account) -> None:
    _session.add(account)


def add_employee_info(employee_info: EmployeeInfo) -> None:
    _session.add(employee_info)


def add_employee(account: Account,
                 employee_info: EmployeeInfo) -> None:
    _session.add_all(account, employee_info)
    _session.commit()


def authen_user(username: str, password: str) -> Account | None:
    return _session\
        .query(Account)\
        .filter_by(
            Account.username == username
        )


def get_all() -> List[Account]:
    return _session.query(Account).all()
