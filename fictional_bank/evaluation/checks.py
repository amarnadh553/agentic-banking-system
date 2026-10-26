import re
import json
from langchain_openai import ChatOpenAI
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
        result = json.loads(response.content)
        score = max(0, min(100, int(result['score_percentage'])))
        return {"score_percentage": score, "correct": score >= 80, "reason": result.get("reason", "")}
    except Exception as e:
        return {"score_percentage": None, "correct": None, "reason": f"Evaluation failed: {e}"}


# result = evaluate_answer_correctness(
#     llm=llm,
#     question="Can you show the customer details for C001?",
#     expected_answer=("C001 is Aarav Rao (email: aarav.rao1@example.com, status: Active)."),
#     agent_response=("- Name: Aarav Rao- Email: aarav.rao1@example.com- Status: Active")
#     )

# print(result)


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



test_case = {
    "qa_id": "Q002",
    "question": "Show C003's name, last 3 transactions and pending requests",
    "expected_agents": [
        "accounts",
        "transactions",
        "service"
    ],
    "expected_tools": [
        "get_customer_details_based_on_id",
        "get_recent_transactions",
        "get_pending_requests"
    ],
    "expected_answer": (
        "Customer C003 is Aditya Mehta. "
        "Show the 3 most recent transactions for C003 and "
        "any pending service requests."
    )
}
api_response={
  "reasoning": "The user asked for the customer's name, the most recent three transactions, and any pending service requests for C003. These require three different specialists: accounts for identity/name, transactions for recent activity, and service for current requests.",
  "response": "- Name: Aditya Mehta- Last 3 transactions for C003:Here are the last 3 transactions for C003:| Transaction ID | Account ID | Date       | Type   | Amount  | Currency | Description     | Status     ||----------------|------------|------------|--------|---------|----------|-----------------|------------|| T00073         | A0006      | 11-10-2026 | Debit  | 20182.16| INR      | ATM Withdrawal  | Failed     || T00057         | A0006      | 04-10-2026 | Credit | 44539.89| INR      | Refund          | Successful || T00076         | A0006      | 02-10-2026 | Credit | 25539.92| INR      | Refund          | Successful |Note: There are 34 matching transactions in total. Showing 3 newest of 34. If you’d like, I can show the next set, or filter by date range or transaction type (debit/credit).- Pending requests: There are no pending service requests for customer C003. Would you like me to show all requests for C003 or check a specific request by ID?",
  "trace": {
    "selected_agent": "accounts,transactions,service",
    "selected_agents": [
      {
        "agent": "accounts",
        "question": "What is the name of customer C003?"
      },
      {
        "agent": "transactions",
        "question": "Show the last 3 transactions for customer C003."
      },
      {
        "agent": "service",
        "question": "List the pending service requests for customer C003."
      }
    ],
    "selected_tools": [
      {
        "agent": "accounts",
        "tool": "get_customer_details_based_on_id",
        "args": {
          "customer_id": "C003"
        }
      },
      {
        "agent": "transactions",
        "tool": "get_recent_transactions",
        "args": {
          "customer_id": "C003",
          "limit": 3
        }
      },
      {
        "agent": "service",
        "tool": "get_pending_requests",
        "args": {
          "customer_id": "C003"
        }
      }
    ],
    "model_name": "gpt-5-nano",
    "latency_seconds": 23.961
  },
  "graph_image_url": None
}

# result = evaluate_tool_selection(
#     expected_agents=test_case["expected_agents"],
#     expected_tools=test_case["expected_tools"],
#     api_response=api_response,
# )

# print(result)


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


# test_case = {
#     "qa_id": "Q002",
#     "question": (
#         "Show C003's name, last 3 transactions "
#         "and pending requests"
#     ),
#     "expected_agents": [
#         "accounts",
#         "transactions",
#         "service",
#     ],
#     "expected_tools": [
#         "get_customer_details_based_on_id",
#         "get_recent_transactions",
#         "get_pending_requests",
#     ],
#     "expected_trajectory": [
#         {
#             "agent": "accounts",
#             "tool": "get_customer_details_based_on_id",
#         },
#         {
#             "agent": "transactions",
#             "tool": "get_recent_transactions",
#         },
#         {
#             "agent": "service",
#             "tool": "get_pending_requests",
#         },
#     ],
#     "expected_answer": (
#         "Customer C003 is Aditya Mehta. "
#         "Return the three most recent transactions and "
#         "any pending service requests."
#     ),
# }
# trajectory_result = evaluate_trajectory(
#     expected_trajectory=test_case["expected_trajectory"],
#     api_response=api_response,
# )

# print(trajectory_result)



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

test_case={
  "reasoning": "The user asked for the customer's name, the most recent three transactions, and any pending service requests for C003. These require three different specialists: accounts for identity/name, transactions for recent activity, and service for current requests.",
  "response": "- Name: Aditya Mehta- Last 3 transactions for C003:Here are the last 3 transactions for C003:| Transaction ID | Account ID | Date       | Type   | Amount  | Currency | Description     | Status     ||----------------|------------|------------|--------|---------|----------|-----------------|------------|| T00073         | A0006      | 11-10-2026 | Debit  | 20182.16| INR      | ATM Withdrawal  | Failed     || T00057         | A0006      | 04-10-2026 | Credit | 44539.89| INR      | Refund          | Successful || T00076         | A0006      | 02-10-2026 | Credit | 25539.92| INR      | Refund          | Successful |Note: There are 34 matching transactions in total. Showing 3 newest of 34. If you’d like, I can show the next set, or filter by date range or transaction type (debit/credit).- Pending requests: There are no pending service requests for customer C003. Would you like me to show all requests for C003 or check a specific request by ID?",
  "trace": {
    "selected_agent": "accounts,transactions,service",
    "selected_agents": [
      {
        "agent": "accounts",
        "question": "What is the name of customer C003?"
      },
      {
        "agent": "transactions",
        "question": "Show the last 3 transactions for customer C003."
      },
      {
        "agent": "service",
        "question": "List the pending service requests for customer C003."
      }
    ],
    "selected_tools": [
      {
        "agent": "accounts",
        "tool": "get_customer_details_based_on_id",
        "args": {
          "customer_id": "C003"
        }
      },
      {
        "agent": "transactions",
        "tool": "get_recent_transactions",
        "args": {
          "customer_id": "C003",
          "limit": 3
        }
      },
      {
        "agent": "service",
        "tool": "get_pending_requests",
        "args": {
          "customer_id": "C003"
        }
      }
    ],
    "model_name": "gpt-5-nano",
    "latency_seconds": 23.961
  },
  "graph_image_url": None
}
# latency_result = evaluate_latency(
#     test_case,
#     threshold_seconds=30.0
# )

# print(json.dumps(latency_result, indent=4))


import re


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
actual_response = test_case
safety_reliability_result = evaluate_safety_reliability(
    actual_response
)

print(json.dumps(safety_reliability_result, indent=4))