#!/usr/bin/env bash
# Put the Groq API key from your clipboard into every demo's .env, without ever printing it.
#
#   1. Copy your key from https://console.groq.com/keys
#   2. Run:  ./set-groq-key.sh
#
# The key goes from the clipboard straight into Python's stdin: it is never echoed, never in a
# command argument (so not in `ps` or shell history), and .env files are git-ignored and set to
# owner-only (600). On macOS the clipboard is cleared afterwards.
set -euo pipefail
cd "$(dirname "$0")"

if command -v pbpaste >/dev/null 2>&1; then
  read_clipboard() { pbpaste; }
elif command -v xclip >/dev/null 2>&1; then
  read_clipboard() { xclip -selection clipboard -o; }
else
  echo "No clipboard tool found (pbpaste or xclip). Paste the key into each .env by hand." >&2
  exit 1
fi

read_clipboard | python3 -c '
import pathlib, sys

key = sys.stdin.read().strip()
if not key.startswith("gsk_") or len(key) < 20 or any(c.isspace() for c in key):
    sys.exit("The clipboard does not hold a Groq API key (they start with gsk_). Nothing was changed.")

for folder in ["video01-support-agent", "video08-rag-deep-dive", "video10-eval-breakdown"]:
    env = pathlib.Path(folder, ".env")
    source = env if env.exists() else pathlib.Path(folder, ".env.example")
    lines = source.read_text().splitlines()
    if any(line.startswith("GROQ_API_KEY=") for line in lines):
        lines = [f"GROQ_API_KEY={key}" if line.startswith("GROQ_API_KEY=") else line for line in lines]
    else:
        lines.insert(0, f"GROQ_API_KEY={key}")
    env.write_text("\n".join(lines) + "\n")
    env.chmod(0o600)
    print(f"  {env}: key set")
print(f"Done. The key ({len(key)} characters) was saved and never printed.")
'

if command -v pbcopy >/dev/null 2>&1; then
  printf "" | pbcopy && echo "Clipboard cleared."
fi
