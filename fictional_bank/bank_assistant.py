# from fictional_bank.agents import AccountsAgent, TransactionsAgent, ServiceAgent, RoutingGraph
# from fictional_bank.models.llm_model import initialize_llm
# from fictional_bank.config.config import config
# from fictional_bank.tools import ACCOUNTS_TOOLS, TRANSACTIONS_TOOLS, SERVICE_TOOLS


# class BankAssistant:
#     """Builds the LLM, the three specialist agents and the routing graph, and answers questions."""

#     def __init__(self, max_iterations=None):
#         self.max_iterations = config.MAX_ITERATIONS if max_iterations is None else max_iterations
#         self.llm = initialize_llm()
#         # Specialist agents
#         self.accounts_agent = AccountsAgent(llm=self.llm, tools=ACCOUNTS_TOOLS, max_iterations=self.max_iterations)
#         self.transactions_agent = TransactionsAgent(llm=self.llm, tools=TRANSACTIONS_TOOLS, max_iterations=self.max_iterations)
#         self.service_agent = ServiceAgent(llm=self.llm, tools=SERVICE_TOOLS, max_iterations=self.max_iterations)
#         # Router that sends each question to the right agent
#         self.routing_graph = RoutingGraph(
#             llm=self.llm,
#             agents={
#                 "accounts": self.accounts_agent,
#                 "transactions": self.transactions_agent,
#                 "service": self.service_agent,
#             },
#         )

#     def ask(self, question: str) -> dict:
#         """Answer one question. Returns the final state with 'route' and 'result'."""
#         return self.routing_graph.run(question)

#     def ask_and_print(self, question: str) -> dict:
#         state = self.ask(question)
#         print("\n========== FINAL RESULT ==========")
#         print(f"Question:  {question}")
#         print(f"Routed to: {state['route']}")
#         print(state["result"])
#         return state

#     def run_questions(self, questions: list[str]) -> list[dict]:
#         return [self.ask_and_print(question) for question in questions]