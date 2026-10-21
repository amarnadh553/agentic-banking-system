from langgraph.graph import StateGraph, START, END

from fictional_bank.graph.state import AgentState
from fictional_bank.graph.routing import (
    router_node,
    specialists_node,
    synthesize_node,
    clarification_node,
    routing_logic,
)


class BuildGraph:
    """
    START -> router -> (clarification -> END)
                    -> specialists (run in parallel) -> synthesizer -> END
    """

    def __init__(self, coordinator_agent, accounts_agent, transactions_agent, service_agent, synthesizer_agent):
        self.coordinator_agent = coordinator_agent
        self.synthesizer_agent = synthesizer_agent
        self.agents = {
            "accounts": accounts_agent,
            "transactions": transactions_agent,
            "service": service_agent,
        }

    async def router(self, state: AgentState) -> dict:
        return await router_node(state, self.coordinator_agent)

    async def specialists(self, state: AgentState) -> dict:
        return await specialists_node(state, self.agents)

    async def synthesizer(self, state: AgentState) -> dict:
        return await synthesize_node(state, self.synthesizer_agent)

    def build(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("router", self.router)
        workflow.add_node("specialists", self.specialists)
        workflow.add_node("synthesizer", self.synthesizer)
        workflow.add_node("clarification", clarification_node)

        workflow.add_edge(START, "router")
        workflow.add_conditional_edges(
            "router",
            routing_logic,
            {"specialists": "specialists", "clarification": "clarification"},
        )
        workflow.add_edge("specialists", "synthesizer")
        workflow.add_edge("synthesizer", END)
        workflow.add_edge("clarification", END)
        return workflow.compile()
