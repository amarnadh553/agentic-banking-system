
import json
from pathlib import Path
import pandas as pd


# Path to your evaluation report
report_path = Path(r'C:\Users\Amarnadh\Documents\DATA_SCIENCE\LEARNING\AGENTIC_AI\fictional_bank_bot\fictional_bank\evaluation\golden\evaluation_report.json')

# Output files
output_dir = report_path.parent
csv_path = output_dir / "evaluation_overview.csv"
json_path = output_dir / "evaluation_overview.json"


def create_evaluation_overview(report_path):
    with open(report_path, "r", encoding="utf-8") as file:
        report_data = json.load(file)

    if isinstance(report_data, dict):
        report_data = report_data.get("results", report_data.get("test_cases", []))

    rows = []

    for item in report_data:
        details = item.get("details", {})

        tool = details.get("tool_selection", {})
        trajectory = details.get("trajectory", {})
        latency = details.get("latency", {})
        safety = details.get("safety_reliability", {})

        answer_score = item.get("answer_score", 0) or 0
        answer_correct = item.get("answer_correct", False)

        tool_correct = (
            item.get(
                "agent_selection_correct",
                tool.get("agent_selection_correct", False),
            )
            and item.get(
                "tool_selection_correct",
                tool.get("tool_selection_correct", False),
            )
        )

        trajectory_correct = item.get(
            "trajectory_correct",
            trajectory.get("trajectory_correct", False),
        )

        latency_seconds = item.get(
            "latency_seconds",
            latency.get("latency_seconds"),
        )

        latency_pass = item.get(
            "latency_passed",
            latency.get("passed", False),
        )

        safe_reliable = item.get(
            "overall_safety_reliability_passed",
            safety.get("overall_passed", False),
        )

        # Overall score: five equally weighted dimensions.
        # Answer score is already expressed as a percentage.
        tool_score = (
            item.get("agent_selection_score", tool.get("agent_selection_score", 0))
            + item.get("tool_selection_score", tool.get("tool_selection_score", 0))
        ) / 2

        trajectory_score = item.get(
            "trajectory_score",
            trajectory.get("trajectory_score", 0),
        )

        score = round(
            (
                answer_score
                + tool_score
                + trajectory_score
                + (100 if latency_pass else 0)
                + (100 if safe_reliable else 0)
            ) / 5,
            2,
        )

        rows.append({
            "Test Case": item.get("qa_id", item.get("question", "Unknown")),
            "Answer Correct": answer_correct,
            "Tool Correct": tool_correct,
            "Trajectory Correct": trajectory_correct,
            "Latency (s)": latency_seconds,
            "Latency Pass": latency_pass,
            "Safe/Reliable": safe_reliable,
            "Score (%)": score,
        })

    df = pd.DataFrame(rows)

    # Save overview reports
    df.to_csv(csv_path, index=False)
    df.to_json(json_path, orient="records", indent=4)

    print("\nEVALUATION OVERVIEW\n")
    print(df.to_string(index=False))

    print(f"\nCSV report saved:  {csv_path}")
    print(f"JSON report saved: {json_path}")

    return df


if __name__ == "__main__":
    overview_df = create_evaluation_overview(report_path)
