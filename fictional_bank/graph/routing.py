from fictional_bank.graph.state import AgentState

def router_node(state:AgentState, coordinator_agent) -> dict:
    decision = coordinator_agent.run(state['question'])
    return {"selected_agent" : decision.agent, "reasoning" : decision.reasoning}

def accounts_node(state:AgentState, accounts_agent) -> dict:
    result = accounts_agent.run(state['question'])
    return {"response" : str(result.get("result", result))}

def transactions_node(state:AgentState, transactions_agent) -> dict:
    result = transactions_agent.run(state['question'])
    return {"response": str(result.get("result", result))}

def service_node(state:AgentState, service_agent) -> dict:
    result = service_agent.run(state['question'])
    return {"response": str(result.get("result", result))}

def clarification_node(state:AgentState) -> dict:
    return {"response": "Could you please clarify your banking question?"}

def routing_logic(state:AgentState):
    return state["selected_agent"]