"""Beat 4: score every pipeline on the same test questions.

    python evaluate.py                 # all four pipelines
    python evaluate.py naive guarded   # just these

Two scores per pipeline:
  found    the retrieved chunks contain the passage with the answer (no model needed)
  correct  the final answer contains the key fact; for questions the docs can't
           answer, "correct" means it said "I don't know" instead of inventing one
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor

from demokit.evals import accuracy
from demokit.show import banner, table
from rag import IDK, PIPELINES, ROOT

QUESTIONS = json.loads((ROOT / "data" / "questions.json").read_text())


def found(pipeline, q: dict) -> bool:
    context = " ".join(c for _, c in pipeline.retrieve(q["question"])).lower()
    return q["gold"] is not None and q["gold"].lower() in context


def is_correct(q: dict, answer: str) -> bool:
    a = answer.lower()
    if q["answer"] is None:  # not in the docs: the only right answer is "I don't know"
        return "don't know" in a or "do not know" in a
    return all(fact.lower() in a for fact in q["must_include"])


def grade(pipeline, q: dict) -> dict:
    answer = pipeline.ask(q["question"])["answer"]
    return {"id": q["id"], "answerable": q["answer"] is not None,
            "found": found(pipeline, q) if q["answer"] else None,
            "answer": answer, "passed": is_correct(q, answer)}


def run(pipeline, questions=QUESTIONS) -> list[dict]:
    with ThreadPoolExecutor(max_workers=3) as pool:
        return list(pool.map(lambda q: grade(pipeline, q), questions))


def main(names: list[str]) -> None:
    banner("RAG eval: same questions, four pipelines")
    answerable = [q for q in QUESTIONS if q["answer"]]
    print(f"{len(answerable)} questions with a known answer, "
          f"{len(QUESTIONS) - len(answerable)} the docs can't answer.\n")
    summary = []
    for name in names:
        p = PIPELINES[name]
        rows = run(p)
        ans = [r for r in rows if r["answerable"]]
        unans = [r for r in rows if not r["answerable"]]
        summary.append([p.name,
                        f"{sum(r['found'] for r in ans)}/{len(ans)}",
                        f"{sum(r['passed'] for r in ans)}/{len(ans)}",
                        f"{sum(not r['passed'] for r in unans)}/{len(unans)}",
                        f"{accuracy(rows):.0%}"])
        misses = [r["id"] for r in rows if not r["passed"]]
        if misses:
            print(f"  {p.name}: wrong on {', '.join(misses)}")
    print()
    table(summary, ["pipeline", "found", "correct", "made up", "overall"])
    print(f'\n"made up" = answered a question the docs do not cover instead of "{IDK}"')


if __name__ == "__main__":
    main(sys.argv[1:] or list(PIPELINES))
