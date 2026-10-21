from fictional_bank.graph.state import AgentState

def router_node(state: AgentState, coordinator_agent) -> dict:
    """Route the question using the synchronous coordinator."""
    decision = coordinator_agent.run(state["question"])
    return {"selected_agent": decision.agent, "reasoning": decision.reasoning,}

async def accounts_node(state: AgentState, accounts_agent) -> dict:
    result = await accounts_agent.run(state["question"])
    return {"response": str(result.get("result", result))}

async def transactions_node(state: AgentState, transactions_agent) -> dict:
    result = await transactions_agent.run(state["question"])
    return {"response": str(result.get("result", result))}

async def service_node(state: AgentState, service_agent) -> dict:
    result = await service_agent.run(state["question"])
    return {"response": str(result.get("result", result))}

def clarification_node(state: AgentState) -> dict:
    return {"response": "Could you please clarify your banking question?"}

def routing_logic(state: AgentState) -> str:
    selected_agent = state.get("selected_agent", "").strip().lower()
    valid_routes = {"accounts", "transactions", "service", "clarification"}
    if selected_agent not in valid_routes:
        return "clarification"
    return selected_agent
