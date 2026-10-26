
class EvaluationSuite:
    def __init__(
        self,
        banking_app,
        max_latency_seconds: float = 10.0,
    ):
        from fictional_bank.evals.runner import EvaluationRunner
        from fictional_bank.evals.answer_evaluator import AnswerEvaluator
        from fictional_bank.evals.tool_evaluator import ToolEvaluator
        from fictional_bank.evals.trajectory_evaluator import (
            TrajectoryEvaluator,
        )
        from fictional_bank.evals.latency_evaluator import (
            LatencyEvaluator,
        )
        from fictional_bank.evals.safety_evaluator import (
            SafetyEvaluator,
        )

        self.runner = EvaluationRunner(banking_app)

        # Reuse the existing ChatOpenAI instance for both LLM judges.
        self.answer_evaluator = AnswerEvaluator(banking_app.llm)
        self.tool_evaluator = ToolEvaluator()
        self.trajectory_evaluator = TrajectoryEvaluator()
        self.latency_evaluator = LatencyEvaluator(max_latency_seconds)
        self.safety_evaluator = SafetyEvaluator(banking_app.llm)

    async def evaluate_case(self, case) -> dict:
        record = await self.runner.run_case(case)

        answer = await self.answer_evaluator.evaluate(record)
        tool = self.tool_evaluator.evaluate(record)
        trajectory = self.trajectory_evaluator.evaluate(record)
        latency = self.latency_evaluator.evaluate(record)
        safety = await self.safety_evaluator.evaluate(record)

        record.update(answer)
        record.update(tool)
        record.update(trajectory)
        record.update(latency)
        record.update(safety)

        checks = [
            record.get("answer_correct"),
            record.get("tool_selection_correct"),
            record.get("trajectory_correct"),
            record.get("latency_passed"),
            record.get("safety_passed"),
        ]

        # None means a metric is not configured or could not be measured.
        # Do not count an unverified test as a pass.
        record["passed"] = (
            record.get("execution_success", False)
            and all(value is True for value in checks)
        )

        return record

    async def evaluate_all(self, cases: list) -> list[dict]:
        results = []

        for index, case in enumerate(cases, start=1):
            result = await self.evaluate_case(case)
            results.append(result)

            print(
                f"[{index}/{len(cases)}] "
                f"{'PASS' if result['passed'] else 'FAIL'} "
                f"{case.qa_id}"
            )

        return results
