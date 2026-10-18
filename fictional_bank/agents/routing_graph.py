from typing import Literal, TypedDict

from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END


# --------------------------------------------------
# State shared by every node in the graph
# --------------------------------------------------

class AgentState(TypedDict, total=False):
    question: str   # the user's message (input)
    route: str      # which node the router picked
    result: str     # final answer text (output)
    error: str      # set when routing itself fails


# --------------------------------------------------
# Router decision (structured output)
# --------------------------------------------------

class RouteDecision(BaseModel):
    reasoning: str = Field(description="One short sentence explaining the choice.")
    route: Literal["accounts", "transactions", "service", "fallback"] = Field(description="The single best node for this message.")


ROUTER_SYSTEM_PROMPT = """
    You are the Routing Agent for a retail bank assistant. Your only job is to choose
    which ONE specialist agent should handle the user's message. You never answer the
    question yourself.

    ## Routes
    - accounts: customer profiles, a customer's list of bank accounts, balance of one
    account, total balance across accounts (grouped by currency).
    - transactions: transaction history, recent transactions, transactions in a date
    range, only debits or only credits, total amount spent or received.
    - service: service requests such as address change or card replacement, status of a
    request, pending or open requests, how many requests a customer has.
    - fallback: greetings, thanks, general chat, and anything outside the three areas
    above (loans, transfers, card blocking, weather, and so on).

    ## How to decide
    - Decide from meaning, not exact wording. Users write casually, with typos, and may
    use any language.
    - balance, how much money does X have, accounts, profile, who is X -> accounts.
    - transactions, spent, paid, withdrew, deposits, salary credited, debits, credits,
    last N transactions -> transactions.
    - request, ticket, raised, filed, submitted, logged, complaint, status of R0001,
    pending, in progress, address change -> service.
    - "Transactions" and "requests" are different things. Do not mix them up.
    - R-prefixed IDs like R0001 are service request IDs. Customer IDs like C001 do not
    point to any particular route, so decide from the rest of the message.
    - A missing customer ID does not change the route. The specialist asks for it.
    - If the message has several parts for different routes, choose the route for the
    part the user asked first.
    - If the message is vague but clearly about a customer ("tell me about C001"), choose
    accounts.
    - Choose exactly one route. Never invent route names.

    ## Examples
    - "How much is in C003's salary account" -> accounts
    - "Who is C001" -> accounts
    - "Show the last 5 transactions for C001" -> transactions
    - "How much did C002 spend in September" -> transactions
    - "What has C001 raised" -> service
    - "Status of R0003" -> service
    - "C001 balance and recent transactions" -> accounts
    - "Hi, what can you do" -> fallback
    - "Transfer 500 to C002" -> fallback
    """

FALLBACK_MESSAGE = (
    "I can help with three things: customer profiles, accounts and balances; "
    "transactions; and service requests. Could you ask something about one of these, "
    "and include the customer ID?"
)

ROUTING_ERROR_MESSAGE = "Sorry, I could not work out how to handle that. Please try again."


# --------------------------------------------------
# Routing graph
# --------------------------------------------------

class RoutingGraph:
    """
    START -> router -> accounts | transactions | service | fallback -> END

    agents: {"accounts": agent, "transactions": agent, "service": agent}
    Each agent needs a .run(question) method returning {"result": ...} or {"error": ...}.
    """

    def __init__(self, llm, agents: dict):
        self.agents = agents
        self.router_llm = llm.with_structured_output(RouteDecision)
        self.graph = self._build_graph()

        print("\n========== INITIALIZING ROUTING GRAPH ==========")
        print(f"[DEBUG] Routable agents: {list(self.agents)}")
        print("[DEBUG] Routing graph compiled successfully.")

    # ---------------- Nodes ----------------

    def _router_node(self, state: AgentState) -> dict:
        print("\n========== ROUTER NODE ==========")
        print(f"[DEBUG] Question: {state['question']}")
        messages = [SystemMessage(content=ROUTER_SYSTEM_PROMPT), HumanMessage(content=state["question"])]
        try:
            decision = self.router_llm.invoke(messages)
        except Exception as e:
            print(f"[ERROR] Routing failed: {type(e).__name__}: {e}")
            return {"route": "fallback", "error": ROUTING_ERROR_MESSAGE}
        print(f"[DEBUG] Router reasoning: {decision.reasoning}")
        print(f"[DEBUG] Selected route: {decision.route}")
        return {"route": decision.route}

    def _make_agent_node(self, name: str, agent):
        def node(state: AgentState) -> dict:
            print(f"\n========== {name.upper()} NODE ==========")
            try:
                response = agent.run(state["question"])
            except Exception as e:
                print(f"[ERROR] {name} agent failed: {type(e).__name__}: {e}")
                return {"result": f"Sorry, the {name} agent failed: {type(e).__name__}: {e}"}
            return {"result": response.get("result") or f"Error: {response.get('error', 'no answer returned')}"}
        return node

    def _fallback_node(self, state: AgentState) -> dict:
        print("\n========== FALLBACK NODE ==========")
        return {"result": state.get("error") or FALLBACK_MESSAGE}

    # ---------------- Routing logic ----------------

    def _routing_logic(self, state: AgentState) -> str:
        route = state.get("route")
        return route if route in self.agents else "fallback"

    # ---------------- Graph wiring ----------------

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("router", self._router_node)
        for name, agent in self.agents.items():
            workflow.add_node(name, self._make_agent_node(name, agent))
        workflow.add_node("fallback", self._fallback_node)

        workflow.add_edge(START, "router")
        workflow.add_conditional_edges(
            "router",
            self._routing_logic,
            {**{name: name for name in self.agents}, "fallback": "fallback"},
        )

        for name in self.agents:
            workflow.add_edge(name, END)
        workflow.add_edge("fallback", END)

        return workflow.compile()

    # ---------------- Public API ----------------

    def run(self, question: str) -> dict:
        """Run one question through the graph. Returns the final state (question, route, result)."""
        return self.graph.invoke({"question": question})