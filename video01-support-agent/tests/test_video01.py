"""Tests run with NO API key: the Groq client is replaced with a fake."""

import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import agent
from steps import step3_rag, step4_eval, step5_service


@pytest.fixture(autouse=True)
def temp_outbox(tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "OUTBOX", tmp_path / "outbox")
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    return tmp_path / "outbox"


# --- retrieval -------------------------------------------------------------

@pytest.mark.parametrize("search", [agent.search_policy, step3_rag.search_policy])
def test_lockout_query_finds_lockout_section(search):
    top = search("our whole team is locked out of their accounts", k=1)[0]
    assert top.startswith("## Account lockout procedure")


def test_refund_query_finds_refund_section():
    top = agent.search_policy("refund for an annual plan", k=1)[0]
    assert top.startswith("## Refunds on annual plans")


def test_chunks_are_one_per_heading():
    assert all(c.startswith("## ") for c in agent.CHUNKS)
    assert len(agent.CHUNKS) >= 8


# --- tools -----------------------------------------------------------------

def test_post_to_slack_without_webhook_writes_log(temp_outbox):
    agent.post_to_slack("T-07 finance team locked out")
    assert "T-07 finance team locked out" in (temp_outbox / "slack.log").read_text()


def test_save_draft_reply_writes_file(temp_outbox):
    agent.save_draft_reply("T-07", "Hi Linda, we're on it.")
    assert (temp_outbox / "drafts" / "T-07.md").read_text() == "Hi Linda, we're on it."


def test_tool_schemas_match_functions():
    names = [t["function"]["name"] for t in agent.TOOLS]
    assert names == ["lookup_policy", "post_to_slack", "save_draft_reply"]
    assert set(agent.TOOL_FUNCTIONS) == set(names)
    assert all(t["type"] == "function" for t in agent.TOOLS)


# --- the agent loop, with a fake model ---------------------------------------

def _reply(content=None, tool_calls=None):
    """The shape of a Groq chat completion: choices[0].message."""
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=tool_calls))])


def _call(call_id, name, args):
    return SimpleNamespace(id=call_id, type="function",
                           function=SimpleNamespace(name=name, arguments=json.dumps(args)))


class FakeCompletions:
    """Replays a script: ask for two tools, then stop, then give the final JSON answer."""

    def __init__(self):
        self.requests = []

    def create(self, **kwargs):
        self.requests.append({**kwargs, "messages": list(kwargs["messages"])})
        n = len(self.requests)
        if n == 1:
            return _reply(tool_calls=[
                _call("call_1", "post_to_slack", {"message": "T-07 lockout"}),
                _call("call_2", "save_draft_reply", {"ticket_id": "T-07", "reply": "On it."}),
            ])
        if n == 2:
            return _reply(content="Done: alerted the team and drafted a reply.")
        final = {"summary": "Finance locked out", "urgency": "high", "recommended_action": "Unlock now"}
        return _reply(content=json.dumps(final))


def _fake_client():
    return SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))


def test_triage_loop_runs_tools_and_returns_result(monkeypatch, temp_outbox):
    fake = _fake_client()
    monkeypatch.setattr(agent, "get_client", lambda: fake)
    ticket = {"id": "T-07", "from": "a@b.com", "subject": "s", "body": "b"}

    result = agent.triage(ticket)

    assert result["urgency"] == "high"
    assert result["actions_taken"] == ["post_to_slack", "save_draft_reply"]
    assert (temp_outbox / "drafts" / "T-07.md").exists()
    requests = fake.chat.completions.requests
    assert len(requests) == 3
    # Tool results go back to the model, matched to the call that asked for them.
    tool_msgs = [m for m in requests[1]["messages"] if m["role"] == "tool"]
    assert [m["tool_call_id"] for m in tool_msgs] == ["call_1", "call_2"]
    # The tool calls and the final structured answer go in separate requests.
    assert requests[0]["tools"] == agent.TOOLS and "response_format" not in requests[0]
    assert requests[2]["response_format"]["json_schema"]["schema"] == agent.TRIAGE_SCHEMA
    assert "tools" not in requests[2]


def test_triage_stops_after_max_rounds(monkeypatch, temp_outbox):
    """A model that never stops calling tools can't loop forever."""
    class Looping(FakeCompletions):
        def create(self, **kwargs):
            self.requests.append(kwargs)
            if "tools" in kwargs:
                return _reply(tool_calls=[_call("c", "lookup_policy", {"query": "refund"})])
            return _reply(content=json.dumps({"summary": "s", "urgency": "low", "recommended_action": "a"}))

    fake = SimpleNamespace(chat=SimpleNamespace(completions=Looping()))
    monkeypatch.setattr(agent, "get_client", lambda: fake)
    result = agent.triage({"id": "T-01", "from": "a", "subject": "s", "body": "b"}, max_rounds=3)
    assert result["actions_taken"] == ["lookup_policy"] * 3


# --- eval scoring -----------------------------------------------------------

def test_grade_and_accuracy():
    tickets = [{"id": "A", "expected_urgency": "high"},
               {"id": "B", "expected_urgency": "low"},
               {"id": "C", "expected_urgency": "medium"},
               {"id": "D", "expected_urgency": "high"}]
    rows = [step4_eval.grade(t, p) for t, p in zip(tickets, ["high", "low", "low", "low"])]
    assert [r["passed"] for r in rows] == [True, True, False, False]
    assert step4_eval.accuracy(rows) == 0.5
    assert step4_eval.accuracy([]) == 0.0


