"""Vercel AI SDK Data Stream Protocol

https://sdk.vercel.ai/docs/ai-sdk-ui/stream-protocol
"""

import json
from enum import Enum
from typing import Any, Literal, Type

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
    args: dict


class ToolResult(BaseModel):
    toolCallId: str
    result: Any


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


class BaseStreamProtocol(Enum):
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


class DataStreamProtocol(BaseStreamProtocol):
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
