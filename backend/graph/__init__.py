from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import RetryPolicy

from .nodes import run_planner, run_reporter, web_search, web_search_invoker
from .types import GraphIn, GraphOverallState

__all__ = ["create_graph"]


def create_graph() -> CompiledStateGraph:
    builder = StateGraph(
        state_schema=GraphOverallState,
        input=GraphIn,
    )

    builder.add_node("planner", run_planner, retry=RetryPolicy())
    builder.add_node("reporter", run_reporter, retry=RetryPolicy())
    builder.add_node("web_search", web_search)

    builder.add_edge(START, "planner")
    builder.add_conditional_edges("planner", web_search_invoker, ["web_search"])
    builder.add_edge("web_search", "reporter")
    builder.add_edge("reporter", END)

    return builder.compile()
