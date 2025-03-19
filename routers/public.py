from typing import Annotated
from fastapi import APIRouter, Depends, File, Request, UploadFile

from dtos.request.search import SearchPrompt
from services import public

from db.postgresql.paging import Page, page_param

Paging = Annotated[Page, Depends(page_param)]

router = APIRouter(prefix="/public", tags=["Public"])


@router.post("/search/desc")
async def search_vec_desc(
    prompt: SearchPrompt,
    req: Request,
    pg: Paging,
):
    yolo_model = req.state.ai_models["clip"]
    return public.vector_search_prompt(
        prompt.prompt,
        yolo_model,
        pg,
    )


@router.post("/search/image")
async def search_vec_yolo(
    image: Annotated[UploadFile, File(media_type="image")],
    req: Request,
    pg: Paging,
):
    yolo_model = req.state.ai_models["yolo"]
    clip_model = req.state.ai_models["clip"]

    image_preload = await image.read()

    return public.vector_search_image_yolo(
        image_preload,
        yolo_model,
        clip_model,
        pg,
    )
