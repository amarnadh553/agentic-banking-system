
def parse_agents(value) -> set[str]:
    if isinstance(value, list):
        values = value
    else:
        values = str(value or "").replace("+", ",").split(",")
    return {
        item.strip().lower()
        for item in values
        if item.strip()
    }


class TrajectoryEvaluator:
    def evaluate(self, record: dict) -> dict:
        expected = parse_agents(record["expected_agent"])

        actual = parse_agents(record.get("actual_agents", []))
        if not actual:
            actual = parse_agents(record.get("actual_agent", ""))

        routing_correct = expected == actual

        nodes = [
            str(node).strip().lower()
            for node in record.get("graph_nodes", [])
        ]

        # Graph node names are implementation-dependent. This is
        # supplementary evidence, not the sole source of truth.
        missing_nodes = [
            agent for agent in expected
            if agent in {"accounts", "transactions", "service"}
            and nodes
            and not any(agent in node for node in nodes)
        ]

        passed = routing_correct and not missing_nodes

        return {
            "trajectory_correct": passed,
            "trajectory_reason": (
                "Expected route observed."
                if passed
                else (
                    f"Expected agents={sorted(expected)}, "
                    f"actual agents={sorted(actual)}, "
                    f"missing graph-node evidence={missing_nodes}"
                )
            ),
        }
