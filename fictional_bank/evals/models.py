from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GoldenTestCase:
    qa_id: str
    question: str
    expected_agent: str
    expected_answer: str
    intent: str = ""
    source_tables: str = ""
    evaluation_notes: str = ""


@dataclass
class EvaluationResult:
    qa_id: str
    question: str
    expected_agent: str
    expected_answer: str

    actual_agent: str = ""
    actual_answer: str = ""

    answer_correct: Optional[bool] = None
    tool_selection_correct: Optional[bool] = None
    trajectory_correct: Optional[bool] = None
    latency_passed: Optional[bool] = None
    safety_passed: Optional[bool] = None

    execution_success: bool = False
    latency_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)
    evaluator_reasons: dict[str, str] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        checks = [
            self.answer_correct,
            self.tool_selection_correct,
            self.trajectory_correct,
            self.latency_passed,
            self.safety_passed,
        ]
        return self.execution_success and all(
            check is True for check in checks
        )