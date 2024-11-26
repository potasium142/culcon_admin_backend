from typing_extensions import List
from db.models.account import Account, AccountType
from dtos.request.account import AccountCreateDto
from datetime import datetime, timedelta, timezone

from db.repos import account_repo as repos

from auth import encryption, jwt_token


def create_account(account_dto: AccountCreateDto) -> str:
    account = account_dto.get_account()
    hashed_password = encryption.hash(account.password)

    account.password = hashed_password

    token = jwt_token.encode(account, timedelta(hours=1))
    account.token = token

    repos.add_account(account=account)

    return account.token
