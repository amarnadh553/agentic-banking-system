# Fictional Bank Bot

A multi-agent banking assistant built with **LangGraph**, **MCP tools** and **FastAPI**, plus an **evaluation suite** that scores every answer on five checks.

Ask a question in plain English, even one that needs several kinds of data:

> *Show C003's name, last 3 transactions and pending requests*

A router splits it into sub-questions, the specialist agents answer in parallel using MCP tools, and a synthesizer merges them into one reply. The API also returns a `trace` showing which agents and tools were used.

> All data is fictional (CSV files). No real customer or banking information is used.

---

## Features

- **Router with multi-intent planning:** one question can go to several agents at once.
- **Three specialist agents:** accounts, transactions and service requests, each with its own tools.
- **Parallel execution:** the selected agents run at the same time.
- **Synthesizer:** merges several answers into one reply (skipped when only one agent answers).
- **Clarification path:** vague questions get a follow-up question instead of a guess.
- **MCP servers:** tools are exposed over MCP, so they also work in Claude Desktop.
- **Trace in every response:** selected agents, tool calls with arguments, model name and latency.
- **Evaluation suite:** golden dataset, LLM judge, tool-selection, trajectory, latency and safety checks, with JSON and CSV reports.

---

## Architecture

```
                 User question
                       |
                 FastAPI  (/api/v1/banking/ask)
                       |
                LangGraph: Router (CoordinatorAgent)
                       |   structured output: list of {agent, question}
        +--------------+---------------+---------------+
        |              |               |               |
    accounts      transactions      service      clarification
     agent           agent           agent        (vague question)
        |              |               |               |
     MCP tools     MCP tools       MCP tools            |
        |              |               |               |
        +--------------+---------------+               |
                       |                               |
                  Synthesizer  -----------------------+
                       |
          response + trace (agents, tools, model, latency)
```

How a request flows:

1. **Router** reads the question and returns a plan: which agents to call, each with a self-contained sub-question.
2. **Specialist agents** run in parallel. Each one calls its MCP tools and writes its own result to the shared state (`accounts_result`, `transactions_result`, `service_result`), so no state merging is needed.
3. **Synthesizer** combines the results into one answer. With a single answer it passes it through without an extra LLM call.
4. **API** returns the answer and a `trace`.

**Why a router and not a supervisor?** The sub-questions are independent, so the router can plan everything up front. A supervisor loop is only needed when one step depends on the result of another.

### Agents and tools

| Agent | What it handles | Example tools |
|---|---|---|
| accounts | customer details, accounts, balances, status | `get_customer_details_based_on_id`, `get_customer_accounts_based_on_customer_id`, `get_account_balance`, `get_total_balance` |
| transactions | recent transactions, search by date, status | `get_recent_transactions`, `search_transactions_by_date` |
| service | service requests and their status | `get_service_requests`, `get_request_status`, `get_pending_requests` |
| clarification | questions that are too vague to answer | none |

### Data

Four CSV files: `customers.csv`, `accounts.csv`, `transactions.csv`, `service_requests.csv`.

---

## Project structure

Adjust names if your folders differ.

```
fictional_bank_bot/
├── fictional_bank/
│   ├── agents/            # base agent, accounts, transactions, service, router, synthesizer
│   ├── graph/             # state.py, banking_graph.py
│   ├── tools/             # tool functions
│   ├── mcp_servers/       # MCP servers (stdio)
│   ├── api/               # main.py (FastAPI)
│   ├── data/              # the four CSV files
│   ├── evals/             # evaluation suite
│   │   ├── checks.py
│   │   ├── report.py
│   │   ├── run_eval.py
│   │   └── golden/banking_golden_dataset.csv
│   └── config.py
├── evaluation_reports/    # generated JSON and CSV reports
├── .env                   # your keys (not committed)
├── requirements.txt
└── README.md
```

---

## Getting started

### 1. Install

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_key_here
LLM_MODEL_NAME=gpt-5-nano
```

### 3. Run the API

From the project root:

```bash
uvicorn fictional_bank.api.main:app
```

Open `http://127.0.0.1:8000/docs` for the interactive docs.

### 4. Ask a question

```bash
curl -X POST http://127.0.0.1:8000/api/v1/banking/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Show C003'"'"'s name, last 3 transactions and pending requests"}'
```

Response shape:

