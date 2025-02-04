from typing import Annotated
import uuid
from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    Cookie,
    Response,
)

import auth

Permission = Annotated[bool, Depends(auth.staff_permission)]

router = APIRouter(prefix="/ws", tags=["WebSocket"])

chat_socket = dict[str, WebSocket]


@router.get("/create/public/session")
async def connect_chat_session(
    res: Response,
    cookie: Annotated[str | None, Cookie()] = None,
):
    if not cookie:
        res.set_cookie(key="test", value="test", max_age=36000000)
    print(cookie)


@router.websocket("/public/chat/{id}")
async def public_chat_socket(ws: WebSocket):
    try:
        cookie = ws.cookies.get("test")

        await ws.accept()

        if not cookie:
            ws.cookies["guest_cookie"] = str(uuid.uuid4())
            await ws.send_text("Generate cookie")

        await ws.send_text(f"GOT: {ws.cookies['guest_cookie']}")
        while True:
            data = await ws.receive_text()
            await ws.send_text(f"GOT: {data}")
    except WebSocketDisconnect:
        await ws.close()
