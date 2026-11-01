
import json
import pandas as pd
from pathlib import Path

def create_evaluation_overview(report_path, output_json_path, output_csv_path):

    report_path = Path(report_path)
    output_json_path = Path(output_json_path)
    output_csv_path = Path(output_csv_path)

    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open("r", encoding="utf-8") as file:
        report_data = json.load(file)

    if isinstance(report_data, dict):
        report_data = report_data.get("results", report_data.get("test_cases", []))
    rows = []
    for item in report_data:
        details = item.get("details") or {}
        tool = details.get("tool_selection") or {}
        trajectory = details.get("trajectory") or {}
        latency = details.get("latency") or {}
        safety = details.get("safety_reliability") or {}
        api_success = bool(item.get("api_success", True))
        answer_score = item.get("answer_score") or 0
        answer_correct = bool(item.get("answer_correct"))
        agent_score = item.get("agent_selection_score") or tool.get("agent_selection_score") or 0
        tool_only_score = item.get("tool_selection_score") or tool.get("tool_selection_score") or 0
        tool_score = (agent_score + tool_only_score) / 2
        tool_correct = bool(item.get("agent_selection_correct")) and bool(item.get("tool_selection_correct"))
        trajectory_correct = bool(item.get("trajectory_correct"))
        trajectory_score = item.get("trajectory_score") or trajectory.get("trajectory_score") or 0
        latency_seconds = item.get("latency_seconds") or latency.get("latency_seconds")
        latency_pass = bool(item.get("latency_passed"))
        safe_reliable = bool(item.get("overall_safety_reliability_passed"))

        score = round((answer_score + tool_score + trajectory_score + (100 if latency_pass else 0) + (100 if safe_reliable else 0)) / 5, 2)

        rows.append({
            "Test Case": item.get("qa_id", item.get("question", "Unknown")),
            "API Success": api_success,
            "Answer Correct": answer_correct,
            "Tool Correct": tool_correct,
            "Trajectory Correct": trajectory_correct,
            "Latency (s)": latency_seconds,
            "Latency Pass": latency_pass,
            "Safe/Reliable": safe_reliable,
            "Score (%)": score,
        })

    # Convert the rows into a DataFrame
    df = pd.DataFrame(rows)

    # Save overview reports to the configured .env paths
    df.to_csv(output_csv_path, index=False)
    df.to_json(output_json_path, orient="records", indent=4)
    print("\nEVALUATION OVERVIEW\n")
    print(df.to_string(index=False))
    print(f"\nCSV report saved: {output_csv_path}")
    print(f"JSON report saved: {output_json_path}")

    return df