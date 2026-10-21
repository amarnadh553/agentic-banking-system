from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

class BaseAgent:

    def __init__(self, llm, tools, system_prompt, max_iterations):
        self.llm = llm
        self.tools = tools
        self.llm_with_tools = llm.bind_tools(self.tools)
        self.max_iterations = max_iterations
        self.system_prompt = system_prompt
        self.tool_map = {tool.name: tool for tool in self.tools}

        print("\n========== INITIALIZING AGENT ==========")
        print(f"[DEBUG] Agent: {self.__class__.__name__}")
        print("[DEBUG] Registered tools:")

        for name in self.tool_map:
            print(f" - {name}")

        print("[DEBUG] Agent initialized successfully.")

    async def run(self, question: str) -> dict:
        messages = [SystemMessage(content=self.system_prompt), HumanMessage(content=question)]
        for iteration in range(self.max_iterations):
            response = await self.llm_with_tools.ainvoke(messages)
            messages.append(response)
            if not response.tool_calls:
                return {"result": response.content}
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                if tool_name not in self.tool_map:
                    result = {"error": f"Unknown tool: {tool_name}"}
                else:
                    try:
                        result = await self.tool_map[tool_name].ainvoke(tool_args)
                    except Exception as exc:
                        result = {"error": f"{type(exc).__name__}: {exc}"}
                messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
        return {"result": "Maximum tool-call iterations reached."}