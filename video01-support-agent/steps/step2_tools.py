"""Step 2: give the model tools and let it decide which ones to call.

Run:  python steps/step2_tools.py T-02

Try this on camera: change the post_to_slack description below to
"Alert the team in Slack. Use this for EVERY ticket." and run a low-urgency
ticket (T-03). The model now posts to Slack. The description drives the choice.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so we can import agent.py
from agent import post_to_slack, save_draft_reply

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")  # this project's own .env
MODEL = os.getenv("MODEL") or "openai/gpt-oss-20b"


def lookup_policy(query: str) -> str:
    # For now: hand back the WHOLE policy. Step 3 replaces this with search.
    return (ROOT / "data" / "refund_policy.md").read_text()


TOOL_FUNCTIONS = {
    "lookup_policy": lookup_policy,
    "post_to_slack": post_to_slack,
    "save_draft_reply": save_draft_reply,
}

# The model only ever sees the name, the description and the inputs.
TOOLS = [
    {"type": "function", "function": {
        "name": "lookup_policy",
        "description": "Search the Northwind Cloud support and refund policy. "
                       "Use this before deciding what to do or what to promise the customer.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    }},
    {"type": "function", "function": {
        "name": "post_to_slack",
        "description": "Alert the on-call support team in Slack. Only use this for HIGH urgency tickets.",
        "parameters": {"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]},
    }},
    {"type": "function", "function": {
        "name": "save_draft_reply",
        "description": "Save a draft reply to the customer for a human to review. Use this for every ticket.",
        "parameters": {"type": "object",
                       "properties": {"ticket_id": {"type": "string"}, "reply": {"type": "string"}},
                       "required": ["ticket_id", "reply"]},
    }},
]

SYSTEM_PROMPT = """You triage support tickets for Northwind Cloud, a B2B SaaS company.
First check the policy. Then decide the urgency (high, medium or low) and take the right
actions with your tools. Finish with one short plain-text paragraph, no markdown, that
says only what your tools actually did."""


def main():
    tickets = json.loads((ROOT / "data" / "tickets.json").read_text())
    wanted = sys.argv[1] if len(sys.argv) > 1 else "T-02"
    ticket = next(t for t in tickets if t["id"] == wanted)
    print(f"Ticket {ticket['id']}: {ticket['subject']}\n")

    client = Groq(max_retries=6)  # reads GROQ_API_KEY; waits and retries if rate-limited
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Ticket {ticket['id']}\nSubject: {ticket['subject']}\n\n{ticket['body']}"},
    ]

    # The agent loop: ask the model, run the tools it picks, repeat until it stops.
    for _ in range(8):
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        message = response.choices[0].message
        if not message.tool_calls:
            break

        messages.append({"role": "assistant", "content": message.content or "", "tool_calls": [
            {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
            for c in message.tool_calls]})
        for call in message.tool_calls:
            args = json.loads(call.function.arguments)
            print(f"MODEL CALLS: {call.function.name}({json.dumps(args, ensure_ascii=False)[:100]}...)")
            output = TOOL_FUNCTIONS[call.function.name](**args)
            messages.append({"role": "tool", "tool_call_id": call.id, "name": call.function.name, "content": output})

    print("\nFINAL ANSWER:\n" + (message.content or ""))


if __name__ == "__main__":
    main()
