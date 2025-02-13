from typing import Annotated
import uuid
import uvicorn
from fastapi import Cookie, FastAPI, Request
from fastapi.responses import JSONResponse
from auth import api as auth_api
from routers import (
    prototype,
    staff,
    manager,
    general,
    dev,
    websocket,
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
app.include_router(websocket.router)
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
