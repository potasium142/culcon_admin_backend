import db
from fastapi import FastAPI
from pydantic import BaseModel

from auth import api as auth_api

from apis import account_api, manager_api

app = FastAPI()

app.include_router(account_api.router)
app.include_router(manager_api.router)
app.include_router(auth_api.router)


@app.get("/")
async def read_root():
    return {"Hello": "World"}
