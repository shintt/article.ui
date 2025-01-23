from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from graph import create_graph

router = APIRouter()
graph = create_graph()


@router.post("/api/chat", response_class=StreamingResponse)
async def run_graph(): ...
