import enum
from typing import Annotated
from dtos.request import product as prod
from fastapi import APIRouter, Depends, File, Request, UploadFile, BackgroundTasks
from services import product as ps
from fastapi.responses import StreamingResponse
from etc.progress_tracker import ProgressTracker, Status

import auth

Permission = Annotated[bool, Depends(auth.staff_permission)]

router = APIRouter(prefix="/api/staff", tags=["Staff"])

oauth2_scheme = auth.oauth2_scheme

pp = ProgressTracker()


@router.get("/permission_test")
async def test(permission: Permission):
    return "ok"


@router.post("/product/create")
async def create_product(
    bg_task: BackgroundTasks,
    req: Request,
    product_detail: prod.ProductCreation,
    main_image: Annotated[UploadFile, File(media_type="image")],
    additional_images: list[Annotated[UploadFile, File(media_type="image")]]
    | None = None,
):
    bg_id = pp.new()
    yolo_model = req.state.ai_models["yolo"]
    clip_model = req.state.ai_models["clip"]

    mip = pp.new_subtask(bg_id, "Preloaded main")

    main_image_preload = await main_image.read()

    additional_images_preload: list[bytes] = []

    if additional_images:
        for i, f in enumerate(additional_images):
            img = await f.read()
            additional_images_preload.append(img)
            pp.update_subtask(bg_id, mip, progress=i + 1)

    pp.close_subtask(
        bg_id,
        mip,
    )
    bg_task.add_task(
        ps.create_product,
        product_detail,
        additional_images_preload,
        main_image_preload,
        yolo_model,
        clip_model,
        pp,
        bg_id,
    )

    return {
        "progress_id": bg_id,
    }


@router.post("/mealkit/create")
async def create_mealkit(
    bg_task: BackgroundTasks,
    req: Request,
    product_detail: prod.MealKitCreation,
    main_image: Annotated[UploadFile, File(media_type="image")],
    additional_images: list[Annotated[UploadFile, File(media_type="image")]]
    | None = None,
):
    bg_id = pp.new()
    yolo_model = req.state.ai_models["yolo"]
    clip_model = req.state.ai_models["clip"]

    mip = pp.new_subtask(bg_id, "Preloaded main")

    main_image_preload = await main_image.read()

    additional_images_preload: list[bytes] = []

    if additional_images:
        for i, f in enumerate(additional_images):
            img = await f.read()
            additional_images_preload.append(img)
            pp.update_subtask(bg_id, mip, progress=i + 1)

    pp.close_subtask(
        bg_id,
        mip,
    )

    bg_task.add_task(
        ps.mealkit_creation,
        product_detail,
        additional_images_preload,
        main_image_preload,
        yolo_model,
        clip_model,
        pp,
        bg_id,
    )

    return {
        "progress_id": bg_id,
    }


@router.put("/product/price/update")
async def update_price(
    product_id: str,
    price: float,
    sale_percent: float,
):
    ps.update_price(
        product_id,
        price,
        sale_percent,
    )
    return {"message": "Price updated"}


@router.get("/product/get")
async def get_product(prod_id: str) -> dict:
    return ps.get_product(prod_id)


@router.get("/progress/get")
async def get_progress(prog_id: int):
    return StreamingResponse(
        pp.get(prog_id),
        media_type="text/event-stream",
    )
