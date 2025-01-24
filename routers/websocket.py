from typing import Annotated
import uuid
from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
)

import auth

Permission = Annotated[bool, Depends(auth.staff_permission)]

router = APIRouter(prefix="/ws", tags=["WebSocket"])

chat_socket = dict[str, WebSocket]


@router.websocket("/public/chat/{id}")
async def public_chat_socket(ws: WebSocket):
    try:
        cookie = ws.cookies.get("guest_cookie")

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
