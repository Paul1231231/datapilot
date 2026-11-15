from datapilot.schemas.qa import QAResult


def test_qa_approval():
    review = QAResult(
        passed=True,
        issues=[],
        correction_instructions="",
        summary="All checks passed.",
        severity="none"
    )

    assert review.passed is True
    assert review.issues == []


def test_qa_rejection():
    review = QAResult(
        passed=False,
        issues=["Incorrect percentage calculation"],
        correction_instructions="Recalculate the percentage.",
        summary="Numerical inconsistency detected.",
        severity="high"
    )

    assert review.passed is False
    assert len(review.issues) == 1