
class ToolEvaluator:
    # Replace these examples with your actual registered tool names.
    EXPECTED_TOOLS_BY_AGENT = {
        "accounts": set(),       # e.g. {"get_customer_details"}
        "transactions": set(),  # e.g. {"get_recent_transactions"}
        "service": set(),       # e.g. {"get_service_requests"}
        "clarification": set(),
    }

    def evaluate(self, record: dict) -> dict:
        expected_agent = record["expected_agent"].strip().lower()
        actual_calls = record.get("tool_calls", [])

        actual_tools = {
            item.get("tool", "")
            for item in actual_calls
            if item.get("status") in {"started", "completed"}
        }

        expected_tools = self.EXPECTED_TOOLS_BY_AGENT.get(
            expected_agent, set()
        )

        if not expected_tools:
            return {
                "tool_selection_correct": None,
                "tool_reason": (
                    "Expected tool mapping is not configured; "
                    "tool selection cannot yet be scored reliably."
                ),
                "actual_tools": sorted(actual_tools),
            }

        missing = expected_tools - actual_tools

        return {
            "tool_selection_correct": not missing,
            "tool_reason": (
                "All expected tools were observed."
                if not missing
                else f"Missing expected tool calls: {sorted(missing)}"
            ),
            "actual_tools": sorted(actual_tools),
        }
