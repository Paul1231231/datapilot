from datapilot.llm.client import LLMClient
from datapilot.schemas.plan import AnalysisPlan


def main():
    client = LLMClient()

    prompt = """
    A company experienced a decrease in revenue during Q3.

    Create an analytical plan to investigate the issue.

    Include:
    1. Calculating revenue by quarter.
    2. Identifying the worst-performing region.
    3. Investigating changes in product sales.

    Assign tasks to the appropriate agents.
    """

    result = client.generate_structured(
        prompt=prompt,
        response_model=AnalysisPlan,
    )

    print("\nGenerated Analysis Plan")
    print(result.model_dump_json(indent=2))

    print("\nTask assignments:")

    for task in result.tasks:
        print(
            f"{task.task_id}: "
            f"{task.description} "
            f"-> {task.assigned_agent}"
        )


if __name__ == "__main__":
    main()