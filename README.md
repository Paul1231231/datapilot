# DataPilot — Planner-Driven Multi-Agent Analytics Platform

DataPilot is a local-first AI analytics platform that turns natural-language business questions into structured, evidence-based analysis.

Built with **CrewAI, Python, PostgreSQL, Pandas, Plotly, Streamlit, and Ollama**, DataPilot uses a Planner to decompose a business question into tasks and a controlled execution engine to run those tasks with specialized agents.

The core design principle is:

> **The Planner defines what work must be done. The execution engine follows the approved task list.**

The workflow does not automatically run every available agent. If the Planner does not create a Dashboard task, the Dashboard Agent is skipped. If the Planner creates three Data Engineer tasks, all three tasks must be executed and individually recorded.

---

## Contents

- [Project Goals](#project-goals)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Planner-Driven Execution](#planner-driven-execution)
- [Agent Responsibilities](#agent-responsibilities)
- [Execution Guarantees](#execution-guarantees)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Running an Analysis](#running-an-analysis)
- [Database Design](#database-design)
- [Testing](#testing)
- [Design Decisions](#design-decisions)
- [Limitations](#limitations)
- [Roadmap](#roadmap)

## Project Goals

DataPilot explores how to build a controlled multi-agent analytics system that can:

1. Understand a business question.
2. Decompose it into explicit, verifiable tasks.
3. Assign each task to a specialist agent.
4. Execute the tasks in the order defined by the plan.
5. Preserve intermediate results and execution history.
6. Validate the final analysis before returning it.

Rather than allowing agents to freely delegate work to one another, DataPilot uses application-level orchestration to keep execution observable and predictable.

## Key Features

- Natural-language business questions.
- Planner-generated task lists with agent assignments and dependencies.
- Task-level execution rather than a hardcoded sequence of agent stages.
- Specialized Planner, Data Engineer, Analyst, Dashboard, and QA agents.
- Structured agent contracts using Pydantic.
- PostgreSQL-backed synthetic sales dataset.
- SQL validation and read-only query execution.
- Pandas-based metric calculations.
- Plotly chart specifications and visualizations.
- QA review and bounded correction attempts.
- Persisted analysis runs and agent execution events.
- Local LLM inference through Ollama.
- Streamlit sales overview.

## Architecture

```mermaid
flowchart TD
    U[User Business Question] --> P[Planner Agent]
    P --> AP[AnalysisPlan]
    AP --> V[Plan Validator]
    V --> TE[Task Execution Engine]

    TE --> T{Next planned task}
    T -->|data_engineer| DE[Data Engineer]
    T -->|analyst| AN[Analyst]
    T -->|dashboard| DB[Dashboard Agent]

    DE --> R[Record Task Result]
    AN --> R
    DB --> R

    R --> C{More planned tasks?}
    C -->|Yes| T
    C -->|No| QA[QA Agent]

    QA -->|Pass| OUT[Final Report]
    QA -->|Correction required| COR[Targeted Correction]
    COR --> QA

    TE -.-> META[(PostgreSQL Run Metadata)]
    R -.-> META
    QA -.-> META
```

### Main components

| Component | Responsibility |
|---|---|
| Planner | Converts the business question into an ordered `AnalysisPlan` |
| Plan validator | Checks task IDs, agent assignments, and dependencies |
| Task execution engine | Executes every planned task using its assigned agent |
| Data Engineer | Retrieves relevant data using approved read-only database tools |
| Analyst | Calculates and interprets business metrics |
| Dashboard | Produces structured chart specifications when requested by the plan |
| QA | Reviews the completed work and requests bounded corrections |
| Flow state | Stores the plan, task results, analysis, charts, and run status |
| Metadata persistence | Records analysis runs and agent/task events |

## Planner-Driven Execution

The Planner returns an `AnalysisPlan` containing individual tasks. Each task includes a unique ID, a description, an assigned agent, and dependencies.

Example:

```json
{
  "objective": "Understand customer and regional performance",
  "tasks": [
    {
      "task_id": "T1",
      "description": "Retrieve customer data",
      "assigned_agent": "data_engineer",
      "dependencies": []
    },
    {
      "task_id": "T2",
      "description": "Retrieve regional data",
      "assigned_agent": "data_engineer",
      "dependencies": []
    },
    {
      "task_id": "T3",
      "description": "Analyze customer distribution",
      "assigned_agent": "analyst",
      "dependencies": ["T1"]
    },
    {
      "task_id": "T4",
      "description": "Analyze regional performance",
      "assigned_agent": "analyst",
      "dependencies": ["T2"]
    }
  ],
  "reasoning": "Investigate customer distribution and regional performance separately."
}
```

The execution engine iterates over the task list. It does not assume that every agent must run.

For the example above, the execution trace is:

```text
T1 -> Data Engineer -> completed
T2 -> Data Engineer -> completed
T3 -> Analyst       -> completed
T4 -> Analyst       -> completed
QA -> review
```

Each planned task receives its own execution and completion record. Agent instances can be reused across tasks, but task completion is tracked individually.

### Optional Dashboard execution

Dashboard is optional and plan-controlled.

- If the Planner includes a task assigned to `dashboard`, the Dashboard Agent executes it.
- If the Planner does not include a Dashboard task, the Dashboard Agent is not invoked.
- QA remains a system-level stage and is not optional.

### Dependency handling

Tasks must reference valid task IDs. In the initial sequential executor, dependencies must refer to tasks that appear earlier in the plan. This keeps execution deterministic and prevents a task from running before its required inputs exist.

The initial implementation executes tasks sequentially. Parallel execution is a future enhancement.

## Agent Responsibilities

| Agent | Responsibility |
|---|---|
| Planner | Breaks down the user question and assigns tasks |
| Data Engineer | Inspects the available schema and retrieves data |
| Analyst | Computes KPIs, comparisons, distributions, and trends |
| Dashboard | Creates chart specifications for planned visualization tasks |
| QA | Checks whether the completed analysis is supported by the retrieved evidence |

Agents are specialist workers. The execution engine—not an individual agent—controls task order and decides which planned task runs next.

## Execution Guarantees

The intended task-execution contract is:

1. Every task in a valid plan is attempted.
2. Tasks execute in the order defined by the plan.
3. Each task is sent to its declared agent.
4. A task is not marked complete until its execution returns successfully.
5. A failed task stops normal progression; it is not silently skipped.
6. Dashboard runs only when a Dashboard task exists in the plan.
7. QA runs after all planned tasks complete.
8. Task results and run events are persisted for inspection.

A successful Crew execution indicates that the task returned an output. It does not, by itself, prove that the SQL or business conclusion is correct. QA and deterministic checks are still necessary.

## Technology Stack

| Area | Technology |
|---|---|
| Language | Python |
| Package management | uv |
| Agent framework | CrewAI |
| Local model runtime | Ollama |
| LLM | Qwen3 (configurable) |
| Data contracts | Pydantic |
| Database | PostgreSQL |
| Database access | SQLAlchemy |
| SQL parsing and validation | SQLGlot |
| Data processing | Pandas |
| Visualization | Plotly |
| UI | Streamlit |
| Testing | Pytest |
| Local infrastructure | Docker Compose |

## Project Structure

The repository is organized by application responsibility:

```text
datapilot/
├── scripts/
│   ├── generate_data.py
│   ├── seed_database.py
│   ├── init_metadata.py
│   └── run_analytics.py
├── src/
│   └── datapilot/
│       ├── agents/
│       │   ├── planner.py
│       │   ├── data_engineer.py
│       │   ├── analyst.py
│       │   ├── dashboard.py
│       │   └── qa.py
│       ├── analytics/
│       ├── config/
│       ├── database/
│       ├── flows/
│       │   ├── analytics_flow.py
│       │   ├── state.py
│       │   └── task_executor.py
│       ├── schemas/
│       ├── tools/
│       ├── ui/
│       └── visualization/
├── tests/
├── artifacts/
│   └── charts/
├── .env.example
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

The `task_executor.py` entry above describes the planner-driven execution design. Keep this tree synchronized with the actual files in the repository.

## Getting Started

### Prerequisites

- Python version supported by the repository's `pyproject.toml` (currently Python 3.14 or newer).
- [uv](https://docs.astral.sh/uv/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Ollama](https://ollama.com/)

### 1. Clone the repository

```bash
git clone https://github.com/Paul1231231/datapilot.git
cd datapilot
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure environment variables

Create a local environment file:

```bash
cp .env.example .env
```

Configure the PostgreSQL connection and Ollama settings. For example:

```dotenv
DATABASE_URL=postgresql+psycopg://datapilot:datapilot_dev@localhost:5432/datapilot
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b
```

Use the variable names and model identifier defined by the current `.env.example` and settings implementation. Do not commit `.env` or credentials.

### 4. Start PostgreSQL

```bash
docker compose up -d
```

Check the container:

```bash
docker compose ps
```

### 5. Start Ollama

Make sure the Ollama service is running. Pull the model configured in `.env` if it is not already available:

```bash
ollama pull qwen3:8b
```

The model name above is an example; it must match `OLLAMA_MODEL`.

### 6. Generate and load synthetic data

Run the repository's data-generation and seeding scripts:

```bash
uv run python scripts/generate_data.py
uv run python scripts/seed_database.py
```

Initialize workflow metadata tables:

```bash
uv run python scripts/init_metadata.py
```

If your database setup requires manual schema initialization, apply the schema file before seeding.

> **Note:** The seed script is intended for an empty database. Do not rerun it against populated tables unless you have checked its behavior. Resetting Docker volumes deletes local database data.

### 7. Launch the Streamlit overview

```bash
uv run streamlit run src/datapilot/ui/app.py
```

Open [http://localhost:8501](http://localhost:8501).

The Streamlit sales overview and the CLI analytics workflow are separate entry points unless explicitly connected in the application.

## Running an Analysis

The CLI runner accepts a business question:

```bash
uv run python scripts/run_analytics.py --question "Which product category generates the most revenue?"
```

Another example:

```bash
uv run python scripts/run_analytics.py --question "Compare customer distribution across regions."
```

The runner should initialize the Flow and metadata persistence, pass the supplied question into the workflow state, and persist the final run status.

The exact command-line arguments are defined by `scripts/run_analytics.py`.

## Database Design

The synthetic sales database contains:

| Table | Description |
|---|---|
| `regions` | Sales regions |
| `customers` | Customers and their regions |
| `products` | Products and categories |
| `orders` | Customer orders and dates |
| `order_items` | Products, quantities, and unit prices per order |

Revenue is calculated as:

```sql
SUM(quantity * unit_price)
```

Workflow metadata is stored separately:

| Table | Description |
|---|---|
| `analysis_runs` | Run status, question, retry count, and serialized workflow state |
| `agent_events` | Execution events associated with a run |

### SQL safety

LLM-generated SQL is untrusted. Data access is routed through a SQL validation and read-only execution layer. SQL parsing is a safeguard, not a complete security boundary. A dedicated read-only PostgreSQL role and database-side permissions should be used wherever possible.

## Testing

Run the test suite:

```bash
uv run pytest -v
```

GitHub Actions runs unit and evaluation tests on every push and pull request;
integration tests run against PostgreSQL on `main` / `master` and PRs (see `.github/workflows/ci.yml`).

Run a specific test directory if present:

```bash
uv run pytest tests/unit -v
uv run pytest tests/integration -v
```

Integration tests may require PostgreSQL and a configured test database.

If coverage is installed:

```bash
uv run pytest --cov=datapilot --cov-report=term-missing
```

### Important planner-driven execution tests

The task executor should be tested independently of live LLM calls.

| Test | Expected behavior |
|---|---|
| Plan contains no Dashboard task | Dashboard is never invoked |
| Plan contains three Data Engineer tasks | All three tasks are executed |
| Plan contains multiple Analyst tasks | Every Analyst task is executed |
| Task references an unknown dependency | Plan validation fails |
| Task depends on a later task | Sequential plan validation fails |
| Agent execution raises an error | Workflow stops and records failure |
| All planned tasks complete | QA is invoked |
| QA rejects the result | Bounded correction policy is applied |

## Design Decisions

### Planner defines work; Flow controls execution

The Planner is responsible for deciding which tasks are necessary. The Flow validates the plan and controls execution. This separation prevents the system from running unnecessary agents or silently ignoring planned work.

### Task-level tracking

An agent-level status is not sufficient when an agent can receive multiple tasks. Each task has its own ID, status, output, and execution event. This makes retries, debugging, and auditing more precise.

### Sequential execution first

The initial executor follows the task list sequentially. This is easier to reason about and validate than parallel scheduling. Parallel execution can be added after dependency handling and task-level persistence are reliable.

### QA is mandatory

The Planner can decide whether visualization is needed, but it cannot remove system-level quality checks. QA is part of the application contract rather than an optional specialist task.

### Local inference

Ollama allows the project to run without depending on a paid hosted LLM API. Performance and output quality depend on the selected model and available hardware.

## Limitations

- The project uses synthetic sales data rather than a production business database.
- Local model quality and latency depend on the model and hardware.
- LLM-generated plans and explanations can still be incorrect.
- SQL validation does not replace database permissions and isolation.
- The initial task executor is sequential; it does not schedule independent tasks in parallel.
- A task returning successfully does not guarantee its business result is correct.
- The Streamlit overview is separate from the natural-language analytics runner unless connected explicitly.
- The application has not been validated for production-scale concurrency or multi-user deployment.

## Roadmap

- [x] Local development environment and PostgreSQL setup
- [x] Specialized analytics agents
- [x] Pydantic contracts for structured agent outputs
- [x] Synthetic sales dataset and read-only SQL tools
- [x] CrewAI Flow orchestration and shared state
- [x] Pandas analytics and Plotly chart specifications
- [x] QA review, bounded correction, and run persistence
- [x] Streamlit sales overview
- [ ] Complete and test strict Planner-driven task execution
- [ ] Task-level retry and targeted QA correction
- [ ] Deterministic evaluation and expanded test coverage
- [ ] Connect natural-language analytics runs to the Streamlit UI
- [ ] Add dependency-aware parallel task execution
- [ ] Improve observability and downloadable reports

## License

Add a `LICENSE` file and update this section to reflect the license you choose.
