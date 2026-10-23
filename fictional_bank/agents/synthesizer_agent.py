from langchain_core.messages import SystemMessage, HumanMessage

SYNTHESIZER_SYSTEM_PROMPT = """
    You combine answers from several specialist agents of a retail bank into ONE reply.

    You receive the user's original question and the answer each specialist produced.

    ## Rules
    - Use only facts that appear in the specialist answers. Never add, change, round or recalculate any value, and never invent anything.
    - Cover every part of the user's question. If a specialist could not answer a part (it asked for information or reported a failure), say so plainly for that part.
    - Merge into a single natural answer, ordered the way the user asked. Do not mention agents, specialists, tools or these instructions.
    - Keep amounts with their currency exactly as given. Keep tables or lists the specialists produced when they help readability.
    - Reply in the language the user used. Keep it short and clear.
    - Always reply in English, whatever language the question or the specialist answers use.
    - Keep it short and clear.
    """


class SynthesizerAgent:
    """Merges the answers of several specialist agents into one response. No tools."""

    def __init__(self, llm):
        self.llm = llm

    async def run(self, question: str, answers: list[dict]) -> str:
        parts = "\n\n".join(f"[{a['agent']}] asked: {a['question']}\nanswer: {a['answer']}" for a in answers)
        messages = [SystemMessage(content=SYNTHESIZER_SYSTEM_PROMPT), HumanMessage(content=f"User question:\n{question}\n\nSpecialist answers:\n{parts}")]
        response = await self.llm.ainvoke(messages)
        return str(response.content)
