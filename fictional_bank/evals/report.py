
import csv
import json
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "evaluation_reports"


def summarize_results(results: list[dict]) -> dict:
    total = len(results)

    if total == 0:
        return {"total_cases": 0, "passed": 0, "failed": 0}

    metrics = [
        "answer_correct",
        "tool_selection_correct",
        "trajectory_correct",
        "latency_passed",
        "safety_passed",
    ]

    summary = {
        "total_cases": total,
        "passed": sum(row.get("passed", False) is True for row in results),
        "failed": sum(row.get("passed", False) is not True for row in results),
        "metrics": {},
    }

    for metric in metrics:
        measured = [
            row[metric] for row in results
            if row.get(metric) is not None
        ]

        summary["metrics"][metric] = {
            "measured": len(measured),
            "not_measured": total - len(measured),
            "passed": sum(value is True for value in measured),
            "pass_rate_percent": (
                round(
                    100 * sum(value is True for value in measured)
                    / len(measured),
                    2,
                )
                if measured else None
            ),
        }

    summary["overall_pass_rate_percent"] = round(
        100 * summary["passed"] / total, 2
    )

    summary["average_latency_seconds"] = round(
        sum(row.get("latency_seconds", 0.0) for row in results) / total,
        3,
    )

    return summary


def save_report(results: list[dict], summary: dict) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = REPORT_DIR / f"evaluation_{timestamp}.json"
    csv_path = REPORT_DIR / f"evaluation_{timestamp}.csv"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(
            {"summary": summary, "results": results},
            file,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    # Flatten nested fields so the CSV is easy to open in Excel.
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        if results:
            columns = sorted({
                key for row in results for key in row
                if not isinstance(row.get(key), (dict, list))
            })
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()

            for row in results:
                writer.writerow({
                    key: row.get(key, "")
                    for key in columns
                })

    return csv_path, json_path
