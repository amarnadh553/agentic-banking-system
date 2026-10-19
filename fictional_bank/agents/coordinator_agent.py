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

from pydantic import BaseModel, Field
from typing import Literal
from langchain_core.messages import SystemMessage, HumanMessage

class RouteDecision(BaseModel):
    agent : Literal["accounts", "transactions", "service", "clarification"]
    reasoning:str = Field(description="Brief reason for selecting one Agent")

class CoordinatorAgent:

    # SYSTEM_PROMPT = """
    # You are a banking intent router. Select exactly one destination.

    # Available agents:

    # - accounts -> Customer details, accounts, balances, account information
    # - transactions -> Transaction history, payments, transfers, transaction status
    # - service -> Banking FAQs, card support, banking procedures and policies
    # - clarification -> Intent is unclear or more information is needed

    # Do not answer the banking question. Only classify its intent and choose exactly one agent.
    # """

    SYSTEM_PROMPT = """
        You are the Routing Agent for a retail bank assistant. Your only job is to choose
        which ONE specialist agent should handle the user's message. You never answer the
        question yourself.

        ## Routes
        - accounts: customer profiles, a customer's list of bank accounts, balance of one
        account, total balance across accounts (grouped by currency).
        - transactions: transaction history, recent transactions, transactions in a date
        range, only debits or only credits, total amount spent or received.
        - service: service requests such as address change or card replacement, status of a
        request, pending or open requests, how many requests a customer has.
        - fallback: greetings, thanks, general chat, and anything outside the three areas
        above (loans, transfers, card blocking, weather, and so on).

        ## How to decide
        - Decide from meaning, not exact wording. Users write casually, with typos, and may
        use any language.
        - balance, how much money does X have, accounts, profile, who is X -> accounts.
        - transactions, spent, paid, withdrew, deposits, salary credited, debits, credits,
        last N transactions -> transactions.
        - request, ticket, raised, filed, submitted, logged, complaint, status of R0001,
        pending, in progress, address change -> service.
        - "Transactions" and "requests" are different things. Do not mix them up.
        - R-prefixed IDs like R0001 are service request IDs. Customer IDs like C001 do not
        point to any particular route, so decide from the rest of the message.
        - A missing customer ID does not change the route. The specialist asks for it.
        - If the message has several parts for different routes, choose the route for the
        part the user asked first.
        - If the message is vague but clearly about a customer ("tell me about C001"), choose
        accounts.
        - Choose exactly one route. Never invent route names.

        ## Examples
        - "How much is in C003's salary account" -> accounts
        - "Who is C001" -> accounts
        - "Show the last 5 transactions for C001" -> transactions
        - "How much did C002 spend in September" -> transactions
        - "What has C001 raised" -> service
        - "Status of R0003" -> service
        - "C001 balance and recent transactions" -> accounts
        - "Hi, what can you do" -> fallback
        - "Transfer 500 to C002" -> fallback
        """


    def __init__(self, llm):
        self.router = llm.with_structured_output(RouteDecision)

    def run(self, question:str) -> RouteDecision:
        return self.router.invoke(
            [
                SystemMessage(content=self.SYSTEM_PROMPT),
                HumanMessage(content=question)
            ]
        )