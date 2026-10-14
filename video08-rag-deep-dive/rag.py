"""RAG over Northwind Cloud's help-centre docs, built so each fix is one switch.

    from rag import Pipeline, NAIVE, BETTER_CHUNKS, BETTER_SEARCH, GUARDED
    answer = GUARDED.ask("How long do annual plans have to request a refund?")

A pipeline is three choices:
  chunker   "fixed"    cut every document into blocks of N words (the usual first attempt)
            "sections" one chunk per heading, with the document and section title on top
  search    "overlap"  count shared words, take the single best chunk
            "hybrid"   keyword ranking (BM25) + meaning (embeddings), fused, top k chunks
  prompt    "plain"    "answer using the context"
            "guarded"  answer only from the context, otherwise say "I don't know"
"""

import re
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from demokit import llm
from demokit.retrieval import BM25Index, cosine, rank_fusion, tokenize

ROOT = Path(__file__).resolve().parent

DOCS_DIR = ROOT / "data" / "docs"
IDK = "I don't know based on our documents."

PROMPT_PLAIN = """You are Northwind Cloud's help assistant. Answer the customer's question
using the context below. Be short and specific."""

PROMPT_GUARDED = f"""You are Northwind Cloud's help assistant. Answer the customer's question
using ONLY the context below. Be short and specific, and name the section you used.
If the context does not contain the answer, reply exactly: {IDK}
Never guess, and never use outside knowledge."""


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def load_docs(folder: Path = DOCS_DIR) -> dict[str, str]:
    return {p.name: p.read_text() for p in sorted(folder.glob("*.md"))}


def chunk_fixed(docs: dict[str, str], size: int = 50) -> list[str]:
    """Every `size` words becomes a chunk, wherever that cut lands."""
    chunks = []
    for text in docs.values():
        words = re.sub(r"^#+ ", "", text, flags=re.M).split()
        chunks += [" ".join(words[i:i + size]) for i in range(0, len(words), size)]
    return chunks


def chunk_sections(docs: dict[str, str]) -> list[str]:
    """One chunk per '## ' section, labelled 'Doc title > Section title'."""
    chunks = []
    for text in docs.values():
        title = text.splitlines()[0].lstrip("# ").strip()
        for section in re.split(r"\n(?=## )", text)[1:]:
            heading, _, body = section.partition("\n")
            chunks.append(f"[{title} > {heading.lstrip('# ').strip()}]\n{body.strip()}")
    return chunks


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search_overlap(chunks: list[str], query: str, k: int = 1) -> list[tuple[float, str]]:
    """Score = how many times the query's words appear in the chunk. Long chunks win."""
    q = tokenize(query)
    scored = [(float(sum(tokenize(c).count(w) for w in q)), c) for c in chunks]
    return sorted(scored, key=lambda s: s[0], reverse=True)[:k]


@dataclass(frozen=True)
class Pipeline:
    name: str
    chunker: str = "fixed"      # "fixed" | "sections"
    search: str = "overlap"     # "overlap" | "hybrid"
    k: int = 1
    prompt: str = "plain"       # "plain" | "guarded"
    chunk_words: int = 50

    @cached_property
    def chunks(self) -> list[str]:
        docs = load_docs()
        return chunk_fixed(docs, self.chunk_words) if self.chunker == "fixed" else chunk_sections(docs)

    @cached_property
    def index(self) -> BM25Index:
        return BM25Index(self.chunks)

    @cached_property
    def vectors(self) -> list[list[float]]:
        return llm.embed(self.chunks, "RETRIEVAL_DOCUMENT")

    def retrieve(self, question: str) -> list[tuple[float, str]]:
        if self.search == "overlap":
            return search_overlap(self.chunks, question, self.k)
        # Keywords: BM25 finds chunks that share the question's rare words.
        keyword = [self.chunks.index(c) for _, c in self.index.search(question, len(self.chunks))]
        # Meaning: embeddings find chunks that say the same thing in other words
        # ("guarantee" vs "contractual commitment", "uptime" vs "availability").
        q = llm.embed([question], "RETRIEVAL_QUERY")[0]
        sims = [cosine(q, v) for v in self.vectors]
        meaning = sorted(range(len(self.chunks)), key=lambda i: sims[i], reverse=True)
        best = rank_fusion(keyword, meaning)[: self.k]
        return [(round(sims[i], 3), self.chunks[i]) for i in best]

    def build_prompt(self, question: str, hits: list[tuple[float, str]]) -> str:
        context = "\n\n---\n\n".join(c for _, c in hits) or "(no relevant documents found)"
        return f"Context:\n{context}\n\nQuestion: {question}"

    def ask(self, question: str, fresh: bool = False) -> dict:
        hits = self.retrieve(question)
        system = PROMPT_GUARDED if self.prompt == "guarded" else PROMPT_PLAIN
        answer = llm.generate_text(self.build_prompt(question, hits), system, fresh=fresh)
        return {"question": question, "answer": answer, "chunks": [c for _, c in hits]}


# The four versions shown on camera, in order. Each changes one thing.
NAIVE = Pipeline("1. naive: fixed chunks + word overlap")
BETTER_CHUNKS = Pipeline("2. + split by section", chunker="sections")
BETTER_SEARCH = Pipeline("3. + hybrid search, top 3", chunker="sections", search="hybrid", k=3)
GUARDED = Pipeline("4. + 'I don't know' guard", chunker="sections", search="hybrid", k=3, prompt="guarded")

PIPELINES = {"naive": NAIVE, "chunks": BETTER_CHUNKS, "search": BETTER_SEARCH, "guarded": GUARDED}
