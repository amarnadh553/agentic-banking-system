import logging
from typing import Optional


from fictional_bank.agents import AccountsAgent, TransactionsAgent, ServiceAgent, CoordinatorAgent
from fictional_bank.models.llm_model import initialize_llm
from fictional_bank.tools import ACCOUNTS_TOOLS, TRANSACTIONS_TOOLS, SERVICE_TOOLS
from fictional_bank.graph.banking_graph import BuildGraph
from fictional_bank.models.llm_model import LLMModelInitializer
from fictional_bank.config.config import Config
from fictional_bank.src.logutils import Logger

llm = initialize_llm()

class BankingApplication:

    def __init__(self, config:Config, logger: Optional[logging.Logger], **kwargs: dict):

        """
        Initializes the Banking ChatBot instance with a given configuration.

        Args:
            config (Config): The configuration object containing all necessary parameters.

        """

        self.config = config
        self.logger = logger if logger else Logger().get_logger()
        # self.llm = initialize_llm()
        self.llm_model_initializer = LLMModelInitializer(
            llm_model_name=self.config.LLM_MODEL_NAME,
            open_ai_api_key=self.config.OPENAI_API_KEY,
            temperature=self.config.TEMPERATURE,
            top_p=self.config.TOP_P,
            frequency_penalty=self.config.FREQUENCY_PENALTY,
            logger=self.logger

        )
        self.llm = self.llm_model_initializer.initialise_llm_model()

        # Initialize agents
        self.coordinator_agent = CoordinatorAgent(llm=self.llm)
        self.accounts_agent = AccountsAgent(llm=self.llm, tools=ACCOUNTS_TOOLS, max_iterations=self.config.MAX_ITERATIONS)
        self.transactions_agent = TransactionsAgent(llm=self.llm, tools=TRANSACTIONS_TOOLS, max_iterations=self.config.MAX_ITERATIONS)
        self.service_agent = ServiceAgent(llm=self.llm, tools=SERVICE_TOOLS, max_iterations=self.config.MAX_ITERATIONS)

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


app = BankingApplication(config=Config(), logger=Logger().get_logger())

# Run a banking question
result = app.run("Can you show the customer details for C001?")
print(result)
# Visualize and save the graph
# app.visualize_graph()

# Code end