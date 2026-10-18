from fictional_bank.bank_assistant import BankAssistant

QUESTIONS = [
    "How much is in C003's salary account",
    "Show the last 5 transactions for customer C001",
    "What has C001 raised",
    "Hi, what can you do",
]

if __name__ == "__main__":
    assistant = BankAssistant()
    assistant.run_questions(QUESTIONS)