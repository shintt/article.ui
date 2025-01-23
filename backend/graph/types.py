import operator
from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl


class SearchSubject(BaseModel):
    """Web Search Subjects"""

    subjects: list[str]


class GraphIn(BaseModel):
    """Article Topic"""

    topic: str = Field(max_length=50)


class GraphOverallState(GraphIn):
    subject: SearchSubject | None = None
    search_results: Annotated[list, operator.add]


class DuckDuckGoResult(BaseModel):
    snippet: str
    title: str
    link: HttpUrl
