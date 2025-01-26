"""Vercel AI SDK Data Stream Protocol

https://sdk.vercel.ai/docs/ai-sdk-ui/stream-protocol
"""

import json
from enum import Enum
from queue import Queue
from typing import Any, AsyncGenerator, Literal, Type

from langchain_core.messages import AIMessageChunk, ToolMessage
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel


class Text(BaseModel):
    string: str


class JsonArray(BaseModel):
    array: list[dict]


class ToolStart(BaseModel):
    toolCallId: str
    toolName: str


class ToolDelta(BaseModel):
    toolCallId: str
    argsTextDelta: str


class ToolCall(ToolStart):
    args: str


class ToolResult(BaseModel):
    toolCallId: str
    result: str


class FinishMessage(BaseModel):
    finishReason: Literal[
        "stop",
        "length",
        "content-filter",
        "tool-calls",
        "error",
        "other",
        "unknown",
    ]
    promptTokens: int
    completionTokens: int


class FinishStep(FinishMessage):
    isContinued: bool


class StreamProtocolMixin(Enum):
    value: str
    model: Type[BaseModel]

    def __new__(cls, template: str, model: Type[BaseModel]):
        obj = object.__new__(cls)
        obj._value_ = template
        obj.model = model

        return obj

    def render(self, **kwargs) -> str:
        assert self.model(**kwargs)
        formatted_kwargs = {
            k: json.dumps(v, separators=(",", ":")) for k, v in kwargs.items()
        }

        return self.value.format(**formatted_kwargs)


class DataStreamProtocol(StreamProtocolMixin):
    TextPart = ("0:{string}\n", Text)
    """The text parts are appended to the message as they are received."""

    DataPart = ("2:{array}\n", JsonArray)
    """The data parts are parsed as JSON and appended to the message as they are received."""

    MessageAnnotationPart = ("8:{array}\n", JsonArray)
    """The message annotation parts are appended to the message as they are received."""

    ErrorPart = ("3:{string}\n", Text)
    """The error parts are appended to the message as they are received."""

    ToolCallStreamingStartPart = (
        'b:{{"toolCallId":{toolCallId},"toolName":{toolName}}}\n',
        ToolStart,
    )
    """A part indicating the start of a streaming tool call."""

    ToolCallDeltaPart = (
        'c:{{"toolCallId":{toolCallId},"argsTextDelta":{argsTextDelta}}}\n',
        ToolDelta,
    )
    """A part representing a delta update for a streaming tool call."""

    ToolCallPart = (
        '9:{{"toolCallId":{toolCallId},"toolName":{toolName},"args":{args}}}\n',
        ToolCall,
    )
    """A part representing a tool call."""

    ToolResultPart = (
        'a:{{"toolCallId":{toolCallId},"result":{result}}}\n',
        ToolResult,
    )
    """A part representing a tool result."""

    StartStepPart = ('f:{{"id":{string}}}\n', Text)
    """A part indicating the start of a step."""

    FinishStepPart = (
        'e:{{"finishReason":{finishReason},"usage":{{"promptTokens":{promptTokens},"completionTokens":{completionTokens}}},"isContinued":{isContinued}}}\n',
        FinishStep,
    )
    """A part indicating that a step (i.e., one LLM API call in the backend) has been completed."""

    FinishMessagePart = (
        'd:{{"finishReason":{finishReason},"usage":{{"promptTokens":{promptTokens},"completionTokens":{completionTokens}}}}}\n',
        FinishMessage,
    )
    """A part indicating the completion of a message with additional metadata, such as `FinishReason` and `Usage`."""


async def consume_stream(
    graph: CompiledStateGraph,
    inputs: Any,
    stream_nodes: list[str] = [],
    **kwargs,
) -> AsyncGenerator[str, None]:
    # Tool queues.
    call_q: Queue = Queue()
    result_q: Queue = Queue()

    # Usage variables.
    # TODO: update to be able to track usage metadata.
    prompt_tokens: int = 0
    completion_tokens: int = 0

    dsp = DataStreamProtocol

    async for message, metadata in graph.astream(
        inputs, stream_mode="messages", **kwargs
    ):
        if metadata["langgraph_node"] not in stream_nodes:  # type: ignore[index]
            continue

        if isinstance(message, AIMessageChunk):
            if content := message.content:
                yield dsp.TextPart.render(string=content)

            if finish_reason := message.response_metadata.get("finish_reason"):
                if finish_reason == "tool_calls":
                    while not call_q.empty():
                        tool_call = call_q.get()
                        tool_call_id = tool_call["toolCallId"]
                        tool_name = tool_call["toolName"]
                        tool_args = tool_call["args"]
                        yield dsp.ToolCallPart.render(
                            toolCallId=tool_call_id,
                            toolName=tool_name,
                            args=tool_args,
                        )
                        result_q.put(tool_call)
                else:
                    yield dsp.FinishMessagePart.render(
                        finishReason=finish_reason,
                        promptTokens=prompt_tokens,
                        completionTokens=completion_tokens,
                    )

            if tool_calls_info := message.additional_kwargs.get("tool_calls"):
                func = tool_calls_info[0]["function"]
                func_name = func["name"]
                func_args = func["arguments"]
                if tool_id := tool_calls_info[0]["id"]:
                    call = {
                        "toolCallId": tool_id,
                        "toolName": func_name,
                        "args": func_args,
                    }
                    call_q.put(call)

                else:
                    call["args"] += func_args

        if isinstance(message, ToolMessage):
            while not result_q.empty():
                tool_result = result_q.get()
                yield dsp.ToolResultPart.render(**tool_result)
