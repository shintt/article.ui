import pytest
from pydantic import ValidationError

from graph import create_graph
from graph.types import GraphIn


@pytest.fixture
def expected_nodes() -> set[str]:
    return {"planner", "web_search", "reporter"}


# @pytest.mark.skip(reason="run if you make changes to the graph structure.")
@pytest.mark.asyncio
async def test_pass_all_expected_nodes(expected_nodes):
    graph = create_graph()
    passed_nodes = set()

    async for event in graph.astream_events(
        {"topic": "How to use LangChain?"}, version="v2"
    ):
        if node_name := event["metadata"].get("langgraph_node"):
            passed_nodes.add(node_name)

    assert expected_nodes <= passed_nodes


@pytest.mark.xfail(raises=ValidationError, strict=True)
def test_input_long_text():
    assert GraphIn(topic="-" * 10000)
