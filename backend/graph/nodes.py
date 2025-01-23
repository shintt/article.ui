import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from duckduckgo_search.exceptions import RatelimitException
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_openai import ChatOpenAI
from langchain_prompty import create_chat_prompt  # type: ignore[import-untyped]
from langgraph.types import Send

from .types import GraphOverallState, SearchSubject

if TYPE_CHECKING:
    # ruff: noqa: F401
    from .types import DuckDuckGoResult, SearchSubject


PROMPT_ROOT = Path(os.getcwd()) / "prompts"
MODEL_NAME = "gpt-4o-mini"


logger = logging.getLogger(__name__)


def _create_planner(
    prompt_path: str = "planner.prompty",
    model_name: str = MODEL_NAME,
):
    """A chain that breaks down a search topic provided by the user into more detailed subjects."""

    prompt = create_chat_prompt(PROMPT_ROOT / prompt_path)
    llm = ChatOpenAI(model=model_name)

    return prompt | llm.with_structured_output(SearchSubject)


def _create_reporter(
    prompt_path: str = "reporter.prompty",
    model_name: str = MODEL_NAME,
):
    """Reporter"""

    prompt = create_chat_prompt(PROMPT_ROOT / prompt_path)
    llm = ChatOpenAI(model=model_name)

    # TODO: change to be able to use tools.

    return prompt | llm


planner = _create_planner()
reporter = _create_reporter()


async def run_planner(state: GraphOverallState):
    inputs = {"topic": state.topic}
    response = await planner.ainvoke(inputs)  # type: SearchSubject

    return {"subject": response}


async def run_reporter(state: GraphOverallState):
    topic = state.topic
    search_results = state.search_results
    _ = await reporter.ainvoke({"topic": topic, "search_results": search_results})

    # TODO: update


async def web_search(search: str):
    """Search web about input arg."""

    try:
        tool = DuckDuckGoSearchResults(output_format="list", num_results=3)
        response = await tool.ainvoke(search)  # type: DuckDuckGoResult
        return {"search_results": [response]}

    except RatelimitException as e:
        logger.error(str(e))


async def web_search_invoker(state: GraphOverallState):
    """Map each subject to `web_search` node."""

    if not state.subject:
        raise ValueError

    return [Send("web_search", s) for s in state.subject.subjects]
