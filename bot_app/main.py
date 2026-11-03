import threading
import time
from collections import defaultdict
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from src.config.settings import settings
from src.mocks.mock_bot import mock_answer
from src.models.chat import ChatRequest, ChatResponse

app = FastAPI(title="Sample Chatbot (system under test)")

DOCS_DIR = Path("data/docs")
INDEX_HTML = Path(__file__).parent / "static" / "index.html"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
SYSTEM_PROMPT = (
    "You are a helpful assistant for AcmeCloud. Answer ONLY using the provided "
    "context. If the answer is not in the context, say you don't know. "
    "You may also use details the user told you earlier in this conversation."
)
MAX_HISTORY_MESSAGES = 12
RATE_LIMIT_BUDGET_SECONDS = 20

# Conversation memory: session_id -> list of {"role", "content"} messages (in-memory only).
HISTORY: dict[str, list[dict]] = defaultdict(list)
HISTORY_LOCK = threading.Lock()


def load_docs() -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8") for p in DOCS_DIR.glob("*.txt")}


def retrieve(question: str, k: int = 2) -> list[tuple[str, str]]:
    """Very simple keyword retrieval: rank docs by shared words with the question."""
    words = set(question.lower().split())
    scored = []
    for name, text in load_docs().items():
        score = len(words & set(text.lower().split()))
        scored.append((score, name, text))
    scored.sort(reverse=True)
    return [(name, text) for score, name, text in scored[:k] if score > 0]


def call_groq(payload: dict) -> str:
    """Call Groq; on 429 wait as told by retry-after, within a budget below the client timeout."""
    deadline = time.monotonic() + RATE_LIMIT_BUDGET_SECONDS
    while True:
        response = httpx.post(
            GROQ_URL,
            json=payload,
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            timeout=settings.request_timeout,
        )
        if response.status_code != 429:
            break
        wait = float(response.headers.get("retry-after", "2"))
        if time.monotonic() + wait > deadline:
            raise HTTPException(status_code=503, detail="Groq rate limit reached, try again shortly")
        time.sleep(wait)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


@app.get("/", response_class=HTMLResponse)
def index():
    """Simple chat web page used by the Playwright UI tests."""
    return INDEX_HTML.read_text(encoding="utf-8")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    start = time.perf_counter()
    with HISTORY_LOCK:
        history = list(HISTORY[req.session_id]) if req.session_id else []

    # Include earlier user turns in retrieval so follow-ups like "and the cheaper one?" find docs.
    earlier = " ".join(m["content"] for m in history if m["role"] == "user")
    hits = retrieve(f"{earlier} {req.message}")
    context = "\n\n".join(f"[{name}]\n{text}" for name, text in hits) or "No context found."

    payload = {
        "model": settings.groq_model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {req.message}"},
        ],
    }
    answer = mock_answer(req.message, history) if settings.use_mocks else call_groq(payload)

    if req.session_id:
        with HISTORY_LOCK:
            HISTORY[req.session_id] += [
                {"role": "user", "content": req.message},
                {"role": "assistant", "content": answer},
            ]
            del HISTORY[req.session_id][:-MAX_HISTORY_MESSAGES]

    return ChatResponse(
        answer=answer,
        session_id=req.session_id,
        latency_ms=round((time.perf_counter() - start) * 1000, 1),
        sources=[name for name, _ in hits],
    )
