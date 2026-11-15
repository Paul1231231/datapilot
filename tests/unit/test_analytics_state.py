from datapilot.flows.state import AnalyticsState


def test_analytics_state_defaults():
    state = AnalyticsState()

    assert state.user_question == ""
    assert state.status == "pending"
    assert state.retry_count == 0
    assert state.plan is None


def test_each_state_has_independent_run_id():
    first = AnalyticsState()
    second = AnalyticsState()

    assert first.run_id != second.run_id


def test_each_state_has_independent_chart_specs():
    first = AnalyticsState()
    second = AnalyticsState()

    first.chart_specs.append({"type": "bar"})

    assert second.chart_specs == []