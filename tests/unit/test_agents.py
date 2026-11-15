from datapilot.agents import create_all_agents

def test_all_agents_are_registered():
    agents = create_all_agents()
    assert set(agents.keys()) == {"planner", "data_engineer", "analyst", "dashboard", "qa"}