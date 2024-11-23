from typing_extensions import List
from db.models.account import Account, AccountType
from dtos.request.account import AccountCreateDto

from db.repos import account_repo as repos


def create_account(account_dto: AccountCreateDto) -> None:
    account = account_dto.get_account()

    repos.add_account(account=account)
    repos.commit()
