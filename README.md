`npx @modelcontextprotocol/inspector python main.py`
{
  "question": "Show C003’s name, last 3 transactions and pending requests",
  "visualize_graph": true
}

Suggested order

`Agent Evaluation Suite (next).` You already have the golden dataset of 142 questions and a verifier for the tools. What’s missing is a runner that sends each question to your API and scores the route, the tool calls and the facts in the answer. It tells you whether any later change (a prompt edit, the multi-route router, a new model) made things better or worse. It also gives you results to quote in the article.
`Session Store.` The agents only see the current message, so a follow-up such as “and his pending requests?” fails. This needs a conversation ID in the API and history passed to the router.
`Observability and Cost Tracker.` Log each request’s route, tool calls, latency and token cost. These are small additions and good for the article.
`PII Redaction.` Mask emails and other personal data in logs and in what is sent to the LLM.
`Authentication and Authorisation.` This is the most important security piece. Today any caller can ask about any customer_id. Authorisation should limit a logged-in customer to their own data. Simple versions are an API key or JWT.
`Edge Layer`. This is infrastructure (gateway, rate limiting). A basic rate limit in FastAPI is enough for a portfolio project.