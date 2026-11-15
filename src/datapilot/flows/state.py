from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from datapilot.schemas.plan import AnalysisPlan

from datapilot.schemas.qa import QAResult

class AnalyticsState(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))

    user_question: str = ""

    plan: AnalysisPlan | None = None
    query_results: str = ""
    analysis: str = ""

    chart_specs: list[dict[str, Any]] = Field(default_factory=list)

    status: str = "pending"
    current_stage: str = "initialization"
    error: str | None = None
    metrics: dict[str, Any] = {}
    qa_result: QAResult | None = None
    retry_count: int = 0
    task_results: list[dict[str, Any]] = Field(
        
    )