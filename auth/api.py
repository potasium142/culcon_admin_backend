from db.postgresql.models.staff_account import StaffAccount
from typing import Annotated

from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from db.postgresql.db_session import db_session

import auth
import sqlalchemy as sqla

from auth import encryption, jwt_token
from auth.token import Token

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.get("/permission_test")
async def test(token: Annotated[str, Depends(auth.oauth2_scheme)]):
    return token


@router.get("/profile")
async def get_profile(token: Annotated[str, Depends(auth.oauth2_scheme)]):
    with db_session.session as ss:
        acc = ss.execute(
            sqla.select(StaffAccount).filter(
                StaffAccount.token == token,
            )
        ).scalar_one()

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
) -> Token:
    with db_session.session as ss:
        user = ss.execute(
            sqla.select(StaffAccount).filter(
                StaffAccount.username == login_form.username
            )
        ).scalar_one()

        if not user:
            raise HTTPException(
                status_code=400,
                detail="No such account with username",
            )

        is_password_match = encryption.verify(login_form.password, user.password)

        if not is_password_match:
            raise HTTPException(status_code=400, detail="Password incorrect")

        token = jwt_token.encode(user)

        user.token = token

        db_session.commit()

        return Token(access_token=token)


@router.post("/logout")
async def logout(token: str) -> dict[str, str]:
    with db_session.session as ss:
        acc = ss.execute(
            sqla.select(StaffAccount).filter(
                StaffAccount.token == token,
            )
        ).scalar_one()

        if not acc:
            raise HTTPException(
                status_code=400,
                detail="No such account with token",
            )

        acc.token = ""

        db_session.commit()

        return {
            "message": "Logout successfully",
        }
