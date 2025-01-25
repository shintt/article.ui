import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .chat import router as router_chat

origins = [
    os.getenv("ORIGIN_FRONT") or "http://localhost:3000",  # frontend
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router_chat)
