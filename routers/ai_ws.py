from typing import Annotated
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from ollama import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgresql.db_session import get_session
from db.postgresql.models.user_account import UserAccount

import sqlalchemy as sqla
from config import env


router = APIRouter(prefix="/ws", tags=["WebSocket"])

chef_client = AsyncClient(host=env.LLM_ENDPOINT)

Session = Annotated[AsyncSession, Depends(get_session)]
# cur_usr_amnt = 0

# user_queue: Queue[WebSocket] = Queue()


@router.websocket("/chef")
async def customer_chat(
    ws: WebSocket,
    token: str,
    ss: Session,
):
    async with ss.begin():
        user = (
            await ss.execute(
                sqla.select(UserAccount).filter(UserAccount.token == token)
            )
        ).scalar_one_or_none()

    try:
        await ws.accept()
        if not user:
            await ws.send_json({
                "sender": "system",
                "msg": "User token is invalid",
            })
            await ws.close()
            return

        while True:
            # queue_index = user_queue.qsize()

            # if cur_usr_amnt >= env.LLM_USER_LIMIT:
            #     await ws.send_json({
            #         "sender": "system",
            #         "msg": "AI Chef is current full",
            #     })
            #     while True:
            #         time.sleep(2)
            #         pass

            data = await ws.receive_text()
            message = {
                "role": "user",
                "content": data,
            }

            await ws.send_text("<chat>")

            async for part in await chef_client.chat(
                model="gemma3_1b_chef",
                messages=[message],
                stream=True,
            ):
                await ws.send_text(part["message"]["content"])

            await ws.send_text("</chat>")

    except WebSocketDisconnect as _:
        pass
