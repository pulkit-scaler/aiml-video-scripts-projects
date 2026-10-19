# Watch me build an AI agent in 15 minutes

A support-ticket triage agent for a fictional B2B SaaS company, Northwind Cloud.

For every ticket the agent:

1. summarises it,
2. sets urgency (`high` / `medium` / `low`),
3. looks up company policy (local search over `data/refund_policy.md`),
4. takes action: posts to Slack for `high` urgency, and saves a draft reply for every ticket.

It is built in five steps. Each step is a separate script that runs on its own.

The shooting script for this video is [SCRIPT.md](SCRIPT.md).

## Project layout

```
agent.py                 the finished agent: triage(ticket) -> dict
steps/step1_llm.py       one model call with structured output (strict JSON schema)
steps/step2_tools.py     three tools + the agent loop
steps/step3_rag.py       split the policy into chunks, index, search (BM25)
steps/step4_eval.py      run all 20 tickets, score accuracy (--prompt v1 | v2)
steps/step5_service.py   FastAPI service: POST /triage, GET /health
data/tickets.json        20 test tickets with expected urgency and action
data/refund_policy.md    the company policy the agent searches
data/sample_ticket.json  T-07, ready to send with curl
tests/                   pytest suite, runs with no API key
Dockerfile               container for the web service (build from this folder)
render.yaml              Render Blueprint for the web service
requirements.txt         this project's dependencies
.env.example             settings to copy into .env
SCRIPT.md                the shooting script
```

## Setup

This folder is self-contained: its own code, data, requirements, `.env` and tests. Python 3.12 or newer.

```bash
cd video01-support-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in GROQ_API_KEY
pytest                        # runs with no API key
```

`.env` values used here:

