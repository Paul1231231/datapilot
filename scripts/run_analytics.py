from datapilot.flows.analytics_flow import AnalyticsFlow


def main():
    question = (
        "Why did Q3 revenue decrease compared with Q2?"
    )

    flow = AnalyticsFlow()

    result = flow.kickoff(
        inputs={
            "user_question": question,
        }
    )

    print("\n========== DATAPILOT RESULT ==========")
    print(result)

    print("\n========== WORKFLOW STATE ==========")
    print(flow.state.model_dump_json(indent=2))


if __name__ == "__main__":
    main()