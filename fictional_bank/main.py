from contextlib import asynccontextmanager
from fastapi import FastAPI
from fictional_bank.config import Config
from fictional_bank.services import FictionalBankApplication
from fictional_bank.mcp_client import MCPToolClient
from fictional_bank.src import Logger
from fictional_bank.config import Config
from fictional_bank.routers import banking_router, evaluation_router





logger = Logger().get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect to domain MCP servers when FastAPI starts."""
    logger.info("Starting Banking API")
    try:
        async with MCPToolClient() as client:

            logger.info("Accounts tools: %s", [tool.name for tool in client.tools_for("accounts")],)
            logger.info("Transactions tools: %s", [tool.name for tool in client.tools_for("transactions")])
            logger.info("Service tools: %s", [tool.name for tool in client.tools_for("service")])

            logger.info("MCP servers connected successfully")
            app.state.banking_app = FictionalBankApplication(
                config=Config(),
                logger=Logger().get_logger(),
                accounts_tools=client.tools_for("accounts"),
                transactions_tools=client.tools_for("transactions"),
                service_tools=client.tools_for("service"),
            )
            logger.info("Banking application initialized successfully")
            yield
    except Exception:
        logger.exception("Banking API startup or runtime failed")
        raise

    finally:
        logger.info("Banking API shutdown completed")


app = FastAPI(
    title="Fictional Banking Agent API",
    description="REST API powered by LangGraph and MCP.",
    version="1.0.0",
    lifespan=lifespan,
)



@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Register API routers
app.include_router(banking_router)
app.include_router(evaluation_router)


# @app.post("/api/v1/banking/ask", response_model=BankingResponse)
# async def ask_banking_agent(request: BankingRequest):
#     question = request.question.strip()

#     if not question:
#         raise HTTPException(status_code=400, detail="Please provide a banking question.")
#     logger.info("Banking request received")
#     try:
#         started = time.perf_counter()
#         banking_app = app.state.banking_app
#         result = await banking_app.run(question)
#         print("RES START", result, "RES END")
#         logger.info("Banking request completed; selected_agent=%s", result.get("selected_agent", "UNKNOWN"))
#         graph_image_url = None
#         if request.visualize_graph:
#             generate_graph(banking_app)
#         latency_seconds = round(time.perf_counter() - started, 3)
#         # return BankingResponse(
#         #     selected_agents=get_selected_agents(result, question),
#         #     selected_tools=get_selected_tools(result),
#         #     model_name=banking_app.config.LLM_MODEL_NAME,
#         #     latency_seconds=latency_seconds,
#         #     selected_agent=result.get("selected_agent", ""),
#         #     reasoning=result.get("reasoning", ""),
#         #     response=remove_newlines(result.get("response", "")),
#         # )
#         return BankingResponse(
#             reasoning=result.get("reasoning", ""),
#             response=remove_newlines(result.get("response", "")),
#             trace=ExecutionTrace(
#                 selected_agent=result.get("selected_agent", ""),
#                 selected_agents=get_selected_agents(result, question),
#                 selected_tools=get_selected_tools(result),
#                 model_name=banking_app.config.LLM_MODEL_NAME,
#                 latency_seconds=latency_seconds,
#             ),
#         )

#     except Exception as exc:
#         logger.exception("Banking request processing failed")
#         raise HTTPException(status_code=500, detail=f"""Failed to process the banking request.{exc}""")



# app.include_router(banking_router)

# @app.post("/api/v1/evaluation/run")
# async def run_evaluation(x_evaluation_token: str = Header(default="")):
#     """Run the banking evaluation suite and generate reports."""
#     config = Config()
#     # Load paths from configuration
#     expected_token = config.EVALUATION_API_TOKEN
#     golden_dataset_path = Path(config.EVALUATION_GOLDEN_DATASET_PATH)
#     report_json_path = Path(config.EVALUATION_REPORT_JSON_PATH)

#     if not expected_token or x_evaluation_token != expected_token:
#         raise HTTPException(status_code=403, detail="Not authorized to run evaluations.")

#     try:
#         # Validate the golden dataset
#         if not golden_dataset_path.exists():
#             raise HTTPException(status_code=404, detail=f"Golden dataset not found: {golden_dataset_path}")

#         # Create the report directory if it doesn't exist
#         Path(config.EVALUATION_REPORT_DIR).mkdir(parents=True, exist_ok=True)

#         # Initialize evaluator
#         evaluator = Evaluation(
#             golden_dataset_path=str(golden_dataset_path),
#             api_url=config.API_URL,
#             latency_threshold=config.RESPONSE_LATENCY_THRESHOLD_IN_SECONDS,
#             report_json_path=config.EVALUATION_REPORT_JSON_PATH,
#             report_csv_path=config.EVALUATION_REPORT_CSV_PATH,
#         )

#         # Run evaluation without blocking the async API server
#         report_rows = await run_in_threadpool(evaluator.run)

#         # Generate evaluation overview using configured paths
#         # overview_df = await run_in_threadpool(
#         #     create_evaluation_overview,
#         #     str(report_json_path),
#         #     output_json_path=config.EVALUATION_OVERVIEW_JSON_PATH,
#         #     output_csv_path=config.EVALUATION_OVERVIEW_CSV_PATH,
#         # )
#         overview_df = await run_in_threadpool(
#             create_evaluation_overview,
#             config.EVALUATION_REPORT_JSON_PATH,
#             config.EVALUATION_OVERVIEW_JSON_PATH,
#             config.EVALUATION_OVERVIEW_CSV_PATH,
#         )

#         return {
#             "status": "completed",
#             "total_test_cases": len(report_rows),
#             "overview": overview_df.to_dict(orient="records"),
#             "report_paths": {
#                 "report_json": config.EVALUATION_REPORT_JSON_PATH,
#                 "report_csv": config.EVALUATION_REPORT_CSV_PATH,
#                 "overview_json": config.EVALUATION_OVERVIEW_JSON_PATH,
#                 "overview_csv": config.EVALUATION_OVERVIEW_CSV_PATH,
#             },
#             "message": "Evaluation reports generated successfully.",
#         }

#     except HTTPException:
#         raise

#     except Exception as exc:
#         logger.exception("Evaluation execution failed")
#         raise HTTPException(status_code=500, detail=f"Evaluation failed. Check the application logs. {exc}") from exc