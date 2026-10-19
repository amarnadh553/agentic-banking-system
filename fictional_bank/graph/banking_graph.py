from langgraph.graph import StateGraph, START, END
from fictional_bank.graph.state import AgentState
from fictional_bank.graph.routing import router_node, accounts_node, transactions_node, service_node, clarification_node, routing_logic


class BuildGraph:

    def __init__(self, coordinator_agent, accounts_agent, transactions_agent, service_agent):
        self.coordinator_agent = coordinator_agent
        self.accounts_agent = accounts_agent
        self.transactions_agent = transactions_agent
        self.service_agent = service_agent

    def build(self):

        workflow = StateGraph(AgentState)

        ## Nodes
        workflow.add_node("router", lambda state:router_node(state, self.coordinator_agent))
        workflow.add_node("accounts", lambda state:accounts_node(state, self.accounts_agent))
        workflow.add_node("transactions", lambda state:transactions_node(state, self.transactions_agent))
        workflow.add_node("service", lambda state:service_node(state, self.service_agent))
        workflow.add_node("clarification", clarification_node)

        # Entry point
        workflow.add_edge(START, "router")

        # Conditional routing
        workflow.add_conditional_edges(
            "router",
            routing_logic,
            {
                "accounts": "accounts",
                "transactions": "transactions",
                "service": "service",
                "clarification": "clarification",
            }
        )
        # End nodes
        workflow.add_edge("accounts", END)
        workflow.add_edge("transactions", END)
        workflow.add_edge("service", END)
        workflow.add_edge("clarification", END)
        return workflow.compile()