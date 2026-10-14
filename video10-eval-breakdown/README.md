# Video 10: 95% accurate and still broken

The demo for "2:05 The demo". A finance-inbox agent for Northwind Cloud labels every incoming
message and routes it. On five hand-picked messages it's perfect. On the full inbox the average
still looks great. Split by message type, one rare type fails every time, and it's the expensive
one: chargebacks from the bank, with a deadline.

The shooting script for this video is [SCRIPT.md](SCRIPT.md).

## Setup

This folder is self-contained: its own code, data, requirements, `.env` and tests. Python 3.12 or newer.

```bash
cd video10-eval-breakdown
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in GROQ_API_KEY
pytest                        # runs with no API key
```

## What's here

```
classifier.py         the agent: v1 label set, v2 label set, classify one or all messages
demo.py               one command per beat
build_dataset.py      regenerates data/inbox.json (seeded, always the same 80 messages)
data/inbox.json       80 messages with true labels: 25 invoices, 20 refund requests,
                      20 billing questions, 10 renewals, 5 payment disputes
demokit/              this demo's toolkit: Groq calls + replay cache, scoring, console tables
tests/                runs with no API key
SCRIPT.md             the shooting script
```

## The beats

| Beat | Command | What appears | Script line |
|---|---|---|---|
| 1 | `python demo.py beat1` | 5 hand-picked messages, 5/5 PASS | "Five out of five. Looks great. Ship it, right?" |
| 2 | `python demo.py beat2` | All 80 messages: 75/80 = 93.8% | "Bigger test. Still `[FILL: real accuracy]`." Use the number printed here. |
| 3 | `python demo.py beat3` | Accuracy per message type, worst first. `payment_dispute 0/5 0%` at the top | "Split it by type. This category? It fails nearly every time." |
| 4 | `python demo.py beat4` | The errors (3 x `payment_dispute` labelled `support_question`, 1 as `refund_request`, 1 as `invoice`), one example chargeback routed to the refunds queue, the cause, then the v2 breakdown: 100% | "The person with data and ML understanding catches step three." |

**Why v1 fails:** its label list was written from five easy examples and has no
`payment_dispute`. With nowhere to put a chargeback, the agent files it under the closest label:
on Groq's `gpt-oss-20b`, three as billing questions, one as a refund, one as an invoice. Support
sees it days later, the bank's deadline passes, and the money is
gone. **The fix (v2)** adds the missing type with a clear definition, and narrows
`refund_request` to customers asking us directly. Both label sets are at the top of
`classifier.py`, ready to show on screen.

## Shoot-day safety: warm the cache

```bash
python demo.py warm      # the day before, with GROQ_API_KEY set
```

That runs every beat once (about 165 model calls on `openai/gpt-oss-20b`; on Groq's free tier it
pauses for the per-minute limit and takes several minutes) and saves each answer
under `.cache/` in this folder. On camera the beats replay instantly with the same numbers.
`--fresh` forces live calls.

## What is verified, and what to check

Verified offline (`pytest`, with a keyword-based stand-in model): the dataset mix, that v1 has no
way to output `payment_dispute`, that the hand-picked five contain no dispute, and the whole
story end to end (5/5, ≥90% overall, disputes at 0%, fixed in v2).

Needs one real run before the shoot: the exact overall accuracy (fill it into the script), and
that the real model gets the common types right so the average stays high. With v1, the 5
disputes are guaranteed to fail because the label doesn't exist.

## Tests

```bash
pytest
```
