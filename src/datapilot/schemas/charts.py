from typing import Literal

from pydantic import BaseModel, Field


class ChartSpec(BaseModel):
    chart_id: str
    title: str

    chart_type: Literal["bar", "line", "pie"]

    x: list[str]
    y: list[float]

    x_label: str
    y_label: str


class DashboardOutput(BaseModel):
    title: str
    description: str
    charts: list[ChartSpec] = Field(default_factory=list)