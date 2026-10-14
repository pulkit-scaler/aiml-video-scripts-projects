"""Video 10 tests. No API key: the model is faked."""

from collections import Counter

import pytest

import build_dataset
import classifier
import demo
from demokit import evals, llm


def keyword_model(prompt, schema, system="", **kw):
    """A fake model that labels by keywords, and can only use the labels it is given."""
    allowed = schema["properties"]["label"]["enum"]
    text = prompt.lower()
    if "dispute" in text or "chargeback" in text:
        label = "payment_dispute" if "payment_dispute" in allowed else "refund_request"
    elif "invoice" in text and "from: billing@" in text:
        label = "invoice"
    elif "refund" in text or "charged" in text or "money back" in text:
        label = "refund_request"
    elif "renew" in text or "quote" in text or "upgrade" in text:
        label = "contract_renewal"
    else:
        label = "support_question"
    return {"label": label, "reason": "keywords"}


@pytest.fixture(autouse=True)
def fake_model(monkeypatch):
    monkeypatch.setattr(llm, "generate_json", keyword_model)


def test_dataset_is_reproducible_and_has_the_right_mix():
    assert build_dataset.build() != []  # builds without error
    counts = Counter(m["label"] for m in classifier.INBOX)
    assert counts == {"invoice": 25, "refund_request": 20, "support_question": 20,
                      "contract_renewal": 10, "payment_dispute": 5}


def test_v1_cannot_say_payment_dispute():
    assert "payment_dispute" not in classifier.LABELS_V1
    assert "payment_dispute" in classifier.LABELS_V2
    assert classifier.schema(classifier.LABELS_V1)["properties"]["label"]["enum"] == list(classifier.LABELS_V1)


def test_handpicked_has_no_rare_messages():
    picks = classifier.handpicked()
    assert len(picks) == 5 and len({m["id"] for m in picks}) == 5
    assert all(m["label"] != "payment_dispute" for m in picks)


def test_the_story_v1_hides_disputes_v2_fixes_them():
    v1 = classifier.classify_all(classifier.INBOX, "v1")
    by_type = {g["group"]: g for g in evals.breakdown(v1, "truth")}
    assert by_type["payment_dispute"]["accuracy"] == 0
    assert evals.accuracy(v1) >= 0.9          # the average still looks great
    v2 = classifier.classify_all(classifier.INBOX, "v2")
    assert {g["group"]: g for g in evals.breakdown(v2, "truth")}["payment_dispute"]["accuracy"] == 1


def test_breakdown_sorts_worst_first():
    rows = [{"g": "a", "passed": True}, {"g": "b", "passed": False}, {"g": "a", "passed": True}]
    assert [r["group"] for r in evals.breakdown(rows, "g")] == ["b", "a"]


def test_all_beats_run(capsys):
    demo.warm()
    out = capsys.readouterr().out
    assert "Accuracy: 5/5" in out
    assert "payment_dispute labelled as refund_request" in out
    assert "Beat 4b" in out
