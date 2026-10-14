"""Video 8 tests. No API key: the model and the embeddings are faked."""

import re

import pytest

import evaluate
import rag
from demokit import llm

Q = {q["id"]: q for q in evaluate.QUESTIONS}

# A toy "meaning" model: words that mean the same thing share a dimension.
SYNONYMS = {"availability": "uptime", "guarantee": "commitment", "contractual": "commitment"}
VOCAB = ["uptime", "commitment", "enterprise", "team", "refund", "annual", "monthly", "data", "sso"]


def fake_embed(texts, task="RETRIEVAL_DOCUMENT", fresh=False):
    out = []
    for t in texts:
        words = [SYNONYMS.get(w, w) for w in re.findall(r"[a-z]+", t.lower())]
        out.append([float(words.count(v)) for v in VOCAB])
    return out


@pytest.fixture(autouse=True)
def fake_model(monkeypatch):
    monkeypatch.setattr(llm, "embed", fake_embed)
    calls = []

    def fake_text(prompt, system="", **kw):
        calls.append((prompt, system))
        return "fake answer"

    monkeypatch.setattr(llm, "generate_text", fake_text)
    return calls


def context(pipeline, qid):
    return " ".join(c for _, c in pipeline.retrieve(Q[qid]["question"]))


# Beat 1 -> 2: the naive cut separates "annual plan" from "30 days".
def test_beat1_naive_chunk_has_wrong_number_not_right_one():
    ctx = context(rag.NAIVE, "Q01")
    assert "annual plan" in ctx and "7 days" in ctx and "30 days" not in ctx
    # Not even "within 30": a strong model fills in "days" by itself and gets it right.
    assert "within 30" not in ctx


def test_tidy_makes_gpt_oss_text_plain():
    assert llm.tidy("within **30\u202fdays** \u2014 don\u2019t") == "within 30 days \u2014 don't"


def test_beat2_section_chunk_has_the_answer():
    assert "full refund within 30 days" in context(rag.BETTER_CHUNKS, "Q01")


# Beat 3: keyword search picks the similar-sounding Team paragraph; hybrid finds the SLA.
def test_beat3_keyword_search_picks_team_plan():
    ctx = context(rag.BETTER_CHUNKS, "Q03")
    assert "Team plan uptime" in ctx and "99.95" not in ctx


def test_beat3_hybrid_search_finds_enterprise_sla():
    assert "99.95% monthly availability" in context(rag.BETTER_SEARCH, "Q03")


def test_sections_are_labelled_with_doc_and_heading():
    assert all(re.match(r"\[.+ > .+\]\n", c) for c in rag.BETTER_CHUNKS.chunks)


# Beat 4: scoring rules.
def test_is_correct_rules():
    assert evaluate.is_correct(Q["Q01"], "You have 30 days from purchase.")
    assert not evaluate.is_correct(Q["Q01"], "You have 7 days.")
    assert evaluate.is_correct(Q["Q13"], rag.IDK)
    assert not evaluate.is_correct(Q["Q13"], "Yes, we offer on-premise.")


def test_question_set_shape():
    assert len(Q) == 14 and sum(q["answer"] is None for q in Q.values()) == 2


def test_every_gold_passage_exists_in_the_docs():
    corpus = " ".join(rag.load_docs().values())
    for q in Q.values():
        if q["gold"]:
            assert q["gold"] in corpus, q["id"]


# Beat 5: the guarded prompt.
def test_guarded_prompt_is_sent(fake_model):
    rag.GUARDED.ask(Q["Q13"]["question"])
    assert rag.IDK in fake_model[-1][1]
    rag.BETTER_SEARCH.ask(Q["Q13"]["question"])
    assert rag.IDK not in fake_model[-1][1]


def test_eval_runs_end_to_end(capsys):
    evaluate.main(["naive", "guarded"])
    out = capsys.readouterr().out
    assert "1. naive" in out and "4. + 'I don't know' guard" in out
