from typing_extensions import List
from db.models.account import Account, AccountType
from dtos.request.account import AccountCreateDto

from db.repos import account_repo as repos

from auth import encryption


def create_account(account_dto: AccountCreateDto) -> None:
    account = account_dto.get_account()
    hashed_password = encryption.hash(account.password)

    account.password = hashed_password

    account.token = ""
    repos.add_account(account=account)
    repos.commit()
