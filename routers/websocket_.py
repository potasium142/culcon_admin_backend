import datetime
from enum import Enum
from typing import Annotated
from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
)
from db.postgresql.db_session import db_session

import auth
from db.postgresql.models.chat import ChatHistory
from db.postgresql.models.staff_account import StaffAccount
from db.postgresql.models.user_account import UserAccount

Permission = Annotated[bool, Depends(auth.staff_permission)]

router = APIRouter(prefix="/ws", tags=["WebSocket"])


class MsgType(str, Enum):
    MSG = "msg"
    INFO = "info"
    DATA = "data"
    ERROR = "error"


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
        # print("are we close yet?")
        close = (not self.customer_ws) and (not self.staff_ws)
        # print("yes?" if close else "no???")
        return close

    async def __connect(
        self,
        src: WebSocket,
        target: WebSocket | None,
        name: str,
    ):
        src_ws = src
        target_ws = target

        await src_ws.send_json({
            "sender": "system",
            "timestamp": str(datetime.datetime.now()),
            "type": MsgType.DATA,
            "chatlog": self.chat_history,
        })

        if target_ws:
            await target_ws.send_json({
                "sender": "system",
                "timestamp": str(datetime.datetime.now()),
                "type": MsgType.INFO,
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
        del msg["type"]
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
            "type": MsgType.INFO,
            "info": f"{self.cid} has left the chat.",
        }
        if self.staff_ws:
            await self.staff_ws.send_json(msg)

    async def s_left_chat(self):
        self.staff_ws = None
        msg = {
            "sender": "system",
            "timestamp": str(datetime.datetime.now()),
            "type": MsgType.INFO,
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
    token: str = "",
):
    with db_session.session as ss:
        staff = ss.query(StaffAccount).filter_by(token=token).first()
        customer = ss.get(UserAccount, id)

    try:
        await ws.accept()

        if not customer:
            await ws.send_json({
                "sender": "system",
                "timestamp": str(datetime.datetime.now()),
                "type": MsgType.ERROR,
                "msg": f'User with id "{id}" does not exist',
            })
            await ws.close()
            return

        if not staff:
            await ws.send_json({
                "sender": "system",
                "timestamp": str(datetime.datetime.now()),
                "type": MsgType.ERROR,
                "msg": "Staff token is invalid",
            })
            await ws.close()
            return

        if id not in chatlist:
            chatlist[id] = ChatInstance(id)

        await chatlist[id].s_connect(ws)

        await ws.send_json({
            "sender": "system",
            "timestamp": str(datetime.datetime.now()),
            "type": MsgType.INFO,
            "customer_profile": {
                "pfp": customer.profile_pic_uri,
                "username": customer.username,
                "id": customer.id,
            },
        })
        while True:
            data = await ws.receive_text()
            await chatlist[id].s_send_msg({
                "sender": "staff",
                "timestamp": str(datetime.datetime.now()),
                "type": MsgType.MSG,
                "msg": data,
            })
    except WebSocketDisconnect:
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

    id = ""

    try:
        await ws.accept()

        if not user:
            await ws.send_json({
                "sender": "system",
                "timestamp": str(datetime.datetime.now()),
                "type": MsgType.ERROR,
                "msg": "User token is invalid",
            })
            await ws.close()
            return

        id = str(user.id)

        if id not in chatlist:
            chatlist[id] = ChatInstance(id)

        await chatlist[id].c_connect(ws)

        while True:
            data = await ws.receive_text()
            await chatlist[id].c_send_msg({
                "sender": id,
                "timestamp": str(datetime.datetime.now()),
                "type": MsgType.MSG,
                "msg": data,
            })

    except WebSocketDisconnect as _:
        await chatlist[id].c_left_chat()

        if chatlist[id].closable():
            chatlist[id].save_chat_history()
            del chatlist[id]
