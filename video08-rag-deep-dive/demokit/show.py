"""Plain console output that reads well on camera (no extra dependencies)."""

import textwrap


def banner(title: str) -> None:
    line = "=" * max(40, len(title) + 4)
    print(f"\n{line}\n  {title}\n{line}")


def table(rows: list[list], headers: list[str]) -> None:
    cells = [[str(c) for c in r] for r in [headers, *rows]]
    widths = [max(len(r[i]) for r in cells) for i in range(len(headers))]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*cells[0]))
    print("  ".join("-" * w for w in widths))
    for r in cells[1:]:
        print(fmt.format(*r))


def wrap(text: str, width: int = 88, indent: str = "  ") -> str:
    return "\n".join(textwrap.fill(p, width, initial_indent=indent, subsequent_indent=indent)
                     for p in text.splitlines() if p.strip())
