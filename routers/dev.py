from typing import Annotated
from fastapi import APIRouter, Depends
from dtos.request.account import AccountCreateDto
from services import account_service as acc_sv

import auth

Permission = Annotated[bool, Depends(auth.manager_permission)]

router = APIRouter(prefix="/dev", tags=["Dev"])


@router.post("/create", response_model=None)
async def create(account: AccountCreateDto) -> dict[str, str]:
    token = acc_sv.create_account(account)
    return {"access_token": token}


@router.get("/cors_test")
async def cors() -> str:
    return "CORS"
