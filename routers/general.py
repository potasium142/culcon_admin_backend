from fastapi import APIRouter
from services import product as ps
from fastapi.responses import StreamingResponse
from etc.progress_tracker import pp

import auth


router = APIRouter(prefix="/api/general", tags=["General"])

oauth2_scheme = auth.oauth2_scheme


@router.get("/product/get")
async def get_product(prod_id: str):
    return ps.get_product(prod_id)


@router.get("/product/get_all")
async def get_all_product():
    return ps.get_list_product()


@router.get("/progress/get")
async def get_progress(prog_id: int):
    return StreamingResponse(
        pp.get(prog_id),
        media_type="text/event-stream",
    )
