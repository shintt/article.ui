import operator
from typing import Annotated

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field, HttpUrl


class SearchSubject(BaseModel):
    """Web Search Subjects"""

    subjects: list[str]


class GraphIn(BaseModel):
    """Article Topic"""

    topic: str = Field(max_length=50)


class ParentState(GraphIn):
    subject: SearchSubject | None = Field(default=None)
    search_results: Annotated[list, operator.add]


class SubgraphState(ParentState):
    messages: Annotated[list, add_messages]
    continue_to_write: bool = Field(default=False)


class DuckDuckGoResult(BaseModel):
    snippet: str
    title: str
    link: HttpUrl


class EndVerdict(BaseModel):
    """Whether continue writing the report."""

    continue_to_write: bool
