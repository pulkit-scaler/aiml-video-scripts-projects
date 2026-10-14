"""The on-camera beats for Video 8 (RAG deep dive). One command per beat.

    python demo.py beat1   the naive version: confident and wrong
    python demo.py beat2   fix one: split by section, not every 50 words
    python demo.py beat3   fix two: hybrid search finds the right paragraph
    python demo.py beat4   measure it: before and after scores
    python demo.py beat5   a question the docs don't cover: make it say "I don't know"
    python demo.py ask "your question" [naive|chunks|search|guarded]
    python demo.py warm    run everything once, so the shoot replays from cache

Add --fresh to any command to skip the cache and call the model live.
"""

import json
import sys

from rag import BETTER_CHUNKS, BETTER_SEARCH, GUARDED, NAIVE, PIPELINES, ROOT
import evaluate
from demokit.show import banner, wrap

QUESTIONS = {q["id"]: q for q in json.loads((ROOT / "data" / "questions.json").read_text())}
FRESH = "--fresh" in sys.argv


def show(pipeline, qid: str) -> None:
    q = QUESTIONS[qid]
    result = pipeline.ask(q["question"], fresh=FRESH)
    banner(pipeline.name)
    print(f"Question: {q['question']}\n")
    for i, chunk in enumerate(result["chunks"], 1):
        print(f"Chunk {i} it read:")
        print(wrap(chunk) + "\n")
    print("Answer:")
    print(wrap(result["answer"]))
    if q["answer"]:
        verdict = "CORRECT" if evaluate.is_correct(q, result["answer"]) else "WRONG"
        print(f"\nTrue answer: {q['answer']}   ->  {verdict}")


def beat1():
    show(NAIVE, "Q01")


def beat2():
    show(BETTER_CHUNKS, "Q01")


def beat3():
    show(BETTER_CHUNKS, "Q03")   # still finds the similar-sounding Team plan paragraph
    show(BETTER_SEARCH, "Q03")   # hybrid search finds the Enterprise SLA


def beat4():
    evaluate.main(list(PIPELINES))


def beat5():
    show(BETTER_SEARCH, "Q13")   # makes something up
    show(GUARDED, "Q13")         # says "I don't know"


def ask(question: str, name: str = "guarded") -> None:
    QUESTIONS["ad-hoc"] = {"question": question, "answer": None}
    show(PIPELINES[name], "ad-hoc")


def warm():
    for beat in (beat1, beat2, beat3, beat5):
        beat()
    beat4()


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--fresh"]
    if not args or args[0] not in {"beat1", "beat2", "beat3", "beat4", "beat5", "ask", "warm"}:
        print(__doc__)
    elif args[0] == "ask":
        ask(*args[1:3])
    else:
        globals()[args[0]]()
