from dtos.request.account import AccountCreateDto
from datetime import timedelta

from auth import encryption, jwt_token

from db.postgresql.db_session import db_session


def create_account(account_dto: AccountCreateDto) -> str:
    account = account_dto.get()
    hashed_password = encryption.hash(account.password)

    account.password = hashed_password

    token = jwt_token.encode(account, timedelta(hours=1))
    account.token = token

    db_session.session.add(account)
    db_session.commit()

    return account.token
