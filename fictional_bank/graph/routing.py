import asyncio

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


async def specialists_node(state: AgentState, agents: dict) -> dict:
    """Run every planned specialist at the same time and collect their answers in plan order."""

    async def run_one(task: dict) -> dict:
        try:
            result = await agents[task["agent"]].run(task["question"])
            answer = str(result.get("result", result))
        except Exception as exc:  # one failing specialist must not lose the others' answers
            answer = f"This part could not be answered ({type(exc).__name__})."
        return {"agent": task["agent"], "question": task["question"], "answer": answer}

    answers = await asyncio.gather(*(run_one(t) for t in state["tasks"]))
    return {"answers": list(answers)}


async def synthesize_node(state: AgentState, synthesizer_agent) -> dict:
    """One answer is returned as is (no extra LLM call); several are merged into one reply."""
    answers = state["answers"]
    if len(answers) == 1:
        return {"response": answers[0]["answer"]}
    return {"response": await synthesizer_agent.run(state["question"], answers)}


def clarification_node(state: AgentState) -> dict:
    return {"response": "Could you please clarify your banking question?"}


def routing_logic(state: AgentState) -> str:
    """Go to the specialists when the plan has tasks, otherwise ask for clarification."""
    return "specialists" if state.get("tasks") else "clarification"
