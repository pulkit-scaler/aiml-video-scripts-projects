"""The finished support-ticket triage agent.

For each ticket it: summarises it, sets urgency (high / medium / low),
looks up company policy, posts to Slack if urgent, and saves a draft reply.

    from agent import triage
    result = triage(ticket)
"""

import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel
from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")  # this project's own .env


def get_client():
    """A Groq client. Reads GROQ_API_KEY from the environment or .env.
    max_retries=0: complete() below handles rate limits itself, waiting exactly as long as Groq asks."""
    return Groq(max_retries=0)


def wait_seconds(err) -> float:
    """How long Groq asks us to wait after a rate-limit error ("try again in 1m2.5s")."""
    header = err.response.headers.get("retry-after") if getattr(err, "response", None) is not None else None
    if header:
        return float(header)
    match = re.search(r"try again in (?:(\d+)m)?([\d.]+)s", str(err))
    return int(match.group(1) or 0) * 60 + float(match.group(2)) if match else 5.0


def complete(client, max_wait: float = 300, **kwargs):
    """One chat completion. On Groq's free-tier rate limit, wait as long as Groq asks and try again,
    for up to max_wait seconds in total. Ends with a plain message, never a traceback."""
    from groq import RateLimitError
    waited = 0.0
    while True:
        try:
            return client.chat.completions.create(**kwargs)
        except RateLimitError as err:
            seconds = wait_seconds(err)
            if seconds > 120:  # the daily budget is used up: waiting a minute won't help
                raise SystemExit(f"Groq's daily limit for {kwargs.get('model')} is used up. Try again in "
                                 f"{seconds / 60:.0f} minutes, or set MODEL in .env to another model.") from err
            if waited + seconds > max_wait:
                raise SystemExit("Groq kept rate-limiting this key for 5 minutes. Make sure nothing else "
                                 "is using the same API key, wait a minute, and run again.") from err
            if seconds >= 3:
                print(f"  (Groq rate limit: waiting {seconds:.0f}s)", file=sys.stderr)
            time.sleep(seconds + 0.5)
            waited += seconds + 0.5


MODEL = os.getenv("MODEL") or "openai/gpt-oss-20b"
# gpt-oss thinks before it answers. "low" keeps that short, so calls stay fast and cheap.
REASONING = {"reasoning_effort": "low"} if MODEL.startswith("openai/gpt-oss") else {}
OUTBOX = Path(os.getenv("OUTBOX_DIR") or ROOT / "outbox")


# ---------------------------------------------------------------------------
# 1. The prompts. v1 is our first draft; v2 is the fix found by the eval.
# ---------------------------------------------------------------------------

PROMPT_V1 = """You triage customer support tickets for Northwind Cloud, a B2B SaaS company.
For each ticket, write a one-sentence summary, set urgency to high, medium or low,
and recommend the next action for the support team.
Set urgency based on how upset the customer sounds: angry, frustrated or
threatening customers are high; calm and polite customers are low or medium."""

PROMPT_V2 = """You triage customer support tickets for Northwind Cloud, a B2B SaaS company.
For each ticket, write a one-sentence summary, set urgency to high, medium or low,
and recommend the next action for the support team.
Judge urgency by business impact and deadlines, not by tone.
- high: an outage, a whole team or many customers blocked, a security risk, data loss, or a deadline within a day.
- medium: one user or one feature blocked, or a billing problem such as a wrong charge, a double charge or a refund.
- low: questions, pricing or sales requests, feature requests, cosmetic issues and feedback, however angry the customer is."""

PROMPTS = {"v1": PROMPT_V1, "v2": PROMPT_V2}

# Extra instructions for the full agent (the part that uses tools).
AGENT_INSTRUCTIONS = """
You have tools. For every ticket:
1. Call lookup_policy to find the relevant company policy.
2. If urgency is high, call post_to_slack with a one-line alert for the on-call team, in this form:
   "HIGH urgency: <ticket id>, <customer>: <the problem and any deadline>".
3. Call save_draft_reply with a short, warm reply to the customer that follows the policy.
   It is a draft that a support agent will check before sending, so never claim that anything
   has already been verified, unlocked, fixed or sent. Say what happens next, as the policy sets out.
   Sign it "Northwind Cloud Support", with no placeholders such as [Your Name].
Then give your final triage."""


class Triage(BaseModel):
    """The structured answer we want back for every ticket."""
    summary: str
    urgency: Literal["high", "medium", "low"]
    recommended_action: str


# The same shape as a JSON schema, so Groq can force the model to follow it (strict mode).
TRIAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "urgency": {"type": "string", "enum": ["high", "medium", "low"]},
        "recommended_action": {"type": "string"},
    },
    "required": ["summary", "urgency", "recommended_action"],
    "additionalProperties": False,
}


def ticket_text(ticket: dict) -> str:
    return f"From: {ticket['from']}\nSubject: {ticket['subject']}\n\n{ticket['body']}"


# ---------------------------------------------------------------------------
# 2. Retrieval (RAG): split the policy into sections and search with BM25.
# ---------------------------------------------------------------------------

def load_chunks(path=ROOT / "data" / "refund_policy.md") -> list[str]:
    """One chunk per '## ' section, so each chunk is a complete policy rule."""
    text = Path(path).read_text()
    sections = re.split(r"\n(?=## )", text)
    return [s.strip() for s in sections if s.startswith("## ")]


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


CHUNKS = load_chunks()
INDEX = BM25Okapi([tokenize(c) for c in CHUNKS])


def search_policy(query: str, k: int = 2) -> list[str]:
    scores = INDEX.get_scores(tokenize(query))
    best = sorted(range(len(CHUNKS)), key=lambda i: scores[i], reverse=True)
    return [CHUNKS[i] for i in best[:k]]


