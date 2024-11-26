import db
import uvicorn

from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse

from auth import api as auth_api

from apis import account_api, manager_api, staff_api

app = FastAPI()

app.include_router(account_api.router)
app.include_router(manager_api.router)
app.include_router(staff_api.router)
app.include_router(auth_api.router)


@app.exception_handler(Exception)
async def validation_exception_handler(request: Request, exc: Exception):
    # Change here to Logger
    return JSONResponse(
        status_code=500,
        content={
            "message": (
                f"Failed method {request.method} at URL {request.url}."
                f" Exception message is {exc!r}."
            )
        },
    )


@app.get("/")
async def read_root():
    return {"Hello": "World"}

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8686)
