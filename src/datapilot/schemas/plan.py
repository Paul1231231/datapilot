from typing import Literal

from pydantic import BaseModel, Field


class AnalysisTask(BaseModel):
    task_id: str = Field(
        description="Unique identifier for this task"
    )

    description: str = Field(
        min_length=5,
        description="What needs to be investigated"
    )

    assigned_agent: Literal[
        "data_engineer",
        "analyst",
        "dashboard",
    ]

    dependencies: list[str] = Field(
        default_factory=list,
        description="Task IDs that must finish first"
    )


class AnalysisPlan(BaseModel):
    objective: str = Field(
        min_length=5,
        description="Overall analytical objective"
    )

    tasks: list[AnalysisTask] = Field(
        min_length=1,
        description="Tasks required to complete the analysis"
    )

    reasoning: str = Field(
        description="Brief explanation of the proposed plan"
    )