import time
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from src.config.settings import settings
from src.models.chat import ChatRequest, ChatResponse

app = FastAPI(title="Sample Chatbot (system under test)")

DOCS_DIR = Path("data/docs")
INDEX_HTML = Path(__file__).parent / "static" / "index.html"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
SYSTEM_PROMPT = (
    "You are a helpful assistant for AcmeCloud. Answer ONLY using the provided "
    "context. If the answer is not in the context, say you don't know."
)


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
    hits = retrieve(req.message)
    context = "\n\n".join(f"[{name}]\n{text}" for name, text in hits) or "No context found."

    payload = {
        "model": settings.groq_model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {req.message}"},
        ],
    }
    response = httpx.post(
        GROQ_URL,
        json=payload,
        headers={"Authorization": f"Bearer {settings.groq_api_key}"},
        timeout=settings.request_timeout,
    )
    response.raise_for_status()
    answer = response.json()["choices"][0]["message"]["content"]

    return ChatResponse(
        answer=answer,
        session_id=req.session_id,
        latency_ms=round((time.perf_counter() - start) * 1000, 1),
        sources=[name for name, _ in hits],
    )
