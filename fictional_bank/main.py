from fictional_bank.agents import AccountsAgent, TransactionsAgent, ServiceAgent, CoordinatorAgent
from fictional_bank.models.llm_model import initialize_llm
from fictional_bank.config.config import config
from fictional_bank.tools import ACCOUNTS_TOOLS, TRANSACTIONS_TOOLS, SERVICE_TOOLS
from fictional_bank.graph.banking_graph import BuildGraph
from fictional_bank.models.llm_model import LLMModelInitializer

llm = initialize_llm()

class BankingApplication:

    def __init__(self):
        self.llm = initialize_llm()

        # self.llmModelInstance = llmModelInstance
        # llmModelInitializer = self.llmModelInstance
        # self.llm_model_instance = llmModelInitializer.initialise_llm_model()

        # Initialize agents
        self.coordinator_agent = CoordinatorAgent(llm=self.llm)
        self.accounts_agent = AccountsAgent(llm=self.llm, tools=ACCOUNTS_TOOLS, max_iterations=config.MAX_ITERATIONS)
        self.transactions_agent = TransactionsAgent(llm=self.llm, tools=TRANSACTIONS_TOOLS, max_iterations=config.MAX_ITERATIONS)
        self.service_agent = ServiceAgent(llm=self.llm, tools=SERVICE_TOOLS, max_iterations=config.MAX_ITERATIONS,)

        # Build and compile graph
        self.banking_graph = BuildGraph(coordinator_agent=self.coordinator_agent, accounts_agent=self.accounts_agent, transactions_agent=self.transactions_agent, service_agent=self.service_agent,)
        self.graph = self.banking_graph.build()

    def run(self, question: str) -> dict:
        """Execute the banking graph for a given question."""

        result = self.graph.invoke({
            "question": question,
            "selected_agent": "",
            "reasoning": "",
            "response": "",
        })

        print("Selected agent:", result["selected_agent"])
        print("Reasoning:", result["reasoning"])
        print("Response:", result["response"])
        return result

    def visualize_graph(self, output_path: str = "banking_graph.png"):
        """Display and save the graph visualization."""
        from IPython.display import Image, display
        png_data = self.graph.get_graph().draw_mermaid_png()
        display(Image(png_data))
        with open(output_path, "wb") as file:
            file.write(png_data)
        print(f"Graph saved as {output_path}")


app = BankingApplication()

# Run a banking question
result = app.run("Can you show the customer details for C001?")

# Visualize and save the graph
app.visualize_graph()