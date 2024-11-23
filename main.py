import db
from fastapi import FastAPI
from pydantic import BaseModel

from apis import account_api
from apis.authenticate import authen_api

app = FastAPI()

app.include_router(account_api.router)
app.include_router(authen_api.router)


@app.get("/")
async def read_root():
    return {"Hello": "World"}
