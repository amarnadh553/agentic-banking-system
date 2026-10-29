import csv
import json
import re
from pathlib import Path
import requests
from fictional_bank.config import Config
from fictional_bank.models import LLMModelInitializer
from fictional_bank.models.llm_model import initialize_llm

llm = initialize_llm()

## Answer Correctness
def evaluate_answer_correctness(**kwargs):

    """
    Evaluate the agent answer correctness using LLM As A Judge.
    Returns : Dict containing correctness score (0 - 100) and reason
    """
    llm = kwargs.get("llm")
    question = kwargs.get("question")
    expected_answer = kwargs.get("expected_answer")
    agent_response = kwargs.get("agent_response")

    if not agent_response or not agent_response.strip():
        return {"score_percentage" : 0, "correct" : False, "reason" : "Agent returned an empty response"}

    prompt = f"""

            You are an evaluator for an Agentic Fictional banking system.

            Evaluate the actual agent response against the expected anser for the given question.

            QUESTION : 
            {question}

            EXPECTED ANSWER:
            {expected_answer}

            ACTUAL AGENT RESPONSE:
            {agent_response}

            Scoring criteria:
            - 100: All important facts are correct and all required information is present.
            - 80: Mostly correct, with a minor omission or insignificant issue.
            - 60: Partially correct, with some missing or incorrect information.
            - 40: Several important facts are missing or incorrect.
            - 20: Mostly incorrect, with very little useful correct information.
            - 0: Completely incorrect, irrelevant, or empty.

            Rules:
            1. Judge semantic correctness, not exact wording.
            2. Do not penalize harmless formatting differences.
            3. Penalize incorrect factual claims and important omissions.
            4. Extra information must not contradict the expected answer.
            5. For banking questions, consider unsupported or unrequested sensitive financial details when assessing correctness.
            6. Do not assume a claim is correct merely because the agent states it.

            Return only valid JSON in this format:
            {{
                "score_percentage": 0,
                "correct": false,
                "reason": "Brief explanation of the score"
            }}
    """
    try:
        response = llm.invoke(prompt)
        # response = llm.invoke(
        #     prompt,
        #     config={                                   # shows up in LangSmith as its own, filterable run
        #         "run_name": "eval_answer_judge",
        #         "tags": ["eval", "llm-judge"],
        #         "metadata": {"qa_id": kwargs.get("qa_id", "")},
        #     },
        # )
        result = json.loads(response.content)
        score = max(0, min(100, int(result['score_percentage'])))
        return {"score_percentage": score, "correct": score >= 80, "reason": result.get("reason", "")}
    except Exception as e:
        return {"score_percentage": None, "correct": None, "reason": f"Evaluation failed: {e}"}




def evaluate_tool_selection(**kwargs):

    """
    Evaluate agent and tool selection using the golden dataset and FastAPI response trace.

    Tool score:
        100% = exact match
        Partial score = partial overlap, penalizing extra tools
        0% = no matching tools

    Agent score is calculated separately.
    """

    expected_agents = kwargs.get("expected_agents")
    expected_tools = kwargs.get("expected_tools")
    api_response = kwargs.get("api_response")

    trace = api_response.get("trace") or {}

    actual_agents = {item["agent"].strip().lower() for item in trace.get("selected_agents", []) if item.get("agent")}
    actual_tools = {item["tool"].strip() for item in trace.get("selected_tools", []) if item.get("tool")}
    expected_agents_set = {agent.strip().lower() for agent in expected_agents}
    expected_tools_set = set(expected_tools)

    def score_selection(expected: set, actual: set) -> float:
        if not expected and not actual:
            return 100.0
        if not expected or not actual:
            return 0.0
        return round(len(expected & actual) / len(expected | actual) * 100, 2,)

    agent_score = score_selection(expected_agents_set, actual_agents)
    tool_score = score_selection(expected_tools_set, actual_tools)
    return {
        "agent_selection_score": agent_score,
        "tool_selection_score": tool_score,
        "agent_selection_correct": (expected_agents_set == actual_agents),
        "tool_selection_correct": (expected_tools_set == actual_tools),
        "expected_agents": sorted(expected_agents_set),
        "actual_agents": sorted(actual_agents),
        "expected_tools": sorted(expected_tools_set),
        "actual_tools": sorted(actual_tools),
    }





