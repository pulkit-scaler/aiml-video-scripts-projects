# Video 8: RAG deep dive, live

The masterclass follow-up's live segment (script "3:30 The deep dive, live"). A help-centre
assistant for Northwind Cloud (the same fictional company as Video 1) that answers from five
policy documents. It starts broken and gets fixed one switch at a time, on camera.

The shooting script for this video is [SCRIPT.md](SCRIPT.md).

## Setup

This folder is self-contained: its own code, data, requirements, `.env` and tests. Python 3.12 or newer.

```bash
cd video08-rag-deep-dive
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in GROQ_API_KEY
pytest                        # runs with no API key
```

## What's here

```
rag.py              the pipeline: chunker + search + prompt, and the four versions shown on camera
demo.py             one command per beat
evaluate.py         beat 4: score every version on the same questions
data/docs/*.md      the knowledge base (billing, service levels, security, data, support)
data/questions.json 12 questions with known answers + 2 the docs can't answer
demokit/            this demo's toolkit: Groq calls + replay cache, local embeddings, BM25, scoring
tests/              runs with no API key
SCRIPT.md           the shooting script
```

## The beats

| Beat | Command | What happens | Why it happens |
|---|---|---|---|
| 1. Naive, and where it breaks | `python demo.py beat1` | "How long does a customer on an annual plan have to request a refund?" The answer says **7 days**. True answer: 30 days. | Documents are cut every 50 words. The chunk it finds has the monthly plan's "7 days" and the start of the annual section, but the cut lands before "30 days". |
| 2. Fix one: chunking | `python demo.py beat2` | Same question, now **30 days**. | One chunk per section, labelled `[Billing and refunds > Annual plans]`. The answer was in the document all along. |
| 3. Fix two: search | `python demo.py beat3` | "What uptime does the Enterprise plan guarantee?" Keyword search returns the **Team plan** paragraph (99.5%). Hybrid search returns the **Enterprise SLA** (99.95%). | The Team paragraph shares the question's words ("uptime", "plan", "guarantee"). The SLA says "availability" and "contractual commitment". Embeddings match meaning, BM25 matches rare words, rank fusion merges both. |
| 4. Measure it | `python demo.py beat4` | A table: each version's *found* (right passage retrieved), *correct* and *made up* scores. | Same 14 questions every time. "Looks better" becomes a number. |
| 5. "I don't know" | `python demo.py beat5` | "Do you offer an on-premise version?" Without the guard it invents an answer. With it: "I don't know based on our documents." | The guarded prompt allows answers only from the retrieved context. |

Free questions during Q&A: `python demo.py ask "Is SSO on the Team plan?" guarded`
(swap `guarded` for `naive`, `chunks` or `search`).

At every beat, say what changed, why, and the takeaway. The script's `[FILL: demo scores]`
comes from the beat 4 table.

## Shoot-day safety: warm the cache

```bash
python demo.py warm      # the day before, with GROQ_API_KEY set
```

Answers come from Groq (default `openai/gpt-oss-120b`). Embeddings run locally with
`BAAI/bge-base-en-v1.5` (fastembed, about 210 MB, downloaded once into `.cache/fastembed/`), because
Groq has no embeddings API. Every model answer and embedding is saved under `.cache/` in this folder. On camera the same
commands replay instantly and identically, with no network. `--fresh` forces a live call;
`DEMO_CACHE=off` in `.env` turns replay off.

## What is verified, and what to check

Verified offline (`pytest`): beat 1's chunk contains "7 days" and not "30 days"; beat 2's
contains "30 days"; keyword search returns the Team paragraph for the Enterprise question;
hybrid search ranks the SLA in the top 3 (with a stand-in embedding model); every gold passage
exists in the docs; the scoring rules.

Verified live on Groq (`openai/gpt-oss-120b`, 14 Oct 2026), and replayed from the cache:

| Version | Found | Correct | Made up | Overall |
|---|---|---|---|---|
| 1. naive | 8/12 | 8/12 | 2/2 | 57% |
| 2. + split by section | 11/12 | 10/12 | 2/2 | 71% |
| 3. + hybrid search | 12/12 | 11/12 | 2/2 | 79% |
| 4. + "I don't know" guard | 12/12 | 11/12 | 0/2 | 93% |

Beat 1 answers "within 7 days" (wrong); beat 2 answers "30 days". Beat 3: keyword search answers
99.9% (wrong, from the Team paragraph); hybrid search ranks the Enterprise SLA 2nd and answers
99.95%. Beat 5: unguarded, it invents "we don't provide an on-premise version"; guarded, it says
"I don't know based on our documents."

Two details that matter on Groq. The smaller `bge-small` embedding model missed the SLA, so
`bge-base` is the default. And the 50-word cut must land before "30" in beat 1: `gpt-oss`
completes "within 30" to "30 days" on its own, so the billing doc's first sentence is worded to
put the cut at "...can request a full refund". Answers are tidied before scoring, because
`gpt-oss` writes "30 days" with a narrow no-break space. If one doesn't land, rerun with `--fresh`, or adjust the question wording in
`data/questions.json`.

## Tests

```bash
pytest
```
