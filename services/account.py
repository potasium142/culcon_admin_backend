from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgresql.models.shipper import ShipperAvailbility
from db.postgresql.models.staff_account import AccountType, StaffAccount
import sqlalchemy as sqla
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

            await ss.flush()

            if account.type == AccountType.SHIPPER:
                acc_id = await ss.scalar(
                    sqla.select(StaffAccount.id)
                    .filter(
                        StaffAccount.type == AccountType.SHIPPER,
                        StaffAccount.token == token,
                    )
                    .limit(1)
                )

                if not acc_id:
                    raise HandledError("Cannot find account after created")

                shipper_info = ShipperAvailbility(id=acc_id)

                ss.add(shipper_info)
                await ss.flush()

        except IntegrityError as e:
            raise HandledError(e._message())

    return account.token
