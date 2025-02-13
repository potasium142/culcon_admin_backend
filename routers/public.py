from typing import Annotated
from fastapi import APIRouter, File, Request, UploadFile

from dtos.request.search import SearchPrompt
from services import public


router = APIRouter(prefix="/public", tags=["Public"])


@router.post("/search/clip")
async def search_vec_clip(
    prompt: SearchPrompt,
    req: Request,
):
    yolo_model = req.state.ai_models["clip"]
    return public.vector_search_image_clip(prompt.prompt, yolo_model)


@router.post("/search/desc")
async def search_vec_desc(
    prompt: SearchPrompt,
    req: Request,
):
    yolo_model = req.state.ai_models["clip"]
    return public.vector_search_prompt(prompt.prompt, yolo_model)


@router.post("/search/yolo")
async def search_vec_yolo(
    image: Annotated[UploadFile, File(media_type="image")],
    req: Request,
):
    yolo_model = req.state.ai_models["yolo"]

    image_preload = await image.read()

    return public.vector_search_image_yolo(image_preload, yolo_model)
