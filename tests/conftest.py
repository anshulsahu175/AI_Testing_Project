import subprocess
import sys
import time

import httpx
import pytest

from src.clients.chatbot_client import ChatbotClient
from src.clients.judge_client import GeminiClient
from src.config.settings import settings
from src.evaluators.judge import Judge
from src.models.chat import ChatResponse

BOT_STARTUP_SECONDS = 30


def _bot_is_up() -> bool:
    try:
        return httpx.get(f"{settings.bot_base_url}/health", timeout=2).status_code == 200
    except httpx.TransportError:
        return False


@pytest.fixture(scope="session")
def bot_server():
    """Use the bot if it is already running, otherwise start it for this test session."""
    if _bot_is_up():
        yield settings.bot_base_url
        return

    url = httpx.URL(settings.bot_base_url)
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "bot_app.main:app",
         "--host", url.host, "--port", str(url.port or 8000)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + BOT_STARTUP_SECONDS
    while not _bot_is_up():
        if process.poll() is not None or time.monotonic() > deadline:
            process.kill()
            pytest.exit(
                "Bot could not be started. Try it by hand: uvicorn bot_app.main:app --port 8000",
                returncode=1,
            )
        time.sleep(0.5)

    yield settings.bot_base_url
    process.terminate()
    process.wait(timeout=10)


@pytest.fixture(scope="session")
def client(bot_server):
    """One shared HTTP client for the whole test session."""
    bot = ChatbotClient(base_url=bot_server)
    yield bot
    bot.close()


@pytest.fixture(scope="session")
def pricing_response(client) -> ChatResponse:
    """One real chat call reused by schema tests, to save free-tier quota."""
    return client.send("How much does the Pro plan cost?", session_id="schema-test")


@pytest.fixture(scope="session")
def judge():
    """LLM judge backed by Gemini. Results are cached on disk in .cache/judge."""
    gemini = GeminiClient()
    yield Judge(gemini)
    gemini.close()
