"""The finance-inbox agent from Video 10: read a message, label it, route it.

v1 is what a builder writes after testing on five hand-picked messages.
v2 is the fix found by looking at the errors, category by category.
"""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from demokit import llm

ROOT = Path(__file__).resolve().parent

INBOX = json.loads((ROOT / "data" / "inbox.json").read_text())

LABELS_V1 = {
    "invoice": "a vendor is billing Northwind Cloud",
    "refund_request": "someone wants money back",
    "support_question": "a how-to question about billing or the account",
    "contract_renewal": "a renewal, upgrade or new contract quote",
}

# The fix: the label set was built from five easy examples, so it had no place for a
# chargeback. The model filed them as refunds, and nobody answered the bank in time.
LABELS_V2 = {
    "invoice": "a vendor is billing Northwind Cloud",
    "refund_request": "a customer asks US directly for money back",
    "support_question": "a how-to question about billing or the account",
    "contract_renewal": "a renewal, upgrade or new contract quote",
    "payment_dispute": "a bank, card network or payment provider reports a chargeback or disputed "
                       "card payment, usually with a case number and a deadline to respond",
}

ROUTES = {"invoice": "Accounts payable", "refund_request": "Support (refunds)",
          "support_question": "Support", "contract_renewal": "Sales",
          "payment_dispute": "Finance lead, respond before the deadline"}

VERSIONS = {"v1": LABELS_V1, "v2": LABELS_V2}


def system_prompt(labels: dict) -> str:
    lines = "\n".join(f"- {k}: {v}" for k, v in labels.items())
    return f"""You sort messages in Northwind Cloud's finance inbox.
Pick exactly one label:
{lines}"""


def schema(labels: dict) -> dict:
    return {"type": "object",
            "properties": {"label": {"type": "string", "enum": list(labels)},
                           "reason": {"type": "string"}},
            "required": ["label", "reason"],
            "additionalProperties": False}


def message_text(m: dict) -> str:
    return f"From: {m['from']}\nSubject: {m['subject']}\n\n{m['body']}"


def classify(message: dict, version: str = "v2", fresh: bool = False) -> dict:
    labels = VERSIONS[version]
    out = llm.generate_json(message_text(message), schema(labels), system_prompt(labels), fresh=fresh)
    return {"id": message["id"], "truth": message["label"], "pred": out["label"], "reason": out["reason"],
            "passed": out["label"] == message["label"]}


def classify_all(messages: list[dict], version: str = "v2", fresh: bool = False) -> list[dict]:
    with ThreadPoolExecutor(max_workers=3) as pool:
        return list(pool.map(lambda m: classify(m, version, fresh), messages))


def handpicked() -> list[dict]:
    """Beat 1's five messages: the first clean example of each common type, plus one more invoice."""
    picks = []
    for label in ["invoice", "refund_request", "support_question", "contract_renewal", "invoice"]:
        picks.append(next(m for m in INBOX if m["label"] == label and m not in picks))
    return picks
