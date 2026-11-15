import pytest
from pydantic import ValidationError

from datapilot.schemas.plan import (
    AnalysisPlan,
    AnalysisTask,
)


def test_valid_analysis_task():
    task = AnalysisTask(
        task_id="task_1",
        description="Calculate quarterly revenue",
        assigned_agent="data_engineer",
        dependencies=[],
    )

    assert task.assigned_agent == "data_engineer"


def test_invalid_agent_assignment():
    with pytest.raises(ValidationError):
        AnalysisTask(
            task_id="task_1",
            description="Calculate quarterly revenue",
            assigned_agent="marketing_agent",
        )


def test_valid_analysis_plan():
    plan = AnalysisPlan(
        objective="Investigate quarterly revenue decline",
        tasks=[
            AnalysisTask(
                task_id="task_1",
                description="Calculate quarterly revenue",
                assigned_agent="data_engineer",
            )
        ],
        reasoning="Revenue must be calculated before investigating trends.",
    )

    assert len(plan.tasks) == 1
    assert plan.tasks[0].task_id == "task_1"


def test_empty_task_list_is_rejected():
    with pytest.raises(ValidationError):
        AnalysisPlan(
            objective="Investigate quarterly revenue decline",
            tasks=[],
            reasoning="No tasks were generated.",
        )