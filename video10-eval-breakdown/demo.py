"""The on-camera beats for Video 10: "95% accurate and still broken".

    python demo.py beat1   5 hand-picked messages: all correct
    python demo.py beat2   all 80 messages: overall accuracy still looks great
    python demo.py beat3   split by message type: one rare type fails almost every time
    python demo.py beat4   look at the errors, fix the label set (v2), re-run the breakdown
    python demo.py warm    run everything once, so the shoot replays from cache

Add --fresh to skip the cache and call the model live.
"""

import sys

from classifier import INBOX, ROUTES, classify_all, handpicked, message_text
from demokit.evals import accuracy, breakdown, confusion, pct
from demokit.show import banner, table, wrap

FRESH = "--fresh" in sys.argv


def beat1():
    banner("Beat 1: five hand-picked messages (v1)")
    rows = classify_all(handpicked(), "v1", FRESH)
    table([[r["id"], r["truth"], r["pred"], "PASS" if r["passed"] else "FAIL"] for r in rows],
          ["id", "true label", "agent said", ""])
    print(f"\nAccuracy: {sum(r['passed'] for r in rows)}/{len(rows)}")


def beat2():
    banner(f"Beat 2: the full inbox, {len(INBOX)} messages (v1)")
    rows = classify_all(INBOX, "v1", FRESH)
    print(f"Accuracy: {sum(r['passed'] for r in rows)}/{len(rows)} = {pct(accuracy(rows))}")
    return rows


def show_breakdown(rows, title):
    banner(title)
    table([[g["group"], g["n"], f"{g['correct']}/{g['n']}", pct(g["accuracy"])] for g in breakdown(rows, "truth")],
          ["message type", "count", "correct", "accuracy"])
    print(f"\nOverall: {pct(accuracy(rows))}")


def beat3():
    rows = classify_all(INBOX, "v1", FRESH)
    show_breakdown(rows, "Beat 3: same run, split by message type (v1)")
    return rows


def beat4():
    rows = classify_all(INBOX, "v1", FRESH)
    banner("Beat 4a: what went wrong?")
    for (truth, pred), n in confusion(rows, "truth", "pred").most_common():
        print(f"  {n} x {truth} labelled as {pred}")
    worst = next((r for r in rows if r["truth"] == "payment_dispute" and not r["passed"]), None)
    if worst:
        msg = next(m for m in INBOX if m["id"] == worst["id"])
        print(f"\nExample, {worst['id']}:")
        print(wrap(message_text(msg)))
        print(f"\n  Agent said: {worst['pred']}, routed to {ROUTES[worst['pred']]}")
        print(f"  Should be:  payment_dispute, routed to {ROUTES['payment_dispute']}")
        print("\n  Cause: v1's label list has no 'payment_dispute'. It was built from five easy examples.")
    show_breakdown(classify_all(INBOX, "v2", FRESH), "Beat 4b: v2 adds payment_dispute, re-run")


def warm():
    beat1(); beat2(); beat3(); beat4()


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--fresh"]
    if not args or args[0] not in {"beat1", "beat2", "beat3", "beat4", "warm"}:
        print(__doc__)
    else:
        globals()[args[0]]()
