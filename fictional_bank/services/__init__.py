# Standard library

# Local imports
from fictional_bank.src import Logger
from fictional_bank.config import Config
from fictional_bank.graph import BuildGraph
from fictional_bank.models.llm_model import create_llm
from fictional_bank.tools import ACCOUNTS_TOOLS, TRANSACTIONS_TOOLS, SERVICE_TOOLS
from fictional_bank.agents import AccountsAgent, TransactionsAgent, ServiceAgent, CoordinatorAgent, SynthesizerAgent


class FictionalBankApplication:

    def __init__(self, config: Config, logger, accounts_tools, transactions_tools, service_tools):
        self.config = config
        self.logger = logger or Logger().get_logger()
        self.llm = create_llm(self.config, self.logger)

        account_tool_list = (list(accounts_tools) if accounts_tools is not None else ACCOUNTS_TOOLS)
        transaction_tool_list = (list(transactions_tools) if transactions_tools is not None else TRANSACTIONS_TOOLS)
        service_tool_list = (list(service_tools) if service_tools is not None else SERVICE_TOOLS)

        ## Agents with with llm and tools
        self.coordinator_agent = CoordinatorAgent(llm=self.llm)
        self.synthesizer_agent = SynthesizerAgent(llm=self.llm)
        self.accounts_agent = AccountsAgent(llm=self.llm, tools=account_tool_list, max_iterations=self.config.MAX_ITERATIONS)
        self.transactions_agent = TransactionsAgent(llm=self.llm, tools=transaction_tool_list, max_iterations=self.config.MAX_ITERATIONS)
        self.service_agent = ServiceAgent(llm=self.llm, tools=service_tool_list, max_iterations=self.config.MAX_ITERATIONS)

        ## Building Grpha using LangGraph
        self.banking_graph = BuildGraph(coordinator_agent=self.coordinator_agent, accounts_agent=self.accounts_agent, transactions_agent=self.transactions_agent, service_agent=self.service_agent, synthesizer_agent=self.synthesizer_agent)
        self.graph = self.banking_graph.build()

    async def run(self, question: str) -> dict:
        result = await self.graph.ainvoke(
            {
                "question": question,
                "selected_agent": "",
                "reasoning": "",
                "tasks": [],
                "answers": [],
                "response": "",
            }
        )
        print("Selected agent:", result.get("selected_agent", ""))
        print("Reasoning:", result.get("reasoning", ""))
        print("Response:", result.get("response", ""))
        return result

    def visualize_graph(self, output_path: str = "banking_graph.png"):
        from IPython.display import Image, display
        png_data = self.graph.get_graph().draw_mermaid_png()
        display(Image(png_data))
        with open(output_path, "wb") as file:
            file.write(png_data)
        print(f"Graph saved as {output_path}")
