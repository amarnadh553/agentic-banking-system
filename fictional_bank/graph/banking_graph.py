from langgraph.graph import StateGraph, START, END

from fictional_bank.graph import AgentState
from fictional_bank.graph.routing import router_node, accounts_node, transactions_node, service_node, clarification_node, routing_logic



class BuildGraph:

    def __init__(self, coordinator_agent, accounts_agent, transactions_agent, service_agent):
        self.coordinator_agent = coordinator_agent
        self.accounts_agent = accounts_agent
        self.transactions_agent = transactions_agent
        self.service_agent = service_agent

    async def router(self, state: AgentState) -> dict:
        return router_node(state, self.coordinator_agent)

    async def accounts(self, state: AgentState) -> dict:
        return await accounts_node(state, self.accounts_agent)

    async def transactions(self, state: AgentState) -> dict:
        return await transactions_node(state, self.transactions_agent)

    async def service(self, state: AgentState) -> dict:
        return await service_node(state, self.service_agent)

    def build(self):

        workflow = StateGraph(AgentState)

        workflow.add_node("router", self.router)
        workflow.add_node("accounts", self.accounts)
        workflow.add_node("transactions", self.transactions)
        workflow.add_node("service", self.service)
        workflow.add_node("clarification", clarification_node)

        workflow.add_edge(START, "router")

        workflow.add_conditional_edges(
            "router",
            routing_logic,
            {
                "accounts": "accounts",
                "transactions": "transactions",
                "service": "service",
                "clarification": "clarification",
            },
        )

        workflow.add_edge("accounts", END)
        workflow.add_edge("transactions", END)
        workflow.add_edge("service", END)
        workflow.add_edge("clarification", END)
        return workflow.compile()
