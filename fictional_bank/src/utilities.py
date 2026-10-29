

def call_existing_tool(tool, **kwargs):
    """Call either a LangChain tool or its underlying Python function."""
    if hasattr(tool, "invoke"):
        return tool.invoke(kwargs)
    return tool(**kwargs)

def remove_newlines(text: str) -> str:
    """Removes all newline characters from the given string."""
    return text.replace("\n", "")

def generate_graph(banking_app, output_path="banking_graph.png"):
    png_data = banking_app.graph.get_graph().draw_mermaid_png()
    with open(output_path, "wb") as file:
        file.write(png_data)
    return output_path

def get_selected_agents(result: dict, question: str) -> list[dict]:
    """The agents the router picked, each with the sub-question it was given."""
    tasks = result.get("tasks") or [{"agent": "clarification", "question": question}]
    return [{"agent": task["agent"], "question": task["question"]} for task in tasks]

def get_selected_tools(result: dict) -> list[dict]:
    """Every tool the agents called, in order, one dict per call."""
    return [{"agent": agent, "tool": call["name"], "args": call["args"]} for agent, calls in (result.get("tool_calls") or {}).items() for call in calls]
