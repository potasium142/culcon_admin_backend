from typing import Annotated
from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgresql.db_session import get_session
from db.postgresql.models.product import ProductType
from dtos.request.search import SearchPrompt
from services import public

from db.postgresql.paging import Page, page_param

Paging = Annotated[Page, Depends(page_param)]
Session = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(prefix="/public", tags=["Public"])


@router.post("/search/desc")
async def search_vec_desc(
    prompt: SearchPrompt,
    req: Request,
    pg: Paging,
    ss: Session,
    type: ProductType | None = None,
):
    yolo_model = req.state.ai_models["clip"]
    return await public.vector_search_prompt(
        prompt.prompt,
        yolo_model,
        type,
        pg,
        ss,
    )


@router.post("/search/image")
async def search_vec_yolo(
    image: Annotated[UploadFile, File(media_type="image")],
    req: Request,
    pg: Paging,
    ss: Session,
    type: ProductType | None = None,
):
    yolo_model = req.state.ai_models["yolo"]
    clip_model = req.state.ai_models["clip"]

    image_preload = await image.read()

    return await public.vector_search_image_yolo(
        image_preload,
        yolo_model,
        clip_model,
        type,
        pg,
        ss,
    )


@router.post("/search/blog")
async def search_vec_blog(
    req: Request,
    pg: Paging,
    ss: Session,
    prompt: str,
):
    clip_model = req.state.ai_models["clip"]

    return await public.vector_search_blog(
        prompt,
        clip_model,
        pg,
        ss,
    )
