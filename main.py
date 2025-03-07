from typing import Annotated
import uuid
import sqlalchemy
import sqlalchemy.exc
import uvicorn
from fastapi import Cookie, FastAPI, Request
from fastapi.responses import JSONResponse
from auth import api as auth_api
from db.postgresql.db_session import db_session
from routers import (
    prototype,
    staff,
    manager,
    general,
    dev,
    websocket_,
    public,
)
from contextlib import asynccontextmanager
import ai

from fastapi.middleware.cors import CORSMiddleware

preload = dict()


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield {"ai_models": ai.load_all_model(), "test": "lesus"}


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "ws://localhost:8000",
    "ws://localhost:3000",
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
app.include_router(prototype.router)
app.include_router(websocket_.router)
app.include_router(public.router)


@app.exception_handler(Exception)
async def validation_exception_handler(request: Request, exc: Exception):
    # Change here to Logger
    return JSONResponse(
        status_code=500,
        content={
            "api": str(request.url),
            "method": request.method,
            "message": (f"{exc!r}"),
        },
    )


@app.exception_handler(sqlalchemy.exc.SQLAlchemyError)
async def db_exception_handler(
    req: Request,
    exc: sqlalchemy.exc.SQLAlchemyError,
):
    db_session.session.rollback()
    return JSONResponse(
        status_code=500,
        content={
            "message": (f"{exc!r}"),
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
