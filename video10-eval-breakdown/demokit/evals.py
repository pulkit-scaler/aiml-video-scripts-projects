"""Scoring helpers shared by the eval demos."""

from collections import Counter, defaultdict


def accuracy(rows: list[dict], key: str = "passed") -> float:
    return sum(1 for r in rows if r[key]) / len(rows) if rows else 0.0


def breakdown(rows: list[dict], group: str, key: str = "passed") -> list[dict]:
    """Accuracy per group, worst first. Each row needs `group` and `key` fields."""
    groups = defaultdict(list)
    for r in rows:
        groups[r[group]].append(r)
    out = [{"group": g, "n": len(rs), "correct": sum(1 for r in rs if r[key]),
            "accuracy": accuracy(rs, key)} for g, rs in groups.items()]
    return sorted(out, key=lambda r: (r["accuracy"], -r["n"]))


def confusion(rows: list[dict], truth: str, pred: str) -> Counter:
    """Counts of (truth, prediction) pairs for the rows that were wrong."""
    return Counter((r[truth], r[pred]) for r in rows if r[truth] != r[pred])


def pct(x: float) -> str:
    return f"{x:.0%}" if x in (0, 1) else f"{x:.1%}"
