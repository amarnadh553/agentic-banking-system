from langgraph.types import Send

from fictional_bank.graph.state import AgentState

SPECIALISTS = ("accounts", "transactions", "service")
MAX_TASKS = 3


def normalize_tasks(decision) -> list[dict]:
    """
    Turn the router's output into a safe plan: known specialists only, one task per specialist,
    in the order the router gave them. 'clarification' is kept only when nothing else is left.
    """
    merged: dict[str, str] = {}
    for task in getattr(decision, "tasks", None) or []:
        agent = (task.agent or "").strip().lower()
        question = (task.question or "").strip()
        if agent not in SPECIALISTS or not question:
            continue
        # two tasks for one specialist -> one combined question
        merged[agent] = f"{merged[agent]} Also: {question}" if agent in merged else question
    return [{"agent": a, "question": q} for a, q in list(merged.items())[:MAX_TASKS]]


async def router_node(state: AgentState, coordinator_agent) -> dict:
    """Ask the coordinator for a plan: which specialists, and what each should answer."""
    decision = await coordinator_agent.arun(state["question"])
    tasks = normalize_tasks(decision)
    return {
        "tasks": tasks,
        "selected_agent": ",".join(t["agent"] for t in tasks) or "clarification",
        "reasoning": decision.reasoning,
    }


async def run_specialist(task: dict, agent) -> dict:
    """Run one specialist on its sub-question. A failure is reported, not raised, so the other answers survive."""
    try:
        result = await agent.run(task["question"])
        answer = str(result.get("result", result))
    except Exception as exc:
        answer = f"This part could not be answered ({type(exc).__name__})."
    return {"answers": [{"agent": task["agent"], "question": task["question"], "answer": answer}]}


async def accounts_node(task: dict, accounts_agent) -> dict:
    return await run_specialist(task, accounts_agent)


async def transactions_node(task: dict, transactions_agent) -> dict:
    return await run_specialist(task, transactions_agent)


async def service_node(task: dict, service_agent) -> dict:
    return await run_specialist(task, service_agent)


async def synthesize_node(state: AgentState, synthesizer_agent) -> dict:
    """One answer is returned as is (no extra LLM call); several are merged into one reply."""
    order = {t["agent"]: i for i, t in enumerate(state["tasks"])}   # parallel results arrive in any order
    answers = sorted(state["answers"], key=lambda a: order.get(a["agent"], 99))
    if len(answers) == 1:
        return {"response": answers[0]["answer"]}
    return {"response": await synthesizer_agent.run(state["question"], answers)}


def clarification_node(state: AgentState) -> dict:
    return {"response": "Could you please clarify your banking question?"}


def routing_logic(state: AgentState):
    """Fan out: one Send per planned specialist (they run in parallel), or go to clarification."""
    tasks = state.get("tasks") or []
    if not tasks:
        return "clarification"
    return [Send(task["agent"], task) for task in tasks]
