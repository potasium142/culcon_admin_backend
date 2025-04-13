from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from auth import jwt_token
from db.postgresql.models.staff_account import AccountType, StaffAccount
from db.postgresql.db_session import get_session

import sqlalchemy as sqla

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


CREDENTIAL_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def permission(
    token: str,
    role_list: list[AccountType],
    session: AsyncSession,
) -> bool:
    async with session as ss, ss.begin():
        try:
            payload = jwt_token.decode(token)

            if payload.get("id") is None:
                raise CREDENTIAL_EXCEPTION

            r = await ss.execute(
                sqla.select(StaffAccount).filter(
                    StaffAccount.token == token,
                )
            )

            account = r.scalar_one_or_none()

            if account is None:
                raise CREDENTIAL_EXCEPTION

            if account.type not in role_list:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Insufficient permission",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        except InvalidTokenError:
            raise CREDENTIAL_EXCEPTION

        return True


async def manager_permission(
    token: str = Depends(oauth2_scheme),
    session=Depends(get_session),
) -> bool:
    return await permission(
        token,
        [AccountType.MANAGER],
        session,
    )


async def staff_permission(
    token: str = Depends(oauth2_scheme),
    session=Depends(get_session),
) -> bool:
    return await permission(
        token,
        [AccountType.STAFF, AccountType.MANAGER],
        session,
    )


async def shipper_permission(
    token: str = Depends(oauth2_scheme),
    session=Depends(get_session),
) -> bool:
    return await permission(token, [AccountType.SHIPPER, AccountType.MANAGER], session)


async def staff_id(
    token: str = Depends(oauth2_scheme),
    ss: AsyncSession = Depends(get_session),
) -> str:
    async with ss.begin():
        id = await ss.scalar(
            sqla.select(StaffAccount.id).filter(StaffAccount.token == token).limit(1)
        )

        if not id:
            raise CREDENTIAL_EXCEPTION

        return id
