from db.repos import account_repo
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter

import auth

router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"]
)


@router.get("/permission_test")
async def test(token: Annotated[str, Depends(auth.oauth2_scheme)]):
    return "ok"


@router.post("/login")
async def login(login_form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = account_repo.authen_user(
        login_form.username,
        login_form.password
    )

    if not user:
        raise HTTPException(
            status_code=400,
            detail="No such account with username and password"
        )

    return "some fake ass token"
