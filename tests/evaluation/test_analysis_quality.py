def evaluate_analysis(
    report: dict,
    expected_metrics: dict,
) -> list[str]:
    issues = []

    reported_revenue = report.get("total_revenue")
    expected_revenue = expected_metrics["total_revenue"]

    if reported_revenue is None:
        issues.append("Missing total revenue.")
    elif abs(reported_revenue - expected_revenue) > 0.01:
        issues.append("Incorrect total revenue.")

    reported_category = report.get("top_category")
    expected_category = expected_metrics["top_category"]

    if reported_category != expected_category:
        issues.append("Incorrect top revenue category.")

    return issues



def test_correct_analysis():
    report = {
        "total_revenue": 5000.0,
        "top_category": "Electronics",
    }

    expected = {
        "total_revenue": 5000.0,
        "top_category": "Electronics",
    }

    issues = evaluate_analysis(report, expected)

    assert issues == []


def test_incorrect_analysis():
    report = {
        "total_revenue": 4500.0,
        "top_category": "Furniture",
    }

    expected = {
        "total_revenue": 5000.0,
        "top_category": "Electronics",
    }

    issues = evaluate_analysis(report, expected)

    assert len(issues) == 2