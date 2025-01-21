from typing import Annotated
from fastapi import APIRouter, Depends, WebSocket

import auth

Permission = Annotated[bool, Depends(auth.staff_permission)]

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/public/chat")
async def public_chat_socket(ws: WebSocket):
    try:
        await ws.accept()
        while True:
            data = await ws.receive_text()
            await ws.send_text(f"GOT: {data}")
    except:
        await ws.close()
