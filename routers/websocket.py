from typing import Annotated
import uuid
from fastapi import (
    APIRouter,
    Depends,
    Header,
    Request,
    WebSocket,
    WebSocketDisconnect,
    Cookie,
    Response,
)
from db.postgresql.db_session import db_session

import auth
from db.postgresql.models.user_account import UserAccount
from dtos.request import ws

Permission = Annotated[bool, Depends(auth.staff_permission)]

router = APIRouter(prefix="/ws", tags=["WebSocket"])

chat_socket: dict[str, WebSocket] = dict()


@router.get("/chat/queue")
async def get_chat_queue():
    return [k for k, _ in chat_socket.items()]


@router.websocket("/chat/connect/{id}")
async def connect_customer_chat(ws: WebSocket, id: str):
    try:
        await ws.accept()
        while True:
            data = await ws.receive_text()
            await chat_socket[id].send_text(f"staff: {data}")
    except WebSocketDisconnect:
        await ws.close()


@router.websocket("/chat/customer")
async def customer_chat(
    *,
    ws: WebSocket,
    token: Annotated[str | None, Header()] = None,
):
    print(token)
    user = None
    with db_session.session as ss:
        user = ss.query(UserAccount).filter_by(token=token).first()

    if not user:
        raise Exception("User token invalid")

    chat_id = str(user.id)

    try:
        await ws.accept()

        chat_socket[chat_id] = ws

        while True:
            data = await ws.receive_text()
            await ws.send_text(f"customer: {data}")
    except WebSocketDisconnect:
        await ws.close()
        del chat_socket[chat_id]
