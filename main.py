from typing import Annotated, Any
import uuid
import sqlalchemy
import sqlalchemy.exc
import uvicorn
import traceback
from fastapi import Cookie, FastAPI, Request
from fastapi.responses import JSONResponse
from auth import api as auth_api
from db.postgresql.db_session import db_session
from etc.local_error import HandledError
from routers import (
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
async def local_error_handler(_: Request, exc: HandledError):
    return JSONResponse(
        status_code=500,
        content={
            "message": (f"{exc}"),
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
