"""Builds data/inbox.json: 80 messages from Northwind Cloud's finance inbox, each with its true label.

    python build_dataset.py

Seeded, so it always produces the same file. The mix mirrors a real inbox:
lots of routine mail, and a handful of rare messages that matter most.

    invoice            25   vendors billing us
    refund_request     20   customers asking for money back
    support_question   20   billing how-to questions
    contract_renewal   10   renewals and upgrades
    payment_dispute     5   chargebacks from a bank: rare, deadline-driven, expensive to miss
"""

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
rng = random.Random(7)

COMPANIES = ["Fairway Foods", "Brightline Logistics", "Kestrel Health", "Orchid Retail", "Summit Legal",
             "Bluefin Media", "Harbor Analytics", "Copperleaf Energy", "Northgate Schools", "Pioneer Freight",
             "Lumen Dental", "Redwood Insurance", "Atlas Hotels", "Quarry Labs", "Willow Pharma"]
VENDORS = ["CloudCore Hosting", "PrintPoint", "Datastream Ltd", "OfficeHub", "SecureMail", "Metric Ads",
           "TalentBridge Recruiting", "FiberNet Telecom"]
NAMES = ["Linda", "Raj", "Sofia", "Tom", "Aisha", "Daniel", "Mei", "Carlos", "Priya", "Jonas", "Fatima", "Owen"]
MONTHS = ["January", "February", "March", "April", "May", "June"]


def amount():
    return f"${rng.randint(4, 380) * 25:,}.00"


def invoice():
    v = rng.choice(VENDORS)
    return {
        "from": f"billing@{v.split()[0].lower()}.com",
        "subject": rng.choice([f"Invoice INV-{rng.randint(1000, 9999)} from {v}",
                               f"{v}: your {rng.choice(MONTHS)} invoice", f"Payment due: {v}"]),
        "body": rng.choice([
            f"Please find attached invoice INV-{rng.randint(1000, 9999)} for {amount()}, due within 30 days. Bank details are on the invoice.",
            f"Your {rng.choice(MONTHS)} statement from {v} is ready. Amount due: {amount()}. Payment terms are net 30.",
            f"Reminder: invoice INV-{rng.randint(1000, 9999)} for {amount()} is due on {rng.randint(1, 28)} {rng.choice(MONTHS)}. Thank you for your business.",
        ]),
    }


def refund_request():
    c, n = rng.choice(COMPANIES), rng.choice(NAMES)
    return {
        "from": f"{n.lower()}@{c.split()[0].lower()}.com",
        "subject": rng.choice(["Refund request", "Can we get our money back?", "Charged twice",
                               "Cancel and refund annual plan", "Refund for unused seats"]),
        "body": rng.choice([
            f"Hi, we were charged {amount()} twice this month. Could you refund the duplicate charge? Thanks, {n}, {c}",
            f"We cancelled within the first week but were still billed {amount()}. Please refund it. {n}",
            f"Hello, we bought the annual plan by mistake and would like a refund of {amount()}. Regards, {n} at {c}",
            f"We removed 10 seats last month. Can we get a refund for them? {n}, {c}",
        ]),
    }


def support_question():
    c, n = rng.choice(COMPANIES), rng.choice(NAMES)
    return {
        "from": f"{n.lower()}@{c.split()[0].lower()}.com",
        "subject": rng.choice(["Question about billing", "How do I update our card?", "VAT number on invoices",
                               "Where can I download invoices?", "Change billing contact"]),
        "body": rng.choice([
            f"Hi, how do I change the card we pay with? Our old one expires next month. {n}",
            f"Can you add our VAT number to future invoices? It's GB{rng.randint(100000000, 999999999)}. Thanks, {n}, {c}",
            f"Where in the app can I download past invoices for our accountant? {n}",
            f"Our finance contact has changed. Please send billing emails to accounts@{c.split()[0].lower()}.com from now on. {n}",
        ]),
    }


def contract_renewal():
    c, n = rng.choice(COMPANIES), rng.choice(NAMES)
    return {
        "from": f"{n.lower()}@{c.split()[0].lower()}.com",
        "subject": rng.choice(["Renewal coming up", "Upgrade to Enterprise", "Renewing for another year",
                               "Multi-year contract quote"]),
        "body": rng.choice([
            f"Our contract renews in {rng.choice(MONTHS)}. We'd like to add 20 seats and move to Enterprise. Can you send a quote? {n}, {c}",
            f"We're happy to renew for another year. Could you send the renewal order form? {n}",
            f"Can you quote us a three-year contract for {rng.randint(50, 400)} seats? {n} at {c}",
        ]),
    }


def payment_dispute():
    c = rng.choice(COMPANIES)
    bank = rng.choice(["Visa Dispute Resolution", "Mastercard Chargeback Team", "Stripe Disputes", "Amex Merchant Services"])
    return {
        "from": f"disputes@{bank.split()[0].lower()}.com",
        "subject": rng.choice([f"Chargeback notice: case {rng.randint(100000, 999999)}",
                               "Dispute opened on a card payment", "Action required: cardholder dispute"]),
        "body": rng.choice([
            f"A cardholder at {c} has disputed a charge of {amount()}, reason code 10.4 (fraud, card not present). The funds have been withdrawn from your balance. Submit evidence within 7 days or the dispute is closed in the cardholder's favour.",
            f"The cardholder says they asked for a refund that was never processed and has disputed {amount()} with their bank. Respond by {rng.randint(1, 28)} {rng.choice(MONTHS)} with proof of service, or the amount will be reversed permanently.",
            f"Notice of chargeback for {amount()} from {c}. Reason: product not received. You have 10 days to accept or challenge this dispute.",
        ]),
    }


MIX = [("invoice", invoice, 25), ("refund_request", refund_request, 20), ("support_question", support_question, 20),
       ("contract_renewal", contract_renewal, 10), ("payment_dispute", payment_dispute, 5)]


def build() -> list[dict]:
    messages = [{**make(), "label": label} for label, make, n in MIX for _ in range(n)]
    rng.shuffle(messages)
    return [{"id": f"M-{i:02d}", **m} for i, m in enumerate(messages, 1)]


if __name__ == "__main__":
    data = build()
    (ROOT / "data" / "inbox.json").write_text(json.dumps(data, indent=1))
    print(f"Wrote {len(data)} messages to data/inbox.json")
