
import time
from fastapi import HTTPException, APIRouter, Request
from fictional_bank.src import Logger
from fictional_bank.src.utilities import remove_newlines, generate_graph
from fictional_bank.models.banking import BankingResponse, BankingRequest, ExecutionTrace
from fictional_bank.src.utilities import get_selected_agents, get_selected_tools
from langchain_core.callbacks import get_usage_metadata_callback

logger = Logger().get_logger(__name__)


router = APIRouter(prefix="/api/v1/banking", tags=["Banking"])


def estimate_cost_usd(config, input_tokens: int, output_tokens: int) -> float:
    """Estimated cost from the per-1M-token prices in .env. The exact bill is in LangSmith / OpenAI usage."""
    cost = (input_tokens * config.INPUT_PRICE_PER_1M_TOKENS + output_tokens * config.OUTPUT_PRICE_PER_1M_TOKENS) / 1_000_000
    return round(cost, 6)
 
 
@router.post("/ask", response_model=BankingResponse, response_model_exclude_none=True)
async def ask_banking_agent(request: Request, payload: BankingRequest):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Please provide a banking question.")
    logger.info("Banking request received")
    try:
        banking_app = request.app.state.banking_app
 
        started = time.perf_counter()
        with get_usage_metadata_callback() as usage:
            result = await banking_app.run(question)

        latency_seconds = round(time.perf_counter() - started, 3)
        logger.info("Banking request completed; selected_agent=%s", result.get("selected_agent", "UNKNOWN"))
 
        if payload.visualize_graph:
            generate_graph(banking_app)

        answer = result.get("response", "")
        trace = None
        if payload.include_trace:
            models = list(usage.usage_metadata.values())
            input_tokens = sum(m.get("input_tokens", 0) for m in models)
            output_tokens = sum(m.get("output_tokens", 0) for m in models)
            trace = ExecutionTrace(
                selected_agent=result.get("selected_agent", ""),
                selected_agents=get_selected_agents(result, question),
                selected_tools=get_selected_tools(result),
                model_name=banking_app.config.LLM_MODEL_NAME,
                latency_seconds=latency_seconds,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost_usd=estimate_cost_usd(banking_app.config, input_tokens, output_tokens),
            )
 
        return BankingResponse(
            reasoning=result.get("reasoning", ""),
            # response=remove_newlines(result.get("response", "")),
            response=answer if payload.keep_formatting else remove_newlines(answer),
            trace=trace,
        )
 
    except Exception as exc:
        logger.exception("Banking request processing failed")
        raise HTTPException(status_code=500, detail=f"""Failed to process the banking request.{exc}""")


