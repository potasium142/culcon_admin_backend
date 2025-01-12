from typing import Annotated
from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import StreamingResponse
from dtos.request.account import AccountCreateDto

from services import account_service as acc_sv
from db.mongodb import db
from db.mongodb.models.product_doc import ProductDoc
from time import sleep
from etc import cloudinary

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


def test_stream_response(time, iter):
    for i in range(iter):
        sleep(time)
        yield f"{{{i}}}"


@router.get("/test/streaming_response")
async def streaming_response():
    return StreamingResponse(
        test_stream_response(1, 10), media_type="text/event-stream"
    )


@router.post("/test/upload_image")
async def upload(image: UploadFile):
    image_preload = await image.read()
    return cloudinary.upload(
        image=image_preload,
        dir="test",
        public_id=image.filename,
    )
