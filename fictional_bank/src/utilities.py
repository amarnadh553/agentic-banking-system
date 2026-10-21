

def call_existing_tool(tool, **kwargs):
    """Call either a LangChain tool or its underlying Python function."""
    if hasattr(tool, "invoke"):
        return tool.invoke(kwargs)
    return tool(**kwargs)
