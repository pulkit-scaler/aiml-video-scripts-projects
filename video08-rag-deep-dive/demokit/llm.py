"""One place that talks to the model (Groq), plus local embeddings.

Every demo call goes through generate_json() or generate_text(), and embed(). Two things make shoot day safe:

* Replay cache. Each answer is saved under .cache/llm/ in this folder (keyed by model, prompt
  and schema). Run the demo once the day before; on camera the same command replays the
  exact same answers instantly, with no network and no surprises.
  Set DEMO_CACHE=off, or pass fresh=True, to force a live call.
* One model setting. MODEL in .env changes the model for this demo.
* Embeddings run on this machine (fastembed), so Groq is the only API key needed.
"""

import hashlib
import json
import os
import re
import time
import threading
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # this video's folder
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_MODEL = "openai/gpt-oss-120b"
CACHE_DIR = Path(os.getenv("DEMO_CACHE_DIR") or PROJECT_ROOT / ".cache" / "llm")


def model_name() -> str:
    return os.getenv("MODEL") or DEFAULT_MODEL


def get_client():
    """A Groq client. Reads GROQ_API_KEY from the environment or .env."""
    from groq import Groq
    return Groq()


def wait_seconds(err) -> float:
    """How long Groq asks us to wait after a rate-limit error ("try again in 1m2.5s")."""
    header = err.response.headers.get("retry-after") if getattr(err, "response", None) is not None else None
    if header:
        return float(header)
    match = re.search(r"try again in (?:(\d+)m)?([\d.]+)s", str(err))
    return int(match.group(1) or 0) * 60 + float(match.group(2)) if match else 5.0


def complete(client, **kwargs):
    """One chat completion. On Groq's free-tier rate limit, wait as long as Groq asks and try again."""
    from groq import RateLimitError
    for _ in range(30):
        try:
            return client.chat.completions.create(**kwargs)
        except RateLimitError as err:
            seconds = wait_seconds(err)
            if seconds > 120:  # the daily budget is used up: waiting a minute won't help
                raise SystemExit(f"Groq's daily limit for {kwargs.get('model')} is used up. Try again in "
                                 f"{seconds / 60:.0f} minutes, or set MODEL in .env to another model.") from err
            time.sleep(seconds + 0.5)
    return client.chat.completions.create(**kwargs)


def _reasoning(model: str) -> dict:
    """gpt-oss thinks before it answers; "low" keeps that short, so calls stay fast and cheap."""
    return {"reasoning_effort": "low"} if model.startswith("openai/gpt-oss") else {}


def _messages(prompt: str, system: str) -> list[dict]:
    return ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]


def _cache_on() -> bool:
    return os.getenv("DEMO_CACHE", "on").lower() not in {"off", "0", "false", "no"}


def _key(*parts) -> str:
    raw = json.dumps(parts, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _cached(key: str, fresh: bool, call):
    path = CACHE_DIR / f"{key}.json"
    if _cache_on() and not fresh and path.exists():
        return json.loads(path.read_text())["value"]
    value = call()
    if _cache_on():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"value": value}, ensure_ascii=False, indent=1))
    return value


def tidy(text: str) -> str:
    """Plain characters for the terminal and for scoring: gpt-oss likes narrow no-break spaces
    ("30\u202fdays"), non-breaking hyphens, curly quotes and **bold** markdown."""
    for odd, plain in {"\u202f": " ", "\u00a0": " ", "\u2011": "-", "\u2010": "-", "\u2013": "-",
                       "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "**": ""}.items():
        text = text.replace(odd, plain)
    # "10 %" became "10 %" above. Join it back, so "10%" scores as correct and reads cleanly.
    return re.sub(r"(\d) %", r"\1%", text)


def generate_text(prompt: str, system: str = "", *, temperature: float = 0.0, fresh: bool = False) -> str:
    """Plain text answer."""
    model = model_name()

    def call():
        response = complete(
            get_client(),
            model=model, messages=_messages(prompt, system), temperature=temperature, **_reasoning(model))
        return response.choices[0].message.content.strip()

    return tidy(_cached(_key("text", model, system, prompt, temperature), fresh, call))


def generate_json(prompt: str, schema: dict, system: str = "", *, temperature: float = 0.0,
                  fresh: bool = False) -> dict:
    """JSON answer that must match `schema` (Groq structured output, strict mode)."""
    model = model_name()

    def call():
        response = complete(
            get_client(),
            model=model,
            messages=_messages(prompt, system),
            temperature=temperature,
            response_format={"type": "json_schema",
                             "json_schema": {"name": "answer", "strict": True, "schema": schema}},
            **_reasoning(model),
        )
        return json.loads(response.choices[0].message.content)

    return _cached(_key("json", model, system, prompt, schema, temperature), fresh, call)


# Embeddings run locally: Groq has no embeddings API, and this needs no key.
# The model (about 210 MB) downloads once into .cache/fastembed/ on first use.
# bge-base was picked over the smaller bge-small because only bge-base put the Enterprise SLA
# in the top 3 for beat 3's question ("What uptime does the Enterprise plan guarantee?").
_embedder = None
_embedder_lock = threading.Lock()  # the demo embeds from several threads at once


def embed_model_name() -> str:
    return os.getenv("EMBED_MODEL") or "BAAI/bge-base-en-v1.5"


def _load_embedder():
    global _embedder
    with _embedder_lock:
        if _embedder is None:
            from fastembed import TextEmbedding
            _embedder = TextEmbedding(model_name=embed_model_name(),
                                      cache_dir=str(PROJECT_ROOT / ".cache" / "fastembed"))
    return _embedder


def embed(texts: list[str], task: str = "RETRIEVAL_DOCUMENT", *, fresh: bool = False) -> list[list[float]]:
    """One embedding vector per text. task: RETRIEVAL_DOCUMENT (a chunk) or RETRIEVAL_QUERY (a question)."""
    model = embed_model_name()
    vectors = []
    for text in texts:
        def call(text=text):
            embedder = _load_embedder()
            run = embedder.query_embed if task == "RETRIEVAL_QUERY" else embedder.passage_embed
            return [float(x) for x in next(iter(run([text])))]
        vectors.append(_cached(_key("embed", model, task, text), fresh, call))
    return vectors