```json
{
  "reasoning": "The question needs customer details, transactions and service requests.",
  "response": "…final answer…",
  "trace": {
    "selected_agent": "accounts,transactions,service",
    "selected_agents": [
      {"agent": "accounts", "question": "Show the name of customer C003"},
      {"agent": "transactions", "question": "Show the last 3 transactions of customer C003"},
      {"agent": "service", "question": "Show the pending service requests of customer C003"}
    ],
    "selected_tools": [
      {"agent": "accounts", "tool": "get_customer_details_based_on_id", "args": {"customer_id": "C003"}}
    ],
    "model_name": "gpt-5-nano",
    "latency_seconds": 14.657
  },
  "graph_image_url": null
}
```

The example values are illustrative. `trace` shows exactly which agents and tools ran for each question.

### 5. Use the tools in Claude Desktop (optional)

The MCP servers can be added to Claude Desktop's config so you can ask the same questions there. Use absolute paths, and make sure the `.env` file is found (the servers need `OPENAI_API_KEY` and `LLM_MODEL_NAME`).

---

## Evaluation suite

The suite sends every question in the golden dataset to the running API and scores each answer on five checks.

| Check | What it tests | How |
|---|---|---|
| **Answer** | Does the answer match the reference answer? | LLM judge scores accuracy and completeness (0 to 5). Passes at 4 or more on both. |
| **Tool selection** | Were the right tools used? | Compared with the accepted tool sets for the question's intent. Order does not matter. Alternatives are allowed. |
| **Trajectory** | Did the router pick the right agent(s)? | Expected agent set must equal the actual agent set. |
| **Latency** | Was the reply fast enough? | Measured end to end against `--max-latency`. |
| **Safety** | Did the answer invent or leak anything? | Same LLM judge call: invented data, other customers' data, secrets, bypassed rules. |

A question passes only if all five checks pass. A check that cannot be measured counts as not passed.

### Golden dataset

`fictional_bank/evals/golden/banking_golden_dataset.csv` has 141 questions.

| Type | Examples |
|---|---|
| Single agent | customer details, balances, recent transactions, transactions by date, service request status |
| Multi agent | "Show C003's name, last 3 transactions and pending requests" |
| Ambiguous | vague questions that should trigger clarification |

Columns: `qa_id, question, expected_agent, expected_answer, intent, source_tables, evaluation_notes`.

For multi-agent rows, `expected_agent` and `intent` are joined with `+`, for example `accounts+transactions+service` and `customer_details+recent_transactions+pending_requests`.

### Run it

Start the API first, then from the project root:

```bash
python -m fictional_bank.evals.run_eval --limit 5     # quick check
python -m fictional_bank.evals.run_eval               # all questions
```

| Option | Default | Meaning |
|---|---|---|
| `--limit N` | all | run only the first N questions |
| `--max-latency` | 10 | seconds allowed per question |
| `--concurrency` | 1 | questions at the same time (keep 1 for honest latency) |
| `--base-url` | `http://127.0.0.1:8000` | where the API runs |

Reports are saved in `evaluation_reports/` as JSON (full detail) and CSV (opens in Excel). The JSON has the run info, a summary (pass rate per check, per agent and per intent, average and p95 latency) and the result of every question.

### Results

Fill in after your final run.

| Metric | Result |
|---|---|
| Questions | 141 |
| Passed all five checks | _ / 141 |
| Answer | _ % |
| Tool selection | _ % |
| Trajectory | _ % |
| Latency (avg / p95) | _ s / _ s |
| Safety | _ % |

---

## Design decisions

- **Router over supervisor:** simpler and faster when the parts of a question are independent.
- **Separate state keys per agent:** parallel nodes cannot overwrite each other, so no reducers are needed.
- **One judge call for answer and safety:** one extra LLM call per question instead of two.
- **LLM judge instead of exact match:** answers are free text. The judge ignores wording and checks facts.
- **Trace in the API:** tool selection and trajectory are checked against what actually ran, not guessed from the answer.

## Known limitations

- Latency is high for multi-agent questions because each agent makes LLM calls.
- Dependent questions ("show the biggest transaction, then its service request") need a supervisor, which is not built.
- Data is read from CSV files and there is no authentication, so this is a demo, not production code.
- The LLM judge can make mistakes, so spot-check failures in the report.

## Roadmap

- Supervisor mode for dependent questions
- Real database and authentication
- Docker image
- Per-node latency breakdown and tracing (for example LangSmith)
- More safety tests (prompt injection, cross-customer data requests)

## Tech stack

Python, LangGraph, LangChain, OpenAI models, MCP, FastAPI, Pydantic, httpx.