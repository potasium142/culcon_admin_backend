from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgresql.db_session import get_session
from dtos.request.account import AccountCreateDto
from services import account as acc_sv

import auth

Permission = Annotated[bool, Depends(auth.manager_permission)]

router = APIRouter(prefix="/dev", tags=["Dev"])

Session = Annotated[AsyncSession, Depends(get_session)]


@router.post("/create", response_model=None)
async def create(account: AccountCreateDto, session: Session) -> dict[str, str]:
    token = await acc_sv.create_account(account, session)
    return {"access_token": token}


@router.get("/cors_test")
async def cors() -> str:
    return "CORS"
