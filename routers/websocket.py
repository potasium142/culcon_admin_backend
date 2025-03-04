import datetime
import time
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
    WebSocketException,
)
import fastapi
from sqlalchemy.testing.config import ident
from db.postgresql.db_session import db_session

import auth
from db.postgresql.models.chat import ChatHistory
from db.postgresql.models.user_account import UserAccount

Permission = Annotated[bool, Depends(auth.staff_permission)]

router = APIRouter(prefix="/ws", tags=["WebSocket"])


class ChatSession:
    def __init__(self, id: str):
        self.id = id
        self.connection: dict[str, WebSocket] = dict()
        self.chatlog: list[dict[str, str]] = self.__load_chatlog(id)
        self.staff_connected: bool = False
        self.chatlog_existed: bool = True

    def __load_chatlog(self, id):
        with db_session.session as ss:
            chatlog = ss.get(ChatHistory, id)

            if not chatlog:
                self.chatlog_existed = False
                chatlog = list()

        return chatlog[-14:]

    async def connect(self, ws: WebSocket):
        id: str = str(uuid.uuid4())
        await ws.accept()
        self.connection[id] = ws
        for _, c in self.connection.items():
            await c.send_json(self.chatlog)

        return id

    def set_connection(self, con: bool):
        self.staff_connected = con

    async def boardcast(self, msg: dict[str, str]):
        self.chatlog.append(msg)
        for _, c in self.connection.items():
            await c.send_json(msg)

    def end_session(self):
        if len(self.connection) != 0:
            print("nun uh")
            return False
        chat_history = ChatHistory(
            id=self.id,
            chatlog=self.chatlog,
        )

        with db_session.session as ss:
            if self.chatlog_existed:
                ss.merge(chat_history)
            else:
                ss.add(chat_history)

        db_session.commit()

        return True

    async def close_connection(self, id: str, role: str):
        # await self.boardcast({
        #     "timestamp": str(datetime.datetime.now()),
        #     "info": f"{role} has left the chat.",
        # })
        # await self.connection[id].close()
        del self.connection[id]
        self.end_session()

    def removable(self):
        return len(self.connection) == 0


chat_socket: dict[str, ChatSession] = dict()


@router.get("/chat/queue")
async def get_chat_queue():
    return [k for k, _ in chat_socket.items()]


@router.websocket("/chat/connect/{id}")
async def connect_customer_chat(
    ws: WebSocket,
    id: str,
):
    if id not in chat_socket:
        raise WebSocketException(
            fastapi.status.WS_1008_POLICY_VIOLATION,
            "Session not exist",
        )

    if chat_socket[id].staff_connected:
        raise WebSocketException(
            fastapi.status.WS_1008_POLICY_VIOLATION,
            "Staff already connected",
        )

    ws_id = None
    try:
        ws_id = await chat_socket[id].connect(ws)
        chat_socket[id].set_connection(True)
        while True:
            data = await ws.receive_text()
            await chat_socket[id].boardcast({
                "sender": "staff",
                "timestamp": str(datetime.datetime.now()),
                "msg": data,
            })
        # await self.boardcast({
        #     "timestamp": str(datetime.datetime.now()),
        #     "info": f"{role} has left the chat.",
        # })
    except WebSocketDisconnect:
        chat_socket[id].set_connection(False)
        if ws_id:
            await chat_socket[id].close_connection(ws_id, "Staff")

        if chat_socket[id].removable():
            del chat_socket[id]


@router.websocket("/chat/customer")
async def customer_chat(
    ws: WebSocket,
    token: str = "",
    # token: Annotated[str | None, Header()] = None,
):
    with db_session.session as ss:
        user = ss.query(UserAccount).filter_by(token=token).first()

    if not user:
        raise Exception("User token invalid")

    chat_id = str(user.id)

    ws_id = None
    try:
        if chat_id not in chat_socket:
            chat_socket[chat_id] = ChatSession(chat_id)

        ws_id = await chat_socket[chat_id].connect(ws)

        while True:
            data = await ws.receive_text()
            await chat_socket[chat_id].boardcast({
                "sender": chat_id,
                "timestamp": str(datetime.datetime.now()),
                "msg": data,
            })

    except WebSocketDisconnect as _:
        # await chat_socket[chat_id].boardcast({
        #     "timestamp": str(datetime.datetime.now()),
        #     "info": f"{chat_id} has left the chat.",
        # })
        if ws_id:
            await chat_socket[chat_id].close_connection(ws_id, "Customer")

        if chat_socket[chat_id].removable():
            del chat_socket[chat_id]
