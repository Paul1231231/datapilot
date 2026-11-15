
# DataPilot — AI-Powered Multi-Agent Analytics Platform

DataPilot is a local-first AI analytics platform that transforms
natural-language business questions into data-driven insights.

Built with CrewAI, Python, PostgreSQL, Pandas, Plotly and Streamlit,
the platform uses specialized AI agents to plan analytical tasks,
retrieve business data, identify trends, generate visualizations,
and validate analytical results.

## Key Features

- Multi-agent analytics workflow using CrewAI
- Specialized Planner, Data Engineer, Analyst, Dashboard and QA agents
- Natural-language business question processing
- Structured agent communication using Pydantic
- PostgreSQL-backed sales analytics
- Read-only SQL execution and query validation
- Pandas-based metric calculations
- Interactive Plotly visualizations
- QA review with bounded correction attempts
- Analysis run and agent event persistence
- Streamlit dashboard
- Local LLM inference using Ollama

## Architecture

DataPilot uses a controlled multi-agent architecture.

The CrewAI Flow coordinates the execution of specialized agents.
Pydantic models define structured inputs and outputs, while shared
workflow state stores intermediate results.

The agents are not allowed to execute arbitrary database operations.
Database queries pass through a validation and read-only execution
layer.

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python |
| Package management | uv |
| Agent framework | CrewAI |
| Local LLM | Ollama |
| LLM model | Qwen3 |
| Data validation | Pydantic |
| Database | PostgreSQL |
| Database access | SQLAlchemy |
| SQL parsing | SQLGlot |
| Data processing | Pandas |
| Visualization | Plotly |
| Frontend | Streamlit |
| Testing | Pytest |
| Infrastructure | Docker Compose |

## Agent Responsibilities

| Agent | Responsibility |
|---|---|
| Planner | Decomposes business questions into analytical tasks |
| Data Engineer | Inspects data and retrieves relevant information |
| Analyst | Calculates KPIs and interprets trends |
| Dashboard | Produces chart specifications and visualizations |
| QA | Reviews analytical results and requests corrections |

## Workflow

1. User submits a business question.
2. Planner creates an analytical plan.
3. Data Engineer retrieves relevant data.
4. Analyst calculates metrics and interprets results.
5. Dashboard agent prepares visualizations.
6. QA agent checks the results.
7. Failed reviews trigger bounded correction attempts.
8. The final result and workflow events are persisted.

## Project Structure

```text
src/datapilot/
├── agents/
├── analytics/
├── config/
├── database/
├── flows/
├── schemas/
├── tools/
└── ui/
```

## Getting Started

### Prerequisites

- Python 3.12+
- uv
- Docker Desktop
- Ollama

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/datapilot.git
cd datapilot
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Configure your database URL and Ollama settings in `.env`.

Example:

```env
DATABASE_URL=postgresql+psycopg://datapilot:datapilot_dev@localhost:5432/datapilot
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b
```

Use the actual model and configuration supported by your installation.

### 4. Start PostgreSQL

```bash
docker compose up -d
```

### 5. Start Ollama

Make sure Ollama is running, then pull the configured model if needed:

```bash
ollama pull qwen3:8b
```

### 6. Initialize the database

Run the schema initialization and synthetic data generation
scripts provided in the `scripts/` directory.

For example:

```bash
uv run python scripts/generate_data.py
uv run python scripts/seed_database.py
uv run python scripts/init_metadata.py
```

Run the schema SQL before seeding if your setup does not initialize
it automatically.

### 7. Launch the dashboard

```bash
uv run streamlit run src/datapilot/ui/app.py
```

Open:

http://localhost:8501

## Testing

Run unit tests:

```bash
uv run pytest tests/unit -v
```

Run integration tests:

```bash
uv run pytest tests/integration -v
```

Run the full test suite:

```bash
uv run pytest -v
```

Generate a coverage report:

```bash
uv run pytest --cov=datapilot --cov-report=term-missing
```

## Database

The sales database contains:

- regions
- customers
- products
- orders
- order_items

The workflow metadata database contains:

- analysis_runs
- agent_events

Revenue is calculated as:

```sql
SUM(quantity * unit_price)
```

## Design Decisions

### Why CrewAI Flow?

CrewAI Flow provides explicit workflow orchestration and shared
state, making execution more predictable than relying on
uncontrolled agent delegation.

### Why Pydantic?

Pydantic enforces structured data contracts between agents and
helps validate their outputs.

### Why Ollama?

Local inference reduces dependence on paid hosted model APIs and
allows the project to run locally.

### Why SQL validation?

LLM-generated SQL is untrusted. Query validation and read-only
database permissions provide safeguards against destructive
database operations.

### Why a separate QA agent?

AI-generated analysis may contain unsupported conclusions or
incorrect interpretations. A QA stage provides an additional
review before the result is returned.

## Limitations

- Uses synthetic sales data rather than a production business database.
- Local LLM performance depends on available hardware and model quality.
- AI-generated analytical explanations still require verification.
- SQL validation is not a complete security boundary.
- The current analytics use cases are limited to the available schema.
- The application has not been validated for production-scale
  concurrent workloads.

## Future Improvements

- Support more business datasets and database schemas.
- Add deterministic analytical validation.
- Improve agent evaluation with a benchmark dataset.
- Add user authentication and role-based access control.
- Introduce background task execution.
- Add workflow tracing and performance monitoring.
- Support downloadable reports.
- Improve dashboard interactivity.

