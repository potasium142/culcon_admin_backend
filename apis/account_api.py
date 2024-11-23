from fastapi import APIRouter
from db.models.account import Account
from services import account_service
from dtos.request.account import AccountCreateDto
import db

from services import account_service as acc_sv

router = APIRouter(
    prefix="/api/account",
    tags=["Account"]
)


@router.get("/test")
async def test():
    return {"test": "test"}


@router.post("/create", response_model=None)
async def create(account: AccountCreateDto) -> str:
    acc_sv.create_account(account)
    return "ok"
