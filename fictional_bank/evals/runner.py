
import json
import os
import time
from typing import Any

import httpx


API_URL = os.getenv("BANKING_API_URL", "http://127.0.0.1:8000/api/v1/banking/ask")
REQUEST_TIMEOUT = 60.0


class EvaluationRunner:
    """Runs golden-dataset questions through the local FastAPI service."""

    def __init__(self, banking_app=None):
        # Kept for compatibility with existing EvaluationSuite construction.
        # HTTP requests are used instead of invoking the graph directly.
        self.banking_app = banking_app

    async def run_case(self, case, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
        started = time.perf_counter()

        record = {
            "qa_id": case.qa_id,
            "question": case.question,
            "expected_agent": case.expected_agent,
            "expected_answer": case.expected_answer,
            "evaluation_notes": case.evaluation_notes,
            "intent": case.intent,
            "source_tables": case.source_tables,
            "actual_agent": "",
            "actual_agents": [],
            "actual_answer": "",
            "tool_calls": [],
            "graph_nodes": [],
            "execution_success": False,
            "latency_seconds": 0.0,
            "error": "",
        }

        try:
            if client is None:
                async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as temporary_client:
                    response = await temporary_client.post(API_URL,json={"question": case.question})
                    response.raise_for_status()
                    output = response.json()
            else:
                response = await client.post(API_URL, json={"question": case.question})
                response.raise_for_status()
                output = response.json()

            if not isinstance(output, dict):
                raise ValueError("API response must be a JSON object.")

            # Support common response field names.
            record["actual_answer"] = str(
                output.get("response")
                or output.get("answer")
                or output.get("message")
                or ""
            )

            record["actual_agent"] = output.get("selected_agent", "")
            record["actual_agents"] = output.get("selected_agents", []) or []

            # These fields are populated only if the API explicitly
            # returns trace data. They cannot be inferred from the answer.
            record["tool_calls"] = output.get("tool_calls", [])
            record["graph_nodes"] = output.get("graph_nodes", [])

            if not record["actual_answer"].strip():
                raise ValueError(
                    "API returned no answer. Check the response schema."
                )

            record["execution_success"] = True

        except Exception as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"

        finally:
            record["latency_seconds"] = round(
                time.perf_counter() - started, 3
            )

        return record


async def main():
    from fictional_bank.evals.dataset import load_golden_dataset
    from fictional_bank.evals.evaluator import EvaluationSuite
    from fictional_bank.evals.report import (
        save_report,
        summarize_results,
    )

    # Start with five cases. Use limit=None for the full dataset.
    cases = load_golden_dataset(limit=5)

    # EvaluationSuite may require the application object for its LLM
    # evaluators. Initialize the existing app using its lifespan.
    from fictional_bank.api.main import app as fastapi_app

    async with fastapi_app.router.lifespan_context(fastapi_app):
        banking_app = fastapi_app.state.banking_app

        suite = EvaluationSuite(
            banking_app=banking_app,
            max_latency_seconds=10.0,
        )

        # The EvaluationSuite must use EvaluationRunner.run_case()
        # for these requests to pass through FastAPI.
        results = await suite.evaluate_all(cases)

        summary = summarize_results(results)
        csv_path, json_path = save_report(results, summary)

    print("\n========== EVALUATION SUMMARY ==========")
    print(json.dumps(summary, indent=2, default=str))
    print(f"\nCSV report:  {csv_path}")
    print(f"JSON report: {json_path}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())