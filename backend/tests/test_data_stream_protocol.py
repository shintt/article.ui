import pytest

from api.chat.protocol import DataStreamProtocol as dsp


@pytest.mark.parametrize(
    "name, arg, expect",
    [
        (
            "TextPart",
            {"string": "example"},
            '0:"example"\n',
        ),
        (
            "DataPart",
            {"array": [{"key": "object1"}, {"anotherKey": "object2"}]},
            '2:[{"key":"object1"},{"anotherKey":"object2"}]\n',
        ),
        (
            "MessageAnnotationPart",
            {"array": [{"id": "message-123", "other": "annotation"}]},
            '8:[{"id":"message-123","other":"annotation"}]\n',
        ),
        (
            "ErrorPart",
            {"string": "error message"},
            '3:"error message"\n',
        ),
        (
            "ToolCallStreamingStartPart",
            {"toolCallId": "call-456", "toolName": "streaming-tool"},
            'b:{"toolCallId":"call-456","toolName":"streaming-tool"}\n',
        ),
        (
            "ToolCallDeltaPart",
            {"toolCallId": "call-456", "argsTextDelta": "partial arg"},
            'c:{"toolCallId":"call-456","argsTextDelta":"partial arg"}\n',
        ),
        (
            "ToolCallPart",
            {
                "toolCallId": "call-123",
                "toolName": "my-tool",
                "args": {"some": "argument"},
            },
            '9:{"toolCallId":"call-123","toolName":"my-tool","args":{"some":"argument"}}\n',
        ),
        (
            "ToolResultPart",
            {"toolCallId": "call-123", "result": "tool output"},
            'a:{"toolCallId":"call-123","result":"tool output"}\n',
        ),
        (
            "StartStepPart",
            {"string": "step_123"},
            'f:{"id":"step_123"}\n',
        ),
        (
            "FinishStepPart",
            {
                "finishReason": "stop",
                "promptTokens": 10,
                "completionTokens": 20,
                "isContinued": False,
            },
            'e:{"finishReason":"stop","usage":{"promptTokens":10,"completionTokens":20},"isContinued":false}\n',
        ),
        (
            "FinishMessagePart",
            {"finishReason": "stop", "promptTokens": 10, "completionTokens": 20},
            'd:{"finishReason":"stop","usage":{"promptTokens":10,"completionTokens":20}}\n',
        ),
    ],
)
def test_render_protocol(name, arg, expect):
    protocol = getattr(dsp, name)  # type: dsp

    assert protocol.render(**arg) == expect
