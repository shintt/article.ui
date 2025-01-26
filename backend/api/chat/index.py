from enum import Enum
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from graph import create_graph

from .protocol import consume_stream

router = APIRouter()
graph = create_graph()


class ToolInvocationState(str, Enum):
    CALL = "call"
    PARTIAL_CALL = "partial-call"
    RESULT = "result"


class ToolInvocation(BaseModel):
    state: ToolInvocationState
    toolCallId: str
    toolName: str
    args: Any
    result: Any


class ClientAttachment(BaseModel):
    name: str
    contentType: str
    url: str


class ClientMessage(BaseModel):
    role: str
    content: str
    experimental_attachments: list[ClientAttachment] | None = None
    toolInvocations: list[ToolInvocation] | None = None


class Request(BaseModel):
    messages: list[ClientMessage]


@router.post("/api/chat", response_class=StreamingResponse)
async def run_graph(request: Request):
    # Input params.
    message = request.messages[-1]
    inputs = {"topic": message.content}
    stream_nodes = ["write"]

    # Run graph.
    stream = consume_stream(graph, inputs, stream_nodes=stream_nodes)

    response = StreamingResponse(stream)
    response.headers["x-vercel-ai-data-stream"] = "v1"

    return response