def evaluate_trajectory(**kwargs) -> dict:
    expected_trajectory = kwargs.get("expected_trajectory")
    api_response = kwargs.get("api_response")
    """
    Evaluate whether the agent workflow followed the expected trajectory.

    Each trajectory step contains:
        agent: expected agent name
        tool: expected tool name

    Returns a trajectory score (0-100), pass/fail, and mismatch details.
    """

    trace = api_response.get("trace") or {}

    # Actual agent and tool execution plan recorded by the API
    # Example  : [{'agent': 'accounts', 'tool': 'get_customer_details_based_on_id'}]
    actual_tools = trace.get("selected_tools") or []
    actual_trajectory = [{"agent": item["agent"].strip().lower(), "tool": item["tool"].strip()} for item in actual_tools if isinstance(item, dict) and item.get("agent") and item.get("tool")]
    expected = [{"agent": item["agent"].strip().lower(), "tool": item["tool"].strip()} for item in expected_trajectory]

    # Exact sequence comparison
    exact_match = expected == actual_trajectory

    # Count expected steps found in the actual sequence.
    # Each actual step can match only one expected step.
    unmatched_actual = actual_trajectory.copy()
    matched_steps = 0
    missing_steps = []

    for step in expected:
        if step in unmatched_actual:
            unmatched_actual.remove(step)
            matched_steps += 1
        else:
            missing_steps.append(step)

    extra_steps = unmatched_actual

    # Score combines step coverage and penalties for extra steps.
    total_steps = max(len(expected), len(actual_trajectory))

    if total_steps == 0:
        score = 100.0
    else:
        score = round(matched_steps / total_steps * 100, 2)

    return {
        "trajectory_score": score,
        "trajectory_correct": exact_match,
        "expected_trajectory": expected,
        "actual_trajectory": actual_trajectory,
        "missing_steps": missing_steps,
        "unexpected_steps": extra_steps,
        "trajectory_reason": (
            "Expected trajectory matches actual trace."
            if exact_match
            else "Expected and actual trajectories differ."
        ),
    }




def evaluate_latency(actual_response, threshold_seconds=10.0):
    """
    Evaluate API response latency against a threshold.
    """
    trace = actual_response.get("trace", {})
    latency = trace.get("latency_seconds")

    if latency is None:
        return {
            "latency_seconds": None,
            "threshold_seconds": threshold_seconds,
            "passed": False,
            "reason": "Latency information is missing from the API response."
        }

    passed = latency <= threshold_seconds

    return {
        "latency_seconds": round(latency, 3),
        "threshold_seconds": threshold_seconds,
        "passed": passed,
        "reason": (
            "Latency is within the threshold."
            if passed
            else "Latency exceeds the threshold."
        )
    }



def evaluate_safety_reliability(actual_response):
    response_text = actual_response.get("response", "")
    trace = actual_response.get("trace", {})

    # Reliability checks
    reliability_checks = {
        "response_present": bool(
            isinstance(response_text, str) and response_text.strip()
        ),
        "trace_present": bool(trace),
        "model_name_present": bool(trace.get("model_name")),
        "latency_present": trace.get("latency_seconds") is not None,
    }

    # Basic safety checks for accidental secret or internal-error exposure
    safety_checks = {
        "no_api_key_exposure": not bool(
            re.search(
                r"\bsk-[A-Za-z0-9_-]{10,}\b",
                response_text
            )
        ),
        "no_traceback_exposure": not bool(
            re.search(
                r"Traceback \(most recent call last\)|"
                r"File \".+\", line \d+",
                response_text
            )
        ),
    }

    reliability_passed = all(reliability_checks.values())
    safety_passed = all(safety_checks.values())

    return {
        "safety": {
            "passed": safety_passed,
            "checks": safety_checks,
        },
        "reliability": {
            "passed": reliability_passed,
            "checks": reliability_checks,
        },
        "overall_passed": safety_passed and reliability_passed,
    }


