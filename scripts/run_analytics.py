from datapilot.database.metadata import (
    initialize_metadata_tables,
    save_analysis_run,
    save_agent_event,
)

from datapilot.flows.analytics_flow import AnalyticsFlow


def main():
    initialize_metadata_tables()

    question = "Why did Q3 revenue decrease compared with Q2?"

    flow = AnalyticsFlow()

    # Create the state and persist the initial run.
    flow.state.user_question = question
    save_analysis_run(flow.state)

    save_agent_event(
        run_id=flow.state.run_id,
        stage="initialization",
        event_type="run_started",
        message="Analytics workflow started.",
    )

    try:
        result = flow.kickoff()

        print("\n========== DATAPILOT RESULT ==========")
        print(result)

    except Exception as exc:
        flow.state.status = "failed"
        flow.state.current_stage = "failed"
        flow.state.error = str(exc)

        save_analysis_run(flow.state)

        save_agent_event(
            run_id=flow.state.run_id,
            stage="workflow",
            event_type="run_failed",
            message=str(exc),
        )

        raise

    print("\n========== FINAL WORKFLOW STATE ==========")
    print(flow.state.model_dump_json(indent=2))


if __name__ == "__main__":
    main()