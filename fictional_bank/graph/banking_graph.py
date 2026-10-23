from langgraph.graph import StateGraph, START, END
from fictional_bank.graph.state import AgentState


class BuildGraph:
    """
    START -> router -> accounts      \
                       transactions  -> synthesizer -> END    (only the agents the router picked run)
                       service       /
                       clarification -> END
    """

    def __init__(self, coordinator_agent, accounts_agent, transactions_agent, service_agent, synthesizer_agent):
        self.coordinator_agent = coordinator_agent
        self.accounts_agent = accounts_agent
        self.transactions_agent = transactions_agent
        self.service_agent = service_agent
        self.synthesizer_agent = synthesizer_agent

    # ---------------- Nodes ----------------

    async def router(self, state: AgentState) -> dict:
        """Ask the coordinator which specialists are needed and what each one should answer."""
        decision = await self.coordinator_agent.arun(state["question"])

        tasks = {}
        for task in decision.tasks:
            if task.agent != "clarification":
                tasks.setdefault(task.agent, task.question)

        return {
            "tasks": [{"agent": agent, "question": question} for agent, question in tasks.items()],
            "selected_agent": ",".join(tasks) or "clarification",
            "reasoning": decision.reasoning,
        }

    async def run_agent(self, name: str, agent, state: AgentState) -> str:
        """Find this agent's sub-question in the plan, run the agent and return its answer."""
        question = next(task["question"] for task in state["tasks"] if task["agent"] == name)
        result = await agent.run(question)
        return str(result.get("result", result))

    async def accounts(self, state: AgentState) -> dict:
        return {"accounts_answer": await self.run_agent("accounts", self.accounts_agent, state)}

    async def transactions(self, state: AgentState) -> dict:
        return {"transactions_answer": await self.run_agent("transactions", self.transactions_agent, state)}

    async def service(self, state: AgentState) -> dict:
        return {"service_answer": await self.run_agent("service", self.service_agent, state)}

    async def synthesizer(self, state: AgentState) -> dict:
        """Combine the specialists' answers into one reply."""
        answers = [{"agent": task["agent"], "question": task["question"], "answer": state[f"{task['agent']}_answer"]} for task in state["tasks"]]
        if len(answers) == 1:
            return {"response": answers[0]["answer"]}
        return {"response": await self.synthesizer_agent.run(state["question"], answers)}

    def clarification(self, state: AgentState) -> dict:
        return {"response": "Could you please clarify your banking question?"}

    # ---------------- routing ----------------

    def after_router(self, state: AgentState):
        """Return the node names to run next. Several names means they run in parallel."""
        if not state["tasks"]:
            return "clarification"
        return [task["agent"] for task in state["tasks"]]

    # ---------------- build graph----------------

    def build(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("router", self.router)
        workflow.add_node("accounts", self.accounts)
        workflow.add_node("transactions", self.transactions)
        workflow.add_node("service", self.service)
        workflow.add_node("synthesizer", self.synthesizer)
        workflow.add_node("clarification", self.clarification)

        workflow.add_edge(START, "router")
        workflow.add_conditional_edges(
            "router",
            self.after_router,
            ["accounts", "transactions", "service", "clarification"],
        )
        workflow.add_edge("accounts", "synthesizer")
        workflow.add_edge("transactions", "synthesizer")
        workflow.add_edge("service", "synthesizer")
        workflow.add_edge("synthesizer", END)
        workflow.add_edge("clarification", END)
        return workflow.compile()
