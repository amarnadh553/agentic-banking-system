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

    def run(self, question):

        print(f"\n========== RUNNING {self.__class__.__name__} ==========")
        print(f"[DEBUG] Question: {question}")

        messages = [SystemMessage(content=self.system_prompt), HumanMessage(content=question)]
        for iteration in range(self.max_iterations):
            print(f"\n========== ITERATION {iteration + 1} ==========")
            print("[DEBUG] Sending messages to LLM...")
            try:
                response = self.llm_with_tools.invoke(messages)
            except Exception as e:
                print(f"[ERROR] LLM invocation failed: "f"{type(e).__name__}: {e}")
                return {"error": str(e)}
            messages.append(response)
            print("[DEBUG] LLM response received.")
            print(f"[DEBUG] Response content: {response.content}")
            print(f"[DEBUG] Tool calls: {response.tool_calls}")
            # Return the final answer
            if not response.tool_calls:
                print("[DEBUG] Final response received.")
                return {"result": response.content}
            # Execute each requested tool
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                print("\n========== TOOL EXECUTION ==========")
                print(f"[DEBUG] Tool name: {tool_name}")
                print(f"[DEBUG] Tool arguments: {tool_args}")
                if tool_name not in self.tool_map:
                    print(f"[ERROR] Unknown tool: {tool_name}")
                    result = {"error": f"Unknown tool: {tool_name}"}
                else:
                    try:
                        result = self.tool_map[tool_name].invoke(tool_args)
                        print("[DEBUG] Tool executed successfully.")
                        print(f"[DEBUG] Tool result: {result}")
                    except Exception as e:
                        print(f"[ERROR] Tool failed: "f"{type(e).__name__}: {e}")
                        result = {"error": (f"{type(e).__name__}: {str(e)}")}
                # Return the tool result to the LLM
                messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
                print("[DEBUG] Tool result added to conversation.")
        print("[WARNING] Maximum iterations reached.")
        return {"result": "Maximum tool-call iterations reached."}