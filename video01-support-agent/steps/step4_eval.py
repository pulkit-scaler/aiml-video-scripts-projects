"""Step 4: evaluate. Run all 20 tickets, compare to the expected answer, score it.

Run:  python steps/step4_eval.py --prompt v1
      python steps/step4_eval.py --prompt v2
"""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so we can import agent.py
from agent import PROMPTS, classify

ROOT = Path(__file__).resolve().parent.parent


def grade(ticket, predicted):
    """One row of the results table."""
    return {
        "id": ticket["id"],
        "expected": ticket["expected_urgency"],
        "predicted": predicted,
        "passed": predicted == ticket["expected_urgency"],
    }


def accuracy(rows):
    return sum(r["passed"] for r in rows) / len(rows) if rows else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", choices=["v1", "v2"], default="v2")
    args = parser.parse_args()
    system_prompt = PROMPTS[args.prompt]

    tickets = json.loads((ROOT / "data" / "tickets.json").read_text())
    print(f"Running {len(tickets)} tickets with prompt {args.prompt}...\n")

    # Run 3 tickets at a time. On Groq's free tier the client waits and retries
    # if we go over the per-minute limit, so this may pause briefly.
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda t: classify(t, system_prompt), tickets))

    rows = [grade(t, r["urgency"]) for t, r in zip(tickets, results)]

    print(f"{'ID':<6} {'EXPECTED':<9} {'PREDICTED':<10} RESULT")
    for r in rows:
        print(f"{r['id']:<6} {r['expected']:<9} {r['predicted']:<10} {'PASS' if r['passed'] else 'FAIL'}")

    passed = sum(r["passed"] for r in rows)
    print(f"\nAccuracy ({args.prompt}): {passed}/{len(rows)} = {accuracy(rows):.0%}")


if __name__ == "__main__":
    main()
