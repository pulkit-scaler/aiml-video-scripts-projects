"""Step 1: one model call, structured output.

Run:  python steps/step1_llm.py T-01
"""

import json
import os
import sys
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")  # this project's own .env
MODEL = os.getenv("MODEL") or "openai/gpt-oss-20b"

SYSTEM_PROMPT = """You triage support tickets for Northwind Cloud, a B2B SaaS company.
For each ticket, write a one-sentence summary, set urgency to high, medium or low,
and recommend the next action for the support team."""


# The exact shape we want back. The model is forced to fill in these fields.
class Triage(BaseModel):
    summary: str
    urgency: Literal["high", "medium", "low"]
    recommended_action: str


# The same shape as a JSON schema. In strict mode, Groq won't let the model answer in any other shape.
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


def main():
    tickets = json.loads((ROOT / "data" / "tickets.json").read_text())
    wanted = sys.argv[1] if len(sys.argv) > 1 else "T-01"
    ticket = next(t for t in tickets if t["id"] == wanted)

    client = Groq()  # reads GROQ_API_KEY
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Subject: {ticket['subject']}\n\n{ticket['body']}"},
        ],
        response_format={"type": "json_schema",
                         "json_schema": {"name": "triage", "strict": True, "schema": TRIAGE_SCHEMA}},
    )

    result = Triage.model_validate_json(response.choices[0].message.content)  # checked against our shape
    print(f"Ticket {ticket['id']}: {ticket['subject']}\n")
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
