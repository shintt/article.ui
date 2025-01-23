from typing import Self

from langchain_core.tools import tool
from pydantic import (
    BaseModel,
    ValidationError,
    field_validator,
    model_validator,
)


@tool
async def render_bar_chart_component(
    chartData: list[dict[str, int | str]],
    dataKeys: list[str],
    XAxis: str,
):
    """A function that issues command to render Bar Chart React Component.
    Once this function executes currectly, a bar chart will be displayed in the web browser.

    Parameters
    ----------
    chartData: list[dict]
        Data to be displayed as the bar chart. Each element in the list represents a tick in the bar chart.

    dataKeys: list[str]
        The field names of the data used as ticks in the bar chart.
        These names and their values must also be present in the `chartData`.

    XAxis: str
        The name of the label for the x-axis of the bar chart.
        This name and its values must also be present in the `chartData`.

    Returns
    -------
    str
        A Message indicating that the command to render the bar chart was successfully issued.

    Examples
    --------
    chartData = [
        {"category": "A", "values": 10},
        {"category": "B", "values": 15},
    ]
    dataKeys = ["values"]
    XAxis = "category"
    """

    class Schema(BaseModel):
        chartData: list[dict[str, int | str]]
        dataKeys: list[str]
        XAxis: str

        @property
        def keys(self) -> list[str]:
            """Keys of first element of chartData."""

            return list(self.chartData[0].keys())

        @field_validator("chartData", mode="after")
        @classmethod
        def validate_key_consistency(cls, v: list[dict]):
            keys = list(v[0].keys())
            for x in v:
                x_keys = list(x.keys())
                if x_keys != keys:
                    raise ValueError(
                        "The dict keys of each list element must be same."
                        f" Key {x_keys} and Key {keys} are not equal."
                    )

            return v

        @model_validator(mode="after")
        def validate_data_keys_are_subset_of_chart_data(self) -> Self:
            for d_key in self.dataKeys:
                if d_key not in self.keys:
                    raise ValueError(f"Key of data_keys {d_key} not in chartData.")

            return self

        @model_validator(mode="after")
        def validate_x_axis_key_is_subset_of_chart_data(self) -> Self:
            if self.XAxis not in self.keys:
                raise ValueError(f"Key of x_axis_key {self.XAxis} not in chartData.")

            return self

    try:
        Schema.model_validate(
            {"chartData": chartData, "dataKeys": dataKeys, "XAxis": XAxis}
        )
        return "The bar chart has beed rendered on the user's screen."

    except ValidationError as e:
        return e
