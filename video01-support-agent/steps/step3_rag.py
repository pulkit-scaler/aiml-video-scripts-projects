"""Step 3: retrieval (RAG). Find the right paragraph of policy, not the whole file.

Run:  python steps/step3_rag.py "whole team locked out, payroll due today"

No extra API keys: BM25 is a classic keyword-ranking algorithm that runs locally.
"""

import re
import sys
from pathlib import Path

from rank_bm25 import BM25Okapi


# 1. Load the policy and split it into chunks, one per "## " heading.
def load_chunks(path="data/refund_policy.md"):
    text = Path(path).read_text()
    sections = re.split(r"\n(?=## )", text)
    return [s.strip() for s in sections if s.startswith("## ")]


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


# 2. Index the chunks.
CHUNKS = load_chunks(Path(__file__).resolve().parent.parent / "data" / "refund_policy.md")
INDEX = BM25Okapi([tokenize(c) for c in CHUNKS])


# 3. Search: score every chunk against the query, return the best ones.
def search_policy(query, k=2):
    scores = INDEX.get_scores(tokenize(query))
    best = sorted(range(len(CHUNKS)), key=lambda i: scores[i], reverse=True)
    return [CHUNKS[i] for i in best[:k]]


# This is what lookup_policy now does inside agent.py.
def lookup_policy(query):
    return "\n\n---\n\n".join(search_policy(query))


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "whole team locked out, payroll due today"
    print(f"Policy split into {len(CHUNKS)} chunks.")
    print(f"Query: {query}\n")
    print("Best match:\n")
    print(search_policy(query, k=1)[0])
