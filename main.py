import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from auth import api as auth_api
from routers import account_api, staff, manager

app = FastAPI()

app.include_router(staff.router)
app.include_router(manager.router)
app.include_router(account_api.router)
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


if __name__ == "__main__":
    uvicorn.run(app)
