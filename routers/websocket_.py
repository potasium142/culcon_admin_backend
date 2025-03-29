import datetime
from enum import Enum
from typing import Annotated
from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
)
import sqlalchemy as sqla
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgresql.db_session import get_session

import auth
from db.postgresql.models.chat import ChatSession
from db.postgresql.models.staff_account import StaffAccount
from db.postgresql.models.user_account import UserAccount
from db.postgresql.paging import Page, display_page, page_param, paging, table_size

Permission = Annotated[bool, Depends(auth.staff_permission)]

Session = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(prefix="/ws", tags=["WebSocket"])

Paging = Annotated[Page, Depends(page_param)]


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

    async def c_connect(self, ws: WebSocket, ss: AsyncSession):
        self.customer_ws = ws
        await self.__connect(self.customer_ws, self.staff_ws, self.cid)
        await self.toggle_connection_status(True, ss)

    async def toggle_connection_status(self, status: bool, ss: AsyncSession):
        chat_session = await ss.get(ChatSession, self.cid)
        if chat_session:
            chat_session.connected = status
        else:
            chat_session = ChatSession(
                id=self.cid,
                chatlog=[],
                connected=status,
            )
        await ss.commit()

    async def load_chat_history(
        self,
        ss: AsyncSession,
    ):
        chat_history = await ss.get(ChatSession, self.cid)

        if chat_history:
            chatlog = chat_history.chatlog
        else:
            chatlog: list[dict[str, str]] = []

        self.chat_history = chatlog[-14:]

        return self.chat_history

    async def save_chat_history(
        self,
        ss: AsyncSession,
    ):
        chat_history = await ss.get(ChatSession, self.cid)

        if chat_history:
            chatlog = chat_history.chatlog
        else:
            chatlog = []

        chatlog[-14:] = self.chat_history

        chat_history = ChatSession(id=self.cid, chatlog=chatlog)

        await ss.merge(chat_history)
        await ss.commit()

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

    async def c_left_chat(self, ss: AsyncSession):
        self.customer_ws = None
        msg = {
            "sender": "system",
            "timestamp": str(datetime.datetime.now()),
            "type": MsgType.INFO,
            "info": f"{self.cid} has left the chat.",
        }
        await self.save_chat_history(ss)
        await self.toggle_connection_status(False, ss)
        if self.staff_ws:
            await self.staff_ws.send_json(msg)

    async def s_left_chat(self, ss: AsyncSession):
        self.staff_ws = None
        msg = {
            "sender": "system",
            "timestamp": str(datetime.datetime.now()),
            "type": MsgType.INFO,
            "info": "staff has left the chat.",
        }
        await self.save_chat_history(ss)
        if self.customer_ws:
            await self.customer_ws.send_json(msg)


chatlist: dict[str, ChatInstance] = dict()


@router.get("/chat/queue")
async def get_chat_queue(
    page: Paging,
    ss: Session,
):
    async with ss.begin():
        chatlist = await ss.scalars(
            paging(
                sqla.select(
                    ChatSession,
                ),
                page,
            )
        )

        content = []

        for ci in chatlist:
            user: UserAccount = await ci.awaitable_attrs.user
            content.append({
                "id": ci.id,
                "username": user.username,
                "user_pfp": user.profile_pic_uri,
                "online": ci.connected,
            })

        count = await table_size(ChatSession.id, ss)
        return display_page(content, count, page)


@router.get("/chat/list")
async def get_all_chat_customer(pg: Paging, ss: Session):
    async with ss.begin():
        chatlist = (
            await ss.execute(
                paging(
                    sqla.select(
                        UserAccount.id,
                        UserAccount.username,
                        UserAccount.profile_pic_uri,
                        ChatSession.connected,
                    ).join_from(
                        UserAccount,
                        ChatSession,
                        full=True,
                    ),
                    pg,
                )
            )
        ).all()

        count = await table_size(UserAccount.id, ss)
        return display_page(
            [
                {
                    "id": ci[0],
                    "username": ci[1],
                    "user_pfp": ci[2],
                    "has_chat": ci[3],
                }
                for ci in chatlist
            ],
            count,
            pg,
        )


@router.websocket("/chat/connect/{id}")
async def connect_customer_chat(
    ws: WebSocket,
    id: str,
    ss: Session,
    token: str = "",
):
    async with ss.begin():
        staff = (
            await ss.execute(
                sqla.select(StaffAccount).filter(StaffAccount.token == token)
            )
        ).scalar_one_or_none()

        customer = await ss.get(UserAccount, id)

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
            await chatlist[id].load_chat_history(ss)

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
        await chatlist[id].s_left_chat(ss)

        if chatlist[id].closable():
            del chatlist[id]


@router.websocket("/chat/customer")
async def customer_chat(
    ws: WebSocket,
    ss: Session,
    token: str = "",
):
    async with ss.begin():
        user = (
            await ss.execute(
                sqla.select(UserAccount).filter(UserAccount.token == token)
            )
        ).scalar_one_or_none()

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
            await chatlist[id].load_chat_history(ss)
        await chatlist[id].c_connect(ws, ss)

        while True:
            data = await ws.receive_text()
            await chatlist[id].c_send_msg({
                "sender": id,
                "timestamp": str(datetime.datetime.now()),
                "type": MsgType.MSG,
                "msg": data,
            })

    except WebSocketDisconnect as _:
        await chatlist[id].c_left_chat(ss)

        if chatlist[id].closable():
            del chatlist[id]
