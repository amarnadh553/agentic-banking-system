
class LatencyEvaluator:
    def __init__(self, max_latency_seconds: float = 10.0):
        if max_latency_seconds <= 0:
            raise ValueError("Latency threshold must be positive.")

        self.max_latency_seconds = max_latency_seconds

    def evaluate(self, record: dict) -> dict:
        latency = record.get("latency_seconds", 0.0)
        passed = (
            record.get("execution_success", False)
            and latency <= self.max_latency_seconds
        )

        return {
            "latency_passed": passed,
            "latency_seconds": latency,
            "latency_reason": (
                f"{latency:.3f}s "
                f"(threshold: {self.max_latency_seconds:.3f}s)"
            ),
        }
