from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn
from main import app

import ai


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield {"ai_models": ai.load_all_stub_model(), "test": "lesus"}


app.router.lifespan_context = lifespan

if __name__ == "__main__":
    uvicorn.run(app)