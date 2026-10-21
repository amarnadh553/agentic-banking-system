

def call_existing_tool(tool, **kwargs):
    """Call either a LangChain tool or its underlying Python function."""
    if hasattr(tool, "invoke"):
        return tool.invoke(kwargs)
    return tool(**kwargs)

def remove_newlines(text: str) -> str:
    """Removes all newline characters from the given string."""
    return text.replace("\n", "")