# ---------------------------------------------------------------------------
# 3. The three tools: plain Python functions the model can ask us to run.
# ---------------------------------------------------------------------------

def lookup_policy(query: str) -> str:
    return "\n\n---\n\n".join(search_policy(query))


def post_to_slack(message: str) -> str:
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if webhook:
        req = urllib.request.Request(
            webhook,
            data=json.dumps({"text": message}).encode(),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
        return "Posted to Slack."
    # No webhook configured: print it and keep a log, so the demo never breaks.
    print(f"[SLACK] {message}")
    OUTBOX.mkdir(parents=True, exist_ok=True)
    with open(OUTBOX / "slack.log", "a") as f:
        f.write(message + "\n")
    return "Posted to Slack (logged to outbox/slack.log)."


def save_draft_reply(ticket_id: str, reply: str) -> str:
    drafts = OUTBOX / "drafts"
    drafts.mkdir(parents=True, exist_ok=True)
    path = drafts / f"{ticket_id}.md"
    path.write_text(reply)
    return f"Draft saved to {path}."


TOOL_FUNCTIONS = {
    "lookup_policy": lookup_policy,
    "post_to_slack": post_to_slack,
    "save_draft_reply": save_draft_reply,
}

# What the model sees. The descriptions are what make it pick the right tool.
TOOLS = [
    {"type": "function", "function": {
        "name": "lookup_policy",
        "description": "Search the Northwind Cloud support and refund policy. "
                       "Use this before deciding what to do or what to promise the customer.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "What to look up, e.g. 'refund annual plan'"}},
            "required": ["query"],
        },
    }},
    {"type": "function", "function": {
        "name": "post_to_slack",
        "description": "Alert the on-call support team in Slack. "
                       "Only use this for HIGH urgency tickets.",
        "parameters": {
            "type": "object",
            "properties": {"message": {"type": "string",
                                       "description": "One-line alert: 'HIGH urgency: <ticket id>, <customer>: <problem>'"}},
            "required": ["message"],
        },
    }},
    {"type": "function", "function": {
        "name": "save_draft_reply",
        "description": "Save a draft reply to the customer for a human agent to review and send. "
                       "Use this for every ticket.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string"},
                "reply": {"type": "string", "description": "The full reply email to the customer"},
            },
            "required": ["ticket_id", "reply"],
        },
    }},
]


# ---------------------------------------------------------------------------
# 4. Classify only (used by the eval) and the full agent loop.
# ---------------------------------------------------------------------------

def json_format() -> dict:
    """Ask for JSON that must match TRIAGE_SCHEMA."""
    return {"type": "json_schema",
            "json_schema": {"name": "triage", "strict": True, "schema": TRIAGE_SCHEMA}}


def classify(ticket: dict, system_prompt: str = PROMPT_V2) -> dict:
    """One model call, structured output, no tools. Fast; used by the eval."""
    response = complete(
        get_client(),
        model=MODEL,
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": ticket_text(ticket)}],
        response_format=json_format(),
        temperature=0,  # same ticket, same answer: the eval must be repeatable
        **REASONING,
    )
    return Triage.model_validate_json(response.choices[0].message.content).model_dump()


def triage(ticket: dict, system_prompt: str = PROMPT_V2, max_rounds: int = 8) -> dict:
    """The full agent: think, call tools, repeat until done, return the triage."""
    client = get_client()
    messages = [
        {"role": "system", "content": system_prompt + AGENT_INSTRUCTIONS},
        {"role": "user", "content": f"Ticket {ticket['id']}\n{ticket_text(ticket)}"},
    ]
    actions = []

    for _ in range(max_rounds):
        response = complete(client, model=MODEL, messages=messages, tools=TOOLS, **REASONING)
        message = response.choices[0].message
        if not message.tool_calls:
            break  # the model is done calling tools

        # Run every tool the model asked for, then hand the results back.
        messages.append({"role": "assistant", "content": message.content or "", "tool_calls": [
            {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
            for c in message.tool_calls]})
        for call in message.tool_calls:
            args = json.loads(call.function.arguments)
            print(f"  -> {call.function.name}({json.dumps(args, ensure_ascii=False)[:120]})")
            output = TOOL_FUNCTIONS[call.function.name](**args)
            actions.append(call.function.name)
            messages.append({"role": "tool", "tool_call_id": call.id, "name": call.function.name, "content": output})

    # One last call, without tools, for the final triage in our exact shape.
    # (Groq can't do tools and structured output in the same request.)
    messages.append({"role": "assistant", "content": message.content or ""})
    messages.append({"role": "user", "content": "Now give your final triage for this ticket."})
    final = complete(client, model=MODEL, messages=messages, response_format=json_format(), **REASONING)
    result = Triage.model_validate_json(final.choices[0].message.content).model_dump()
    return {"ticket_id": ticket["id"], **result, "actions_taken": actions}

if __name__ == "__main__":
    # python agent.py T-07                      a ticket from data/tickets.json
    # python agent.py data/fresh_ticket.json    any ticket saved as a JSON file
    wanted = sys.argv[1] if len(sys.argv) > 1 else "T-07"
    if wanted.endswith(".json"):
        ticket = json.loads(Path(wanted).read_text())
    else:
        tickets = json.loads((ROOT / "data" / "tickets.json").read_text())
        ticket = next(t for t in tickets if t["id"] == wanted)
    # ensure_ascii=False shows characters such as narrow spaces as they are, not as \u202f codes.
    print(json.dumps(triage(ticket), indent=2, ensure_ascii=False))
