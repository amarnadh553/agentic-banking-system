
import asyncio
import time
from fastapi import HTTPException, APIRouter, Request
from fictional_bank.src import Logger
from fictional_bank.src.utilities import remove_newlines, generate_graph
from fictional_bank.models.banking import BankingResponse, BankingRequest, ExecutionTrace
from fictional_bank.src.utilities import get_selected_agents, get_selected_tools

logger = Logger().get_logger(__name__)


router = APIRouter(prefix="/api/v1/banking", tags=["Banking"])


@router.post("/ask", response_model=BankingResponse)
async def ask_banking_agent(request: Request, payload: BankingRequest):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Please provide a banking question.")
    logger.info("Banking request received")
    try:
        started = time.perf_counter()
        # banking_app = request.state.banking_app
        banking_app = request.app.state.banking_app
        result = await banking_app.run(question)
        # try:
        #     logger.info("Waiting for LangGraph execution...")
        #     result = await asyncio.wait_for(banking_app.run(question), timeout=60)
        #     logger.info("LangGraph completed in %.2f seconds", time.perf_counter() - started)
        # except asyncio.TimeoutError as exc:
        #     logger.error("Banking request timed out after %.2f seconds", time.perf_counter() - started)
        #     raise HTTPException(status_code=504, detail="Banking request timed out after 60 seconds.") from exc
        print("RES START", result, "RES END")
        logger.info("Banking request completed; selected_agent=%s", result.get("selected_agent", "UNKNOWN"))
        graph_image_url = None
        if payload.visualize_graph:
            generate_graph(banking_app)
        latency_seconds = round(time.perf_counter() - started, 3)
        # return BankingResponse(
        #     selected_agents=get_selected_agents(result, question),
        #     selected_tools=get_selected_tools(result),
        #     model_name=banking_app.config.LLM_MODEL_NAME,
        #     latency_seconds=latency_seconds,
        #     selected_agent=result.get("selected_agent", ""),
        #     reasoning=result.get("reasoning", ""),
        #     response=remove_newlines(result.get("response", "")),
        # )
        return BankingResponse(
            reasoning=result.get("reasoning", ""),
            response=remove_newlines(result.get("response", "")),
            trace=ExecutionTrace(
                selected_agent=result.get("selected_agent", ""),
                selected_agents=get_selected_agents(result, question),
                selected_tools=get_selected_tools(result),
                model_name=banking_app.config.LLM_MODEL_NAME,
                latency_seconds=latency_seconds,
            ),
        )

    except Exception as exc:
        logger.exception("Banking request processing failed")
        raise HTTPException(status_code=500, detail=f"""Failed to process the banking request.{exc}""")



