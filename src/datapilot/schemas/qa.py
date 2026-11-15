from typing import Literal

from pydantic import BaseModel, Field


class QAResult(BaseModel):
    passed: bool

    issues: list[str] = Field(
        default_factory=list
    )

    severity: Literal[
        "none",
        "low",
        "medium",
        "high",
    ]

    correction_instructions: str = ""