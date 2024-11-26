from db.repos import account_repo
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter

import auth

from auth import encryption,  jwt_token
from auth.token import Token

router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"]
)


@router.get("/permission_test")
async def test(token: Annotated[str, Depends(auth.oauth2_scheme)]):
    return "ok"


@router.post("/login")
async def login(login_form: Annotated[
    OAuth2PasswordRequestForm,
    Depends()
]) -> Token:

    user = account_repo.find_by_username(
        login_form.username,
    )

    if not user:
        raise HTTPException(
            status_code=400,
            detail="No such account with username"
        )

    is_password_match = encryption.verify(login_form.password, user.password)

    if not is_password_match:
        raise HTTPException(
            status_code=400,
            detail="Password incorrect"
        )

    token = jwt_token.encode(user)

    account_repo.update_token(user.id, token)

    return Token(access_token=token, token_type="bearer")
