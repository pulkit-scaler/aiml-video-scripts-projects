# AIML Video Series: demo projects

The three videos in the series that show a working project on screen. Each folder holds the
video's shooting script (`SCRIPT.md`) next to a complete, self-contained project: code, data,
requirements, settings, tests and a run-of-show guide. Nothing is shared between folders, so any
one of them can be copied out and run on its own. The scripts for the other videos are in the
team's script docs.

All demos use the same fictional company, Northwind Cloud, a B2B SaaS business.

| # | Video | Length | Folder | The demo |
|---|---|---|---|---|
| 1 | Watch me build an AI agent in 15 minutes | 13-15 min | [`video01-support-agent`](video01-support-agent/) | A support-ticket agent with tools, RAG, an eval and a deploy |
| 8 | Masterclass Part 2: the deep dive | 25-35 min | [`video08-rag-deep-dive`](video08-rag-deep-dive/) | RAG that breaks, then gets fixed and measured |
| 10 | Why DS/ML fundamentals get you the AI job | 7-7.5 min | [`video10-eval-breakdown`](video10-eval-breakdown/) | 95% accurate and still broken |

## Running a demo

Each demo folder has its own `requirements.txt`, `.env` and tests. Python 3.12 or newer.
The only API key is a [Groq](https://console.groq.com/keys) key. Video 8's embeddings run locally.
To add the key without it ever showing on screen: copy it, then run `./set-groq-key.sh`. It writes
the key from your clipboard into all three `.env` files and clears the clipboard.

```bash
cd video08-rag-deep-dive          # or video01-support-agent, video10-eval-breakdown
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # then fill in GROQ_API_KEY (console.groq.com/keys)
pytest                            # runs with no API key
```

Each folder's `README.md` is its guide. It lists which command goes with which line of the
script, and what should appear on screen.

## Shoot-day checklist

- **The day before:** in Videos 8 and 10, run `python demo.py warm`. Every model answer is saved
  in that folder's `.cache/`, so on camera the same commands replay the same answers instantly,
  even offline. Video 1 is built live, so its steps call the model directly. Run them twice
  the day before and confirm the results in its README's pre-shoot checklist.
- **Never show `.env`** or any dashboard with keys on screen.
- **Groq's free tier is rate-limited** (about 30 requests and 8K tokens a minute, 200K tokens a
  day per model). The demos wait and retry when they hit the per-minute limit, so a big run can
  pause. Warm the caches the day before. For Video 1, which runs live, a paid Groq plan or a
  pre-recorded take of the eval avoids pauses on camera.

## Facts quoted in the scripts

Video 1 quotes the Air Canada chatbot case, and Video 10 quotes Chip Huyen's book
*AI Engineering*. Both are listed with their sources in [SOURCES.md](SOURCES.md), along with the
sign-offs needed before recording.
