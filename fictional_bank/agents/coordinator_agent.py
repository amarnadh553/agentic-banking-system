# from fictional_bank.agents import AccountsAgent, TransactionsAgent, ServiceAgent, RoutingGraph
# from fictional_bank.models.llm_model import initialize_llm
# from fictional_bank.config.config import config
# from fictional_bank.tools import ACCOUNTS_TOOLS, TRANSACTIONS_TOOLS, SERVICE_TOOLS



# llm = initialize_llm()
# accounts_agent = AccountsAgent(llm=llm, tools=ACCOUNTS_TOOLS, max_iterations=config.MAX_ITERATIONS)
# transactions_agent = TransactionsAgent(llm=llm, tools=TRANSACTIONS_TOOLS, max_iterations=config.MAX_ITERATIONS)
# service_agent = ServiceAgent(llm=llm, tools=SERVICE_TOOLS, max_iterations=config.MAX_ITERATIONS)



# # que = "Show me the email and name for customer C001 and tell his active status also if possible "
# # response = accounts_agent.run(que)
# # print("\n========== FINAL RESULT ==========")
# # print(response)

# # class AgentState()


# class CoOrdinatorAgent:
#     pass

from typing import Literal

from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

Route = Literal["accounts", "transactions", "service", "clarification"]


class RouteTask(BaseModel):
    agent: Route
    question: str = Field(
        description="Self-contained sub-question for this agent only. Repeat the customer ID and "
        "any dates or limits; never use pronouns such as 'his' or 'that'."
    )


class RouteDecision(BaseModel):
    tasks: list[RouteTask] = Field(
        description="One task per specialist needed (1 to 3). Use a single 'clarification' task "
        "only when nothing else applies."
    )
    reasoning: str = Field(description="Brief reason for the chosen route(s)")


class CoordinatorAgent:

    SYSTEM_PROMPT = """
        You are the Routing Agent for a retail bank assistant. You never answer the question.
        You split the user's message into tasks and give each task to the right specialist.

        ## Specialists
        - accounts: customer profile (name, email, status), a customer's list of accounts, balance of one account, total balance across accounts.
        - transactions: transaction history, recent transactions, transactions in a date range, only debits or credits, total spent or received.
        - service: service requests such as address change or card replacement, request status, pending requests, how many requests a customer has.
        - clarification: greetings, thanks, general chat, or anything outside the three areas (loans, transfers, card blocking, weather, ...), or a message too vague to act on.

        ## How to plan
        - Decide from meaning, not exact wording. Users write casually, with typos, in any language.
        - Return ONE task per specialist that is needed, at most three. If the message needs two or three specialists, return a task for each of them.
        - Each task's question must be self-contained: include the customer ID, dates, limits and any other detail, and keep only the part that specialist can answer. Replace words like "his", "her", "that account" with the actual ID or value from the message.
        - A customer's name, email, status or accounts always belong to accounts, even when the same message also asks about transactions or requests.
        - "Transactions" and "requests" are different things. R-prefixed IDs (R0001) are service request IDs.
        - A missing customer ID does not change the route; the specialist asks for it.
        - A vague message that is clearly about a customer ("tell me about C001") -> accounts.
        - Use "clarification" alone. Never combine it with other specialists.
        - Never invent route names.
        - Decide from meaning, not exact wording. Users write casually, with typos, in any language.
        - Always write each task question in English, even if the user wrote in another language.

        ## Examples
        - "How much is in C003's salary account" ->
          accounts: "How much is in C003's salary account"

        - "Show the three most recent transactions for customer C003 and his name" ->
          accounts: "What is the name of customer C003?"
          transactions: "Show the 3 most recent transactions for customer C003"

        - "C001 balance and recent transactions" ->
          accounts: "What is the total balance of customer C001?"
          transactions: "Show the most recent transactions for customer C001"

        - "Who is C002 and what has C002 raised" ->
          accounts: "Who is customer C002?"
          service: "What service requests has customer C002 raised?"
          
        - "Status of R0003 for C001" -> service: "What is the status of request R0003 for C001?"
        - "Hi, what can you do" -> clarification
        - "Transfer 500 to C002" -> clarification
        """

    def __init__(self, llm):
        self.router = llm.with_structured_output(RouteDecision)

    def _messages(self, question: str):
        return [SystemMessage(content=self.SYSTEM_PROMPT), HumanMessage(content=question)]

    def run(self, question: str) -> RouteDecision:
        return self.router.invoke(self._messages(question))

    async def arun(self, question: str) -> RouteDecision:
        """Async version: does not block the FastAPI event loop."""
        return await self.router.ainvoke(self._messages(question))
