import os
import csv
from pathlib import Path

from fictional_bank.evals.models import GoldenTestCase


# PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = os.getcwd() + os.sep + 'fictional_bank' + os.sep + 'evals' + os.sep + 'golden'
DEFAULT_DATASET_PATH = PROJECT_ROOT + os.sep + "banking_golden_dataset.csv"

REQUIRED_COLUMNS = {
    "qa_id",
    "question",
    "expected_agent",
    "expected_answer",
    "intent",
    "source_tables",
    "evaluation_notes",
}


def load_golden_dataset(
    dataset_path: str | Path = DEFAULT_DATASET_PATH,
    limit: int | None = None,
) -> list[GoldenTestCase]:
    path = Path(dataset_path)

    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("The golden dataset is empty.")

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing CSV columns: {sorted(missing)}")

        cases = []
        seen_ids = set()

        for row_number, row in enumerate(reader, start=2):
            qa_id = (row.get("qa_id") or "").strip()

            if not qa_id or qa_id in seen_ids:
                raise ValueError(
                    f"Missing or duplicate qa_id at row {row_number}: {qa_id!r}"
                )

            question = (row.get("question") or "").strip()
            expected_agent = (row.get("expected_agent") or "").strip()
            expected_answer = (row.get("expected_answer") or "").strip()

            if not question or not expected_agent or not expected_answer:
                raise ValueError(
                    f"Missing question, expected_agent, or expected_answer "
                    f"for {qa_id}"
                )

            seen_ids.add(qa_id)

            cases.append(
                GoldenTestCase(
                    qa_id=qa_id,
                    question=question,
                    expected_agent=expected_agent,
                    expected_answer=expected_answer,
                    intent=(row.get("intent") or "").strip(),
                    source_tables=(row.get("source_tables") or "").strip(),
                    evaluation_notes=(
                        row.get("evaluation_notes") or ""
                    ).strip(),
                )
            )

    if limit is not None:
        if limit < 1:
            raise ValueError("limit must be positive.")
        cases = cases[:limit]

    return cases
