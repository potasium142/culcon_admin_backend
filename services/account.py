from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from dtos.request.account import AccountCreateDto
from datetime import timedelta

from auth import encryption, jwt_token

from etc.local_error import HandledError


async def create_account(
    account_dto: AccountCreateDto,
    session: AsyncSession,
) -> str:
    async with session as ss, ss.begin():
        try:
            account = account_dto.get()
            hashed_password = encryption.hash(account.password)

            account.password = hashed_password

            token = jwt_token.encode(account, timedelta(hours=1))
            account.token = token

            ss.add(account)

            await ss.commit()

        except IntegrityError as e:
            raise HandledError(e._message())

    return account.token
