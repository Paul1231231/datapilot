from pydantic import BaseModel, Field


class KPIResult(BaseModel):
    metric_name: str

    current_value: float

    previous_value: float | None = None

    percentage_change: float | None = None

    interpretation: str = Field(
        min_length=5,
        description="Explain what this metric means"
    )


class AnalyticalReport(BaseModel):
    summary: str

    findings: list[str]

    recommendations: list[str]

    supporting_metrics: list[KPIResult]