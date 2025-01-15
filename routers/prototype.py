from fastapi import APIRouter, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse
from dtos.request.account import AccountCreateDto

from services import account_service as acc_sv
from db.mongodb import db
from db.mongodb.models.product_doc import ProductDoc
from time import sleep
from etc import cloudinary, progress_tracker


router = APIRouter(prefix="/test", tags=["Prototype"])


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


@router.get("/mongo/get/id")
async def get_id(id: str):
    return db["Blog"].find_one({"_id": id})


@router.post("/mongo/save", response_model=ProductDoc)
async def save(blog: ProductDoc):
    db["Blog"].insert_one(blog.model_dump(by_alias=True))


def test_stream_response(time, iter):
    for i in range(iter):
        sleep(time)
        yield f"{{{i}}}"


@router.get("/streaming_response")
async def streaming_response():
    return StreamingResponse(
        test_stream_response(1, 10), media_type="text/event-stream"
    )


@router.post("/upload_image")
async def upload(image: UploadFile):
    image_preload = await image.read()
    return cloudinary.upload(
        image=image_preload,
        dir="test",
        public_id=image.filename,
    )


pp = progress_tracker.ProgressTracker()


def create_bg_progress(id: int):
    subtask_1 = pp.new_subtask(id, "test_1")
    for i in range(11):
        pp.update_subtask(id, subtask_1, i)
        sleep(1)

    pp.close_subtask(id, subtask_1)

    subtask_2 = pp.new_subtask(id, "test_2")
    for i in range(11):
        pp.update_subtask(id, subtask_2, i)

        sleep(1)

    pp.halt(id, "oh no, anyway")


@router.get("/progress_tracker/create")
async def progress_tracker_test(bg_task: BackgroundTasks):
    id = pp.new()

    bg_task.add_task(create_bg_progress, id)

    return id


@router.get("/progress_tracker/fetch")
async def progress_tracker_test_fetch(id: int):
    return StreamingResponse(
        pp.get(id),
        media_type="text/event-stream",
    )
