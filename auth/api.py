from db.postgresql.models.user_account import UserAccount
from db.postgresql.repos import account_repo
from typing import Annotated

from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from db.postgresql.db_session import db_session

import auth

from auth import encryption, jwt_token
from auth.token import Token

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.get("/permission_test")
async def test(token: Annotated[str, Depends(auth.oauth2_scheme)]):
    return "ok"


@router.post("/login")
async def login(
    login_form: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
) -> Token:
    user = account_repo.find_by_username(
        login_form.username,
    )

    if not user:
        raise HTTPException(
            status_code=400,
            detail="No such account with username",
        )

    is_password_match = encryption.verify(login_form.password, user.password)

    if not is_password_match:
        raise HTTPException(status_code=400, detail="Password incorrect")

    token = jwt_token.encode(user)

    account_repo.update_token(user.id, token)

    return Token(access_token=token)


@router.post("/logout")
async def logout(token: str) -> dict[str, str]:
    user = account_repo.find_by_token(token)

    if not user:
        raise HTTPException(
            status_code=400,
            detail="No such account with token",
        )

    account_repo.update_token(user.id, "")

    return {
        "message": "Logout successfully",
    }
