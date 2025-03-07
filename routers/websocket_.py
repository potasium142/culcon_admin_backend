import datetime
from typing import Annotated
from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
)
from db.postgresql.db_session import db_session

import auth
from db.postgresql.models.chat import ChatHistory
from db.postgresql.models.user_account import UserAccount

Permission = Annotated[bool, Depends(auth.staff_permission)]

router = APIRouter(prefix="/ws", tags=["WebSocket"])


class ChatInstance:
    def __init__(
        self,
        cid: str,
    ) -> None:
        self.customer_ws: WebSocket | None = None
        self.staff_ws: WebSocket | None = None
        self.chat_history = self.load_chat_history(cid)
        self.cid = cid

    def closable(self):
        print("are we close yet?")
        close = (not self.customer_ws) and (not self.staff_ws)
        print("yes?" if close else "no???")
        return close

    async def __connect(
        self,
        src: WebSocket,
        target: WebSocket | None,
        name: str,
    ):
        src_ws = src
        target_ws = target
        await src_ws.send_json(self.chat_history)

        if target_ws:
            await target_ws.send_json({
                "sender": "system",
                "timestamp": str(datetime.datetime.now()),
                "info": f"{name} joined the chat",
            })

    async def s_connect(self, ws: WebSocket):
        self.staff_ws = ws
        await self.__connect(self.staff_ws, self.customer_ws, "staff")

    async def c_connect(self, ws: WebSocket):
        self.customer_ws = ws
        await self.__connect(self.customer_ws, self.staff_ws, self.cid)

    def load_chat_history(
        self,
        cid: str,
    ):
        with db_session.session as ss:
            chat_history = ss.get(ChatHistory, cid)

        if chat_history:
            chatlog = chat_history.chatlog
        else:
            chatlog: list[dict[str, str]] = []

        return chatlog[-14:]

    def save_chat_history(self):
        with db_session.session as ss:
            chat_history = ss.get(ChatHistory, self.cid)

            if chat_history:
                chatlog = chat_history.chatlog
            else:
                chatlog = []

            chatlog[-14:] = self.chat_history

            chat_history = ChatHistory(id=self.cid, chatlog=chatlog)

            ss.merge(chat_history)
            ss.commit()

    async def __send_msg(
        self,
        msg: dict[str, str],
        receiver: WebSocket | None,
    ):
        if receiver:
            await receiver.send_json(msg)
        self.chat_history.append(msg)

    async def c_send_msg(self, msg: dict[str, str]):
        await self.__send_msg(msg, self.staff_ws)

    async def s_send_msg(self, msg: dict[str, str]):
        await self.__send_msg(msg, self.customer_ws)

    async def c_left_chat(self):
        self.customer_ws = None
        msg = {
            "sender": "system",
            "timestamp": str(datetime.datetime.now()),
            "info": f"{self.cid} has left the chat.",
        }
        if self.staff_ws:
            await self.staff_ws.send_json(msg)

    async def s_left_chat(self):
        self.staff_ws = None
        msg = {
            "sender": "system",
            "timestamp": str(datetime.datetime.now()),
            "info": "staff has left the chat.",
        }

        if self.customer_ws:
            await self.customer_ws.send_json(msg)


chatlist: dict[str, ChatInstance] = dict()


@router.get("/chat/queue")
async def get_chat_queue():
    return [k for k, _ in chatlist.items()]


@router.websocket("/chat/connect/{id}")
async def connect_customer_chat(
    ws: WebSocket,
    id: str,
):
    try:
        await ws.accept()

        if id not in chatlist:
            chatlist[id] = ChatInstance(id)

        await chatlist[id].s_connect(ws)

        while True:
            data = await ws.receive_text()
            await chatlist[id].s_send_msg({
                "sender": "staff",
                "timestamp": str(datetime.datetime.now()),
                "msg": data,
            })
    except Exception:
        await chatlist[id].s_left_chat()

        if chatlist[id].closable():
            chatlist[id].save_chat_history()
            del chatlist[id]


@router.websocket("/chat/customer")
async def customer_chat(
    ws: WebSocket,
    token: str = "",
):
    with db_session.session as ss:
        user = ss.query(UserAccount).filter_by(token=token).first()

    if not user:
        raise Exception("User token invalid")

    id = str(user.id)

    try:
        await ws.accept()

        if id not in chatlist:
            chatlist[id] = ChatInstance(id)

        await chatlist[id].c_connect(ws)

        while True:
            data = await ws.receive_text()
            await chatlist[id].c_send_msg({
                "sender": id,
                "timestamp": str(datetime.datetime.now()),
                "msg": data,
            })

    except Exception as _:
        await chatlist[id].c_left_chat()

        if chatlist[id].closable():
            chatlist[id].save_chat_history()
            del chatlist[id]
