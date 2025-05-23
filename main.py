import asyncio
from typing import Annotated, Any
import uuid
from sqlalchemy.exc import (
    NoResultFound,
    StatementError,
)
import uvicorn
import traceback
from fastapi import Cookie, FastAPI, Request
from fastapi.responses import JSONResponse
from auth import api as auth_api
from etc.local_error import HandledError
from routers import (
    shipper,
    staff,
    manager,
    general,
    dev,
    websocket_,
    ai_ws,
    public,
)
from contextlib import asynccontextmanager
import logging
import ai
from fastapi.middleware.cors import CORSMiddleware
import db.postgresql as db

asyncio.run(db.init_db())

preload: dict[Any, Any] = dict()


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield {"ai_models": ai.load_all_model(), "test": "lesus"}


app = FastAPI(lifespan=lifespan)

logger = logging.getLogger("uvicorn.error")

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8000",
    "ws://localhost:8000",
    "ws://localhost:3000",
    "ws://localhost:3001",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_headers=["*"],
    allow_credentials=True,
    allow_methods=["*"],
)

app.include_router(dev.router)
app.include_router(general.router)
app.include_router(manager.router)
app.include_router(staff.router)
app.include_router(auth_api.router)
app.include_router(websocket_.router)
app.include_router(public.router)
app.include_router(ai_ws.router)
app.include_router(shipper.router)


@app.exception_handler(Exception)
async def validation_exception_handler(
    req: Request,
    exc: Exception,
):
    # Change here to Logger
    stacktrace = traceback.format_exc()
    logger.error(exc)
    logger.error(stacktrace)
    return JSONResponse(
        status_code=500,
        content={
            "api": str(req.url),
            "method": req.method,
            "message": (f"{exc!r}"),
            "stack_trace": stacktrace.splitlines(),
        },
    )


@app.exception_handler(HandledError)
@app.exception_handler(NoResultFound)
async def local_error_handler(req: Request, exc: HandledError | NoResultFound):
    return JSONResponse(
        status_code=500,
        content={
            "api": str(req.url),
            "message": (f"{exc}"),
        },
    )


@app.exception_handler(StatementError)
async def sql_error_handler(req: Request, exc: StatementError):
    msg = exc.orig.__str__().splitlines()
    return JSONResponse(
        status_code=500,
        content={
            "api": str(req.url),
            "message": msg[-1],
            "message_detail": msg,
        },
    )


@app.get("/")
async def read_root(cookie: Annotated[str, Cookie()] = None):
    response = JSONResponse(
        content={
            "sussy": "wussy",
            "cookie": cookie,
        }
    )
    if not cookie:
        response.set_cookie(
            key="guest_session",
            value=str(uuid.uuid4()),
        )
    return response


if __name__ == "__main__":
    uvicorn.run(app)
