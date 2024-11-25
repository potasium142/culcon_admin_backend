from fastapi import APIRouter
from dtos.request.account import AccountCreateDto

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
