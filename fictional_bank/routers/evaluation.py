
from pathlib import Path
from fastapi import APIRouter, Header, HTTPException
from fastapi.concurrency import run_in_threadpool

from fictional_bank.config import Config
from fictional_bank.evaluation.report import Evaluation
from fictional_bank.evaluation.run_eval import create_evaluation_overview
from fictional_bank.src import Logger

logger = Logger().get_logger(__name__)

router = APIRouter(prefix="/api/v1/evaluation", tags=["Evaluation"])


@router.post("/run")
async def run_evaluation(x_evaluation_token: str = Header(default="")):
    """Run the banking evaluation suite and generate reports."""
    config = Config()
    expected_token = config.EVALUATION_API_TOKEN
    if not expected_token or x_evaluation_token != expected_token:
        raise HTTPException(status_code=403, detail="Not authorized to run evaluations.")

    try:
        golden_dataset_path = Path(config.EVALUATION_GOLDEN_DATASET_PATH)
        report_json_path = Path(config.EVALUATION_REPORT_JSON_PATH)
        report_csv_path = Path(config.EVALUATION_REPORT_CSV_PATH)
        if not golden_dataset_path.is_file():
            raise HTTPException(status_code=404, detail=f"Golden dataset not found: {golden_dataset_path}")

        # Ensure the report directory exists
        Path(config.EVALUATION_REPORT_DIR).mkdir(parents=True, exist_ok=True)

        report_json_path.parent.mkdir(parents=True, exist_ok=True)
        report_csv_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize the evaluation runner
        print(config.API_URL, "API_URL_TESTING")
        evaluator = Evaluation(
            golden_dataset_path=str(golden_dataset_path),
            api_url=config.API_URL,
            latency_threshold=config.RESPONSE_LATENCY_THRESHOLD_IN_SECONDS,
            report_json_path=str(report_json_path),
            report_csv_path=str(report_csv_path),
        )

        # Run the evaluation without blocking the async API server
        report_rows = await run_in_threadpool(evaluator.run)

        # Generate the overview reports
        overview_df = await run_in_threadpool(
            create_evaluation_overview,
            str(report_json_path),
            config.EVALUATION_OVERVIEW_JSON_PATH,
            config.EVALUATION_OVERVIEW_CSV_PATH,
        )

        return {
            "status": "completed",
            "total_test_cases": len(report_rows),
            "overview": overview_df.to_dict(orient="records"),
            "report_paths": {
                "report_json": str(report_json_path),
                "report_csv": str(report_csv_path),
                "overview_json": config.EVALUATION_OVERVIEW_JSON_PATH,
                "overview_csv": config.EVALUATION_OVERVIEW_CSV_PATH,
            },
            "message": "Evaluation reports generated successfully.",
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Evaluation execution failed")
        raise HTTPException(status_code=500, detail="Evaluation failed. Check the application logs.") from exc
