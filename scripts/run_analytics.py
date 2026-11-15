import argparse

from datapilot.flows.analytics_flow import AnalyticsFlow


def main():
    parser = argparse.ArgumentParser(
        description="Run DataPilot analytics."
    )

    parser.add_argument(
        "--question",
        type=str,
        required=True,
        help="Business question to analyze",
    )

    args = parser.parse_args()

    flow = AnalyticsFlow()
    flow.state.user_question = args.question

    result = flow.kickoff()

    print("\n===== DATAPILOT RESULT =====")
    print(result)


if __name__ == "__main__":
    main()