def test_dataset_has_20_tickets_and_planted_t07():
    tickets = json.loads((agent.ROOT / "data" / "tickets.json").read_text())
    assert [t["id"] for t in tickets] == [f"T-{i:02d}" for i in range(1, 21)]
    t07 = next(t for t in tickets if t["id"] == "T-07")
    assert t07["expected_urgency"] == "high" and "payroll" in t07["body"]


# --- web service --------------------------------------------------------------

def test_health():
    client = TestClient(step5_service.app)
    assert client.get("/health").json()["status"] == "ok"


def test_triage_route(monkeypatch):
    seen = {}

    def fake_triage(ticket):
        seen.update(ticket)
        return {"ticket_id": ticket["id"], "urgency": "high"}

    monkeypatch.setattr(agent, "triage", fake_triage)
    client = TestClient(step5_service.app)
    body = {"id": "T-07", "from": "linda@fairwayfoods.com", "subject": "Access", "body": "Locked out"}

    response = client.post("/triage", json=body)

    assert response.status_code == 200
    assert response.json() == {"ticket_id": "T-07", "urgency": "high"}
    assert seen["from"] == "linda@fairwayfoods.com"


def test_eval_end_to_end_with_fake_classifier(monkeypatch, capsys):
    # Pretend the model answers "low" for every ticket: only the 8 low tickets pass.
    monkeypatch.setattr(step4_eval, "classify", lambda t, prompt: {"urgency": "low"})
    monkeypatch.setattr("sys.argv", ["step4_eval.py", "--prompt", "v1"])
    step4_eval.main()
    out = capsys.readouterr().out
    assert "T-07   high      low        FAIL" in out
    assert "Accuracy (v1): 8/20 = 40%" in out


def test_classify_sends_prompt_and_schema(monkeypatch):
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return _reply(content=json.dumps({"summary": "s", "urgency": "high", "recommended_action": "a"}))

    fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create)))
    monkeypatch.setattr(agent, "get_client", lambda: fake)
    result = agent.classify({"id": "T-07", "from": "x", "subject": "s", "body": "payroll"}, agent.PROMPT_V1)
    assert result["urgency"] == "high"
    assert captured["messages"][0] == {"role": "system", "content": agent.PROMPT_V1}
    schema_format = captured["response_format"]
    assert schema_format["type"] == "json_schema" and schema_format["json_schema"]["strict"] is True
    assert schema_format["json_schema"]["schema"] == agent.TRIAGE_SCHEMA


def test_triage_schema_is_valid_for_strict_mode():
    """Groq strict mode: every property required, no extra properties allowed."""
    schema = agent.TRIAGE_SCHEMA
    assert set(schema["required"]) == set(schema["properties"])
    assert schema["additionalProperties"] is False


def test_prompt_v2_has_the_fix():
    assert "Judge urgency by business impact and deadlines, not by tone." in agent.PROMPT_V2
    assert "not by tone" not in agent.PROMPT_V1


def test_step_scripts_import_without_api_key():
    import importlib
    for name in ["steps.step1_llm", "steps.step2_tools"]:
        importlib.import_module(name)


def test_wait_seconds_reads_groq_rate_limit_message():
    no_header = SimpleNamespace(headers={})

    class Err(Exception):
        response = no_header

    assert agent.wait_seconds(Err("Please try again in 3.08s.")) == 3.08
    assert agent.wait_seconds(Err("Please try again in 1m2.5s.")) == 62.5
    assert agent.wait_seconds(Err("no hint")) == 5.0

    class WithHeader(Exception):
        response = SimpleNamespace(headers={"retry-after": "7"})

    assert agent.wait_seconds(WithHeader("x")) == 7.0


def _rate_limit_error(message="Rate limit reached. Please try again in 4s."):
    import httpx
    from groq import RateLimitError
    response = httpx.Response(429, request=httpx.Request("POST", "https://api.groq.com"))
    return RateLimitError(message, response=response, body=None)


def test_complete_waits_out_rate_limits_then_succeeds(monkeypatch):
    calls, sleeps = [], []
    monkeypatch.setattr(agent.time, "sleep", sleeps.append)

    def create(**kwargs):
        calls.append(kwargs)
        if len(calls) < 3:
            raise _rate_limit_error()
        return "ok"

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    assert agent.complete(client, model="m") == "ok"
    assert len(calls) == 3 and sleeps == [4.5, 4.5]
    assert "max_wait" not in calls[0]


def test_complete_gives_a_plain_message_not_a_traceback(monkeypatch):
    monkeypatch.setattr(agent.time, "sleep", lambda s: None)

    def create(**kwargs):
        raise _rate_limit_error()

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    with pytest.raises(SystemExit, match="kept rate-limiting"):
        agent.complete(client, max_wait=20, model="m")


def test_fresh_ticket_is_not_in_the_test_set():
    tickets = json.loads((agent.ROOT / "data" / "tickets.json").read_text())
    fresh = json.loads((agent.ROOT / "data" / "fresh_ticket.json").read_text())
    assert fresh["id"] not in {t["id"] for t in tickets}
    assert fresh["body"] not in {t["body"] for t in tickets}
    assert {"id", "from", "subject", "body"} <= fresh.keys()