| Variable | Required | Notes |
|---|---|---|
| `GROQ_API_KEY` | yes | from console.groq.com/keys |
| `MODEL` | no | defaults to `openai/gpt-oss-20b`. It must support strict JSON schema on Groq: `openai/gpt-oss-20b` or `openai/gpt-oss-120b`. |
| `SLACK_WEBHOOK_URL` | no | a Slack incoming webhook (see [Set up Slack](#set-up-slack)). If empty, Slack messages are printed and appended to `outbox/slack.log`, so the demo never breaks. |

Draft replies are written to `outbox/drafts/<ticket_id>.md`.

## Set up Slack

The agent posts high-urgency alerts to a Slack channel through an incoming webhook. Setup takes
about five minutes, once.

1. Create a **private** channel for the alerts, for example `#northwind-oncall-alerts`. Private
   (or a separate demo workspace) means the alerts never reach colleagues.
2. Go to [api.slack.com/apps](https://api.slack.com/apps?new_app=1), click **Create New App**,
   choose **Blank app**, name it (for example "Northwind Triage Agent") and pick your workspace.
   It needs no scopes and no events: click **Continue** through both steps, then **Create**, and
   **Create Anyway** when Slack says the app can't do anything yet.
3. In the app's settings, open **Incoming Webhooks** and switch **Activate Incoming Webhooks** on.
4. Click **Add New Webhook**, pick your channel and click **Allow**. A channel made a minute ago
   may not show in the picker yet: open it once in Slack, then reload the page.
5. Back on **Incoming Webhooks**, click **Copy** next to the new webhook URL. It looks like
   `https://hooks.slack.com/services/T.../B.../...`.
6. Paste it into `.env` as `SLACK_WEBHOOK_URL=...`. If you deploy, add the same value in the
   Render (or Railway) environment variables.
7. Test it:

   ```bash
   python -c "import agent; print(agent.post_to_slack('Test from the triage agent'))"
   ```

   It prints `Posted to Slack.` and the message appears in the channel.

The webhook URL is a secret: anyone who has it can post to the channel. Keep it in `.env` only
(git ignores that file) and never show it on screen. If it leaks, delete the webhook on the
**Incoming Webhooks** page and add a new one. With a webhook set, alerts go to Slack only; with
it empty, they go to `outbox/slack.log`. The tests never post: they remove the webhook first.

## Run each step

Run everything from the project folder with the venv active. Run one demo at a time: the Groq
free tier allows 30 requests a minute per key, and two demos at once make each other wait.

```bash
python steps/step1_llm.py T-01                  # structured output for one ticket
python steps/step2_tools.py T-02                # agent loop: watch it pick tools
python steps/step3_rag.py "whole team locked out, payroll due today"
python steps/step4_eval.py --prompt v1          # naive prompt: 12/20, polite T-12 fails
python steps/step4_eval.py --prompt v2          # fixed prompt: 19/20, T-12 passes
uvicorn steps.step5_service:app --reload --port 8010   # web service on :8010
python agent.py T-07                            # the finished agent, one ticket
python agent.py data/fresh_ticket.json          # a ticket that isn't in the test set
```

Calling the service:

```bash
curl localhost:8010/health
curl -X POST localhost:8010/triage -H "Content-Type: application/json" -d @data/fresh_ticket.json
```

## The two prompts (the on-camera fix)

Both live in `agent.py`. The only change is one sentence plus three short definitions.

v1, a believable first draft:

```
Set urgency based on how upset the customer sounds: angry, frustrated or
threatening customers are high; calm and polite customers are low or medium.
```

v2, after the eval shows the failure:

```
Judge urgency by business impact and deadlines, not by tone.
- high: an outage, a whole team or many customers blocked, a security risk, data loss, or a deadline within a day.
- medium: one user or one feature blocked, or a billing problem such as a wrong charge, a double charge or a refund.
- low: questions, pricing or sales requests, feature requests, cosmetic issues and feedback, however angry the customer is.
```

Measured on Groq with `openai/gpt-oss-20b` at temperature 0 (the same on repeated runs, 14 Oct 2026):

| Prompt | Accuracy | Failures |
|---|---|---|
| v1 | 12/20 = 60% | polite but critical marked medium: T-08, T-12, T-14. Angry but trivial marked high: T-04, T-09, T-18. Billing marked high: T-01, T-13. |
| v2 | 19/20 = 95% | T-05 (one user locked out, marked high instead of medium) |

The ticket to show on camera is **T-12**: polite, and critical.

> Hi there, quick question when you have a moment: our nightly backups have failed for the last three nights. We have an external audit tomorrow at 9am ...

v1 reads the tone and calls it medium. v2 reads the impact and calls it high. v1 also fails the
other way: angry customers with trivial problems (T-04 blurry logo, T-09 moved button, T-18 missing
Gantt view) are marked high.

Why not T-07, the payroll ticket? `gpt-oss-20b` is a reasoning model and spots "payroll by 5pm
today" even with the naive prompt, so T-07 passes v1. It's still the best ticket for the cold open
and the end-to-end run, where the finished agent alerts Slack for it.

## Deploy

**Render (Blueprint):** in Render choose New, then Blueprint, pick the repo, and set the
Blueprint file path to `video01-support-agent/render.yaml`. It builds this folder's `Dockerfile`
and checks `/health`. Enter `GROQ_API_KEY` (and optionally `SLACK_WEBHOOK_URL`) when Render
asks; they are never stored in the repo.

**Railway:** New Project, then Deploy from GitHub repo. Set the root directory to
`video01-support-agent`. Add `GROQ_API_KEY` under Variables, then Settings, then Networking,
then Generate Domain.

**Local Docker:**

```bash
# from this folder
docker build -t triage-agent .
docker run --rm -p 8010:8000 --env-file .env triage-agent   # then curl localhost:8010/health
```

## Presenter run-of-show

Two terminals. Terminal A is where you build live. Terminal B holds the finished project with the
venv active and `.env` filled in (see Safety net).

| Time | Segment | Command (Terminal A) | What should appear on screen |
|---|---|---|---|
| 0:00 | Cold open | `python agent.py T-07` (pre-run in Terminal B is fine) | Tool calls scroll by (`lookup_policy`, `post_to_slack`, `save_draft_reply`), then JSON with `"urgency": "high"`. Show the alert arriving in the Slack channel (or the `[SLACK]` line if no webhook is set) and open `outbox/drafts/T-07.md`. |
| 1:00 | Pick the problem | `cat data/tickets.json`, `cat data/refund_policy.md` | A support inbox of 20 tickets and a real policy document. Explain: summarise, set urgency, check policy, act. |
| 2:30 | Step 1: call the model | `python steps/step1_llm.py T-01` | Clean JSON: `summary`, `urgency`, `recommended_action`. Point at the `Triage` class: "we tell it the exact shape we want back". |
| 4:00 | Step 2: tools | `python steps/step2_tools.py T-02`, then `python steps/step2_tools.py T-03` | T-02 (outage): `MODEL CALLS: lookup_policy`, `post_to_slack`, `save_draft_reply`. T-03 (dark mode request): no Slack call. Optional: edit the `post_to_slack` description to "Use this for EVERY ticket", rerun T-03, it now posts. Revert. |
| 6:30 | Step 3: RAG | `python steps/step3_rag.py "whole team locked out, payroll due today"` | "Policy split into 12 chunks", then the `## Account lockout procedure` section. Then try `"refund annual plan"`. |
| 8:30 | Step 4: eval, v1 | `python steps/step4_eval.py --prompt v1` | Results table with 8 FAIL rows, including `T-12 high medium FAIL`, and `Accuracy (v1): 12/20 = 60%`. |
| 9:30 | Step 4: fix and re-run | Show `PROMPT_V2` in `agent.py`, then `python steps/step4_eval.py --prompt v2` | `T-12` now passes; `Accuracy (v2): 19/20 = 95%`. Line to say: "Judge urgency by business impact and deadlines, not by tone." |
| 10:30 | Step 5: deploy | `uvicorn steps.step5_service:app --port 8010`, then `curl localhost:8010/health`; show `Dockerfile` and `render.yaml`; switch to the pre-deployed Render URL | `{"status":"ok","model":"..."}` locally, then the same from the public URL. |
| 12:30 | End to end | `curl -X POST <render-url>/triage -H "Content-Type: application/json" -d @data/fresh_ticket.json` | Full triage JSON for T-21, a ticket that isn't in the test set, with `"urgency": "high"` and all three tools in `actions_taken`, and the `HIGH urgency` alert arriving in the Slack channel. (On a deployed service the draft is saved on the server, so point at `save_draft_reply` in `actions_taken`.) |

### Safety net

Keep a second terminal (Terminal B) open in a copy of the finished project, venv active, `.env`
filled, server already running on another port (`uvicorn steps.step5_service:app --port 8001`).
If anything fails live (network, typo, rate limit), switch to Terminal B and run the same command.
Record the cold open and the eval runs once before the shoot as fallback footage. The Render
service should be deployed before the shoot; the "deploy" segment shows the files and hits the
already-live URL, because a cold Docker build takes several minutes.

### Pre-shoot checklist

- [ ] `pytest -q` passes in both terminals.
- [ ] `.env` has `GROQ_API_KEY`.
- [ ] Run `python steps/step4_eval.py --prompt v1` and `--prompt v2` twice each and note the numbers. The eval runs at temperature 0, so the numbers should repeat; confirm T-12 fails on v1 and passes on v2.
- [ ] Slack: webhook set up (see [Set up Slack](#set-up-slack)), in `.env` and in Render, and the alert channel open on a second screen. Or leave it empty and show `outbox/slack.log`.
- [ ] Nothing else uses the Groq key during the shoot. On the free tier, another demo running at the same time makes the agent pause, and it prints `(Groq rate limit: waiting Ns)`.
- [ ] Port 8010 is free: `lsof -i :8010` prints nothing.
- [ ] Clear old output: `rm -rf outbox`.
- [ ] Render service deployed, `/health` returns ok, `GROQ_API_KEY` set in the Render dashboard (free plans sleep: hit `/health` five minutes before recording).
- [ ] Terminal font large (18pt or more), dark theme, prompt shortened, notifications off.
- [ ] Never show `.env` or the Render environment page on screen. Check the API key has a spend limit.
- [ ] Browser tabs ready: Render dashboard, Slack channel, `localhost:8010/docs` (FastAPI's auto docs page).

## Tests

```bash
pytest
```

The suite mocks the Groq client, so it needs no key and makes no network calls. It covers:
retrieval returns the lockout section for a lockout query, the tools write to `outbox`, the agent
loop runs tools and returns a result with a fake model, `/health` and `/triage` work with a mocked
triage, and the eval scoring math.

## A note on the agent loop

Groq doesn't allow structured output and tool calling in the same request. So the full agent
(`triage()` in `agent.py`) runs the tool loop first, then makes one last call without tools
that returns the final triage in the JSON schema. The eval (`classify()`) uses no tools, so
it's a single call. `openai/gpt-oss-20b` calls one tool per turn, so on screen the tools run one
after another: `lookup_policy`, then `post_to_slack`, then `save_draft_reply`.

On Groq's free tier the client waits and retries when it hits the per-minute limit. A live
step 4 eval (40 calls across v1 and v2) can pause for a minute because of that.
