from sqlalchemy.ext.asyncio import AsyncSession
from db.postgresql.models.staff_account import AccountStatus, StaffAccount
from typing import Annotated

from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from db.postgresql.db_session import db_session, get_session

import auth
import sqlalchemy as sqla

from auth import encryption, jwt_token
from auth.token import Token

router = APIRouter(prefix="/api/auth", tags=["Auth"])

Session = Annotated[AsyncSession, Depends(get_session)]
JWTToken = Annotated[str, Depends(auth.oauth2_scheme)]


@router.get("/permission_test")
async def test(token: JWTToken):
    return token


@router.get("/profile")
async def get_profile(
    token: JWTToken,
    session: Session,
):
    async with session as ss, ss.begin():
        r = await ss.execute(
            sqla.select(StaffAccount).filter(
                StaffAccount.token == token,
            )
        )

        acc = r.scalar_one_or_none()

        if not acc:
            return {"error": "token is invalid"}

        return {
            "id": acc.id,
            "type": acc.type,
            "status": acc.status,
            "username": acc.username,
        }


@router.post("/login")
async def login(
    login_form: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    session: Session,
) -> Token:
    async with session as ss, ss.begin():
        r = await ss.execute(
            sqla.select(StaffAccount).filter(
                StaffAccount.username == login_form.username
            )
        )

        user = r.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=400,
                detail="No such account with username",
            )

        if user.status != AccountStatus.ACTIVE:
            raise HTTPException(
                status_code=400,
                detail="Account is locked",
            )

        is_password_match = encryption.verify(login_form.password, user.password)

        if not is_password_match:
            raise HTTPException(status_code=400, detail="Password incorrect")

        token = jwt_token.encode(user)

        user.token = token

        await db_session.commit()

        return Token(access_token=token)


@router.post("/logout")
async def logout(
    token: JWTToken,
    session: Session,
) -> dict[str, str]:
    async with session as ss, ss.begin():
        r = await ss.execute(
            sqla.select(StaffAccount).filter(
                StaffAccount.token == token,
            )
        )

        acc = r.scalar_one_or_none()

        if not acc:
            raise HTTPException(
                status_code=400,
                detail="No such account with token",
            )

        acc.token = ""

        await db_session.commit()

        return {
            "message": "Logout successfully",
        }
