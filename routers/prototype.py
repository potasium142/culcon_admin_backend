from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from dtos.request.account import AccountCreateDto

from services import account_service as acc_sv, public
from time import sleep
from etc import progress_tracker


router = APIRouter(prefix="/test", tags=["Prototype"])


@router.get("/test")
async def test():
    return {"test": "test"}


@router.post("/create", response_model=None)
async def create(account: AccountCreateDto) -> dict[str, str]:
    token = acc_sv.create_account(account)
    return {"access_token": token}


def test_stream_response(time, iter):
    for i in range(iter):
        sleep(time)
        yield f"{{{i}}}"


@router.get("/streaming_response")
async def streaming_response():
    return StreamingResponse(
        test_stream_response(1, 10), media_type="text/event-stream"
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


@router.get("/vector/search")
async def search_vec(
    prompt: str,
    req: Request,
):
    yolo_model = req.state.ai_models["clip"]
    return public.vector_search_image_clip(prompt, yolo_model)