class Evaluation:
    def __init__(self, golden_dataset_path, api_url, latency_threshold, report_json_path, report_csv_path):
        from fictional_bank.src import Logger
        self.logger = Logger().get_logger(__name__)
        self.config = Config()
        self.llm_model_initializer = LLMModelInitializer(
            llm_model_name=self.config.LLM_MODEL_NAME,
            open_ai_api_key=self.config.OPENAI_API_KEY,
            temperature=self.config.TEMPERATURE,
            frequency_penalty=self.config.FREQUENCY_PENALTY,
            logger=self.logger,
        )
        self.llm = self.llm_model_initializer.initialise_llm_model()

        self.golden_dataset_path = Path(golden_dataset_path)
        self.api_url = api_url
        self.latency_threshold = latency_threshold
        self.report_json_path = Path(report_json_path)
        self.report_csv_path = Path(report_csv_path)
        self.timeout = 60

    @staticmethod
    def load_cases(data):
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("test_cases", "golden_data", "data"):
                if isinstance(data.get(key), list):
                    return data[key]
        raise ValueError("Golden dataset must be a list or a dict containing a test_cases list.")

    def _expected_trajectory(self, case):
        trajectory = case.get("expected_trajectory")
        if trajectory:
            return trajectory
        # If trajectory was not added to the golden data, infer agent-tool pairs
        # from tool names and expected agents without relying on list index alignment.
        tool_to_agent = {
            "get_customer_details_based_on_id": "accounts",
            "get_customer_accounts_based_on_customer_id": "accounts",
            "get_account_balance": "accounts",
            "get_total_balance": "accounts",

            "get_recent_transactions": "transactions",
            "search_transactions_by_date": "transactions",
            "filter_transactions_by_type": "transactions",
            "calculate_total_debits": "transactions",
            "calculate_total_credits": "transactions",

            "get_service_requests": "service",
            "get_request_status": "service",
            "get_pending_requests": "service",
            "count_service_requests": "service",
        }
        tools = case.get("expected_tools", case.get("expeced_tools", [])) or []
        return [{"agent": tool_to_agent[tool], "tool": tool} for tool in tools if tool in tool_to_agent]

    def _call_api(self, question):
        response = requests.post(self.api_url, json={"question": question}, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def run(self):
        with self.golden_dataset_path.open("r", encoding="utf-8") as f:
            golden_data = json.load(f)
        cases = self.load_cases(golden_data)
        report_rows = []

        for index, case in enumerate(cases, start=1):
            qa_id = case.get("qa_id", f"CASE_{index:03d}")
            question = case.get("question", "")
            print(f"Evaluating {qa_id}: {question}")
            row = {"qa_id": qa_id, "question": question}
            try:
                api_response = self._call_api(question)
                agent_response = api_response.get("response", "")
                expected_tools = case.get("expected_tools", case.get("expeced_tools", [])) or []
                expected_agents = case.get("expected_agents", []) or []

                answer_result = evaluate_answer_correctness(llm=self.llm, question=question, expected_answer=case.get("expected_answer", ""), agent_response=agent_response)
                tool_result = evaluate_tool_selection(expected_agents=expected_agents, expected_tools=expected_tools, api_response=api_response)
                trajectory_result = evaluate_trajectory(expected_trajectory=self._expected_trajectory(case), api_response=api_response)
                latency_result = evaluate_latency(api_response, self.latency_threshold)
                safety_result = evaluate_safety_reliability(api_response)

                row.update({
                    "api_success": True,
                    "answer_score": answer_result.get("score_percentage"),
                    "answer_correct": answer_result.get("correct"),
                    "answer_reason": answer_result.get("reason"),
                    "agent_selection_score": tool_result.get("agent_selection_score"),
                    "tool_selection_score": tool_result.get("tool_selection_score"),
                    "agent_selection_correct": tool_result.get("agent_selection_correct"),
                    "tool_selection_correct": tool_result.get("tool_selection_correct"),
                    "trajectory_score": trajectory_result.get("trajectory_score"),
                    "trajectory_correct": trajectory_result.get("trajectory_correct"),
                    "latency_seconds": latency_result.get("latency_seconds"),
                    "latency_threshold_seconds": latency_result.get("threshold_seconds"),
                    "latency_passed": latency_result.get("passed"),
                    "safety_passed": safety_result.get("safety", {}).get("passed"),
                    "reliability_passed": safety_result.get("reliability", {}).get("passed"),
                    "overall_safety_reliability_passed": safety_result.get("overall_passed"),
                    "model_name": (api_response.get("trace") or {}).get("model_name"),
                    "agent_response": agent_response,
                    "api_error": "",
                    "details": {
                        "tool_selection": tool_result,
                        "trajectory": trajectory_result,
                        "latency": latency_result,
                        "safety_reliability": safety_result,
                        "trace": api_response.get("trace", {}),
                    },
                })
            except Exception as exc:
                row.update({
                    "api_success": False,
                    "answer_score": None,
                    "answer_correct": None,
                    "answer_reason": None,
                    "agent_selection_score": None,
                    "tool_selection_score": None,
                    "agent_selection_correct": None,
                    "tool_selection_correct": None,
                    "trajectory_score": None,
                    "trajectory_correct": None,
                    "latency_seconds": None,
                    "latency_threshold_seconds": self.latency_threshold,
                    "latency_passed": False,
                    "safety_passed": None,
                    "reliability_passed": False,
                    "overall_safety_reliability_passed": False,
                    "model_name": None,
                    "agent_response": "",
                    "api_error": str(exc),
                    "details": {},
                })
            report_rows.append(row)

        json_path = self.report_json_path
        csv_path = self.report_csv_path
        json_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        # JSON retains nested diagnostic details; CSV flattens summary columns.
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(report_rows, f, indent=4, ensure_ascii=False, default=str)

        csv_columns = [
            "qa_id", "question", "api_success", "answer_score", "answer_correct",
            "answer_reason", "agent_selection_score", "tool_selection_score",
            "agent_selection_correct", "tool_selection_correct", "trajectory_score",
            "trajectory_correct", "latency_seconds", "latency_threshold_seconds",
            "latency_passed", "safety_passed", "reliability_passed",
            "overall_safety_reliability_passed", "model_name", "api_error",
            "agent_response", "details",
        ]
        with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=csv_columns, extrasaction="ignore")
            writer.writeheader()
            for row in report_rows:
                flat_row = dict(row)
                flat_row["details"] = json.dumps(row.get("details", {}), ensure_ascii=False, default=str)
                writer.writerow(flat_row)

        total = len(report_rows)
        print(f"\nEvaluation completed: {total} test cases")
        print(f"JSON report: {json_path}")
        print(f"CSV report : {csv_path}")
        return report_rows


# if __name__ == "__main__":
#     GOLDEN_DATASET_PATH = r"C:\Users\Amarnadh\Documents\DATA_SCIENCE\LEARNING\AGENTIC_AI\fictional_bank_bot\fictional_bank\evaluation\golden\gold_test.json"
#     evaluator = Evaluation(
#         golden_dataset_path=GOLDEN_DATASET_PATH,
#         api_url="http://127.0.0.1:8000/api/v1/banking/ask",
#         latency_threshold=10.0,
#     )
#     evaluator.run()
