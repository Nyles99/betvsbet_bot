from contextlib import asynccontextmanager

from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import init_db 
import requests as rq


@asynccontextmanager
async def lifespan(app_: FastAPI):
    await init_db()
    print('Bot is ready')
    yield


app = FastAPI(title="To Do App", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/tours/{tg_id}")
async def tours(tg_id: int):
    user = await rq.add_user(tg_id)