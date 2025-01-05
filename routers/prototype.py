from typing import Annotated
from fastapi import APIRouter, Depends
from dtos.request.account import AccountCreateDto

from services import account_service as acc_sv
from db.mongodb import db, models
from db.mongodb.models.product_doc import ProductDoc

import auth

Permission = Annotated[bool, Depends(auth.manager_permission)]

router = APIRouter(prefix="/prototype", tags=["Prototype"])


@router.get("/test")
async def test():
    return {"test": "test"}


@router.post("/create", response_model=None)
async def create(account: AccountCreateDto) -> dict[str, str]:
    token = acc_sv.create_account(account)
    return {"access_token": token}


@router.get("/mongo/get")
async def get():
    return db["Blog"].find()[0]


@router.post("/mongo/save", response_model=ProductDoc)
async def save(blog: ProductDoc):
    db["Blog"].insert_one(blog.model_dump(by_alias=True))
