from langgraph.graph import StateGraph, START, END

from fictional_bank.graph.state import AgentState
from fictional_bank.graph.routing import (
    router_node,
    accounts_node,
    transactions_node,
    service_node,
    synthesize_node,
    clarification_node,
    routing_logic,
)


class BuildGraph:
    """
    START -> router -> accounts      \\
                    -> transactions  -> synthesizer -> END   (only the chosen agents run, in parallel)
                    -> service       /
                    -> clarification -> END
    """

    def __init__(self, coordinator_agent, accounts_agent, transactions_agent, service_agent, synthesizer_agent):
        self.coordinator_agent = coordinator_agent
        self.accounts_agent = accounts_agent
        self.transactions_agent = transactions_agent
        self.service_agent = service_agent
        self.synthesizer_agent = synthesizer_agent

    async def router(self, state: AgentState) -> dict:
        return await router_node(state, self.coordinator_agent)

    # The three specialist nodes receive their own task (from Send), not the whole state.
    async def accounts(self, task: dict) -> dict:
        return await accounts_node(task, self.accounts_agent)

    async def transactions(self, task: dict) -> dict:
        return await transactions_node(task, self.transactions_agent)

    async def service(self, task: dict) -> dict:
        return await service_node(task, self.service_agent)

    async def synthesizer(self, state: AgentState) -> dict:
        return await synthesize_node(state, self.synthesizer_agent)

    def build(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("router", self.router)
        workflow.add_node("accounts", self.accounts)
        workflow.add_node("transactions", self.transactions)
        workflow.add_node("service", self.service)
        workflow.add_node("synthesizer", self.synthesizer)
        workflow.add_node("clarification", clarification_node)

        workflow.add_edge(START, "router")

        # routing_logic returns Send objects; the list below tells LangGraph (and the diagram) the possible targets.
        workflow.add_conditional_edges(
            "router",
            routing_logic,
            ["accounts", "transactions", "service", "clarification"],
        )

        workflow.add_edge("accounts", "synthesizer")
        workflow.add_edge("transactions", "synthesizer")
        workflow.add_edge("service", "synthesizer")
        workflow.add_edge("synthesizer", END)
        workflow.add_edge("clarification", END)
        return workflow.compile()
