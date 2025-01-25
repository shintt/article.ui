import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from duckduckgo_search.exceptions import DuckDuckGoSearchException
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_openai import ChatOpenAI
from langchain_prompty import create_chat_prompt  # type: ignore[import-untyped]
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Send

from .tools import render_bar_chart_component
from .types import EndVerdict, ParentState, SearchSubject, SubgraphState

if TYPE_CHECKING:
    # ruff: noqa: F401
    from langchain_core.messages import AIMessage

    from .types import DuckDuckGoResult, SearchSubject


PROMPT_ROOT = Path(os.getcwd()) / "prompts"
MODEL_NAME = "gpt-4o-mini"


logger = logging.getLogger(__name__)


def _create_planner():
    """A chain that breaks down a search topic provided by the user into more detailed subjects."""

    prompt = create_chat_prompt(PROMPT_ROOT / "planner.prompty")
    llm = ChatOpenAI(model=MODEL_NAME)

    return prompt | llm.with_structured_output(SearchSubject)


def _create_reporter():
    """Create reporter subgraph."""

    llm = ChatOpenAI(model=MODEL_NAME)

    write_prompt = create_chat_prompt(PROMPT_ROOT / "reporter_write.prompty")
    tools = [render_bar_chart_component]
    write_chain = write_prompt | llm.bind_tools(tools)

    verdict_prompt = create_chat_prompt(PROMPT_ROOT / "reporter_end_verdict.prompty")
    verdict_chain = verdict_prompt | llm.with_structured_output(EndVerdict)

    # nodes
    async def write(state: SubgraphState):
        inputs = {
            "topic": state.topic,
            "subject": state.subject,
            "search_results": state.search_results,
            "agent_scratchpad": state.messages,
        }
        response = await write_chain.ainvoke(inputs)

        return {"messages": response}

    async def route_tools(state: SubgraphState) -> Literal["tools", "end_verdict"]:
        """
        Use in the conditional_edge to route to the ToolNode if the last message
        has tool calls. Otherwise, route to the phase of deciding whether to
        continue writing.
        """
        ai_message = state.messages[-1]  # type: AIMessage

        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return "tools"

        return "end_verdict"

    async def end_verdict(state: SubgraphState):
        inputs = {
            "topic": state.topic,
            "subject": state.subject,
            "agent_scratchpad": state.messages,
        }
        response = await verdict_chain.ainvoke(inputs)  # type: EndVerdict

        return {"continue_to_write": response.continue_to_write}

    async def should_continue(state: SubgraphState) -> Literal["write", "end"]:
        if state.continue_to_write:
            return "write"
        else:
            return "end"

    builder = StateGraph(SubgraphState)
    builder.add_node("write", write)
    builder.add_node("end_verdict", end_verdict)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "write")
    builder.add_conditional_edges(
        "write",
        route_tools,
        {"tools": "tools", "end_verdict": "end_verdict"},
    )
    builder.add_edge("tools", "write")
    builder.add_conditional_edges(
        "end_verdict",
        should_continue,
        {"write": "write", "end": END},
    )

    return builder.compile()


planner = _create_planner()
reporter = _create_reporter()


async def run_planner(state: ParentState):
    inputs = {"topic": state.topic}
    response = await planner.ainvoke(inputs)  # type: SearchSubject

    return {"subject": response}


async def web_search(search: str):
    """Search web about input arg."""

    try:
        tool = DuckDuckGoSearchResults(output_format="list", num_results=3)
        response = await tool.ainvoke(search)  # type: DuckDuckGoResult
        return {"search_results": [response]}

    except DuckDuckGoSearchException as e:
        logger.error(str(e))


async def web_search_invoker(state: ParentState):
    """Map each subject to `web_search` node."""

    if not state.subject:
        raise ValueError

    return [Send("web_search", s) for s in state.subject.subjects]
