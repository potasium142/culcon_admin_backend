import sqlalchemy.orm

from db.postgresql import DBSession
from db.postgresql.models.staff_account import StaffAccount

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
    with _session as ss:
        acc: StaffAccount = ss.get(StaffAccount, id)

        if not acc:
            raise Exception("Account not exist")

        acc.token = token

        commit()


def find_by_username(username: str) -> StaffAccount | None:
    with _session as ss:
        try:
            return (
                ss.query(StaffAccount)
                .filter_by(
                    username=username,
                )
                .first()
            )
        except Exception as e:
            ss.rollback()
            raise (e)


def find_by_token(token: str) -> StaffAccount | None:
    return _session.query(StaffAccount).filter_by(token=token).first()


def get_all() -> list[StaffAccount]:
    return _session.query(StaffAccount).all()
