from datapilot.agents.planner import create_planner_agent
from datapilot.agents.data_engineer import create_data_engineer_agent
from datapilot.agents.analyst import create_analyst_agent
from datapilot.agents.dashboard import create_dashboard_agent
from datapilot.agents.qa import create_qa_agent


def create_all_agents():
    return {
        "planner": create_planner_agent(),
        "data_engineer": create_data_engineer_agent(),
        "analyst": create_analyst_agent(),
        "dashboard": create_dashboard_agent(),
        "qa": create_qa_agent(),
    }