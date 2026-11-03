import subprocess
import sys
import time

import httpx
import pytest

from src.clients.chatbot_client import ChatbotClient
from src.clients.judge_client import GeminiClient
from src.config.settings import settings
from src.evaluators.judge import Judge
from src.mocks.mock_judge import MockJudgeClient
from src.models.chat import ChatResponse
from src.utils.cache import DiskCache

BOT_STARTUP_SECONDS = 30


def _bot_is_up(base_url: str) -> bool:
    try:
        return httpx.get(f"{base_url}/health", timeout=2).status_code == 200
    except httpx.TransportError:
        return False


@pytest.fixture(scope="session")
def bot_server(worker_id):
    """Use the bot if it is already running, otherwise start it for this test session.

    With pytest-xdist (-n 2) each worker gets its own bot port: gw0 -> 8000, gw1 -> 8001.
    With BOT_AUTOSTART=false (docker compose) every worker uses BOT_BASE_URL as it is.
    """
    if not settings.bot_autostart:
        if not _bot_is_up(settings.bot_base_url):
            pytest.exit(f"Bot is not reachable at {settings.bot_base_url}", returncode=1)
        yield settings.bot_base_url
        return

    url = httpx.URL(settings.bot_base_url)
    port = (url.port or 8000) + (int(worker_id[2:]) if worker_id.startswith("gw") else 0)
    base_url = f"{url.scheme}://{url.host}:{port}"
    if _bot_is_up(base_url):
        yield base_url
        return

    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "bot_app.main:app", "--host", url.host, "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + BOT_STARTUP_SECONDS
    while not _bot_is_up(base_url):
        if process.poll() is not None or time.monotonic() > deadline:
            process.kill()
            pytest.exit(
                f"Bot could not be started. Try it by hand: uvicorn bot_app.main:app --port {port}",
                returncode=1,
            )
        time.sleep(0.5)

    yield base_url
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
def judge(tmp_path_factory):
    """LLM judge backed by Gemini (cached in .cache/judge), or the offline mock judge."""
    if settings.use_mocks:
        yield Judge(MockJudgeClient(), DiskCache(tmp_path_factory.mktemp("judge-cache")))
        return
    gemini = GeminiClient()
    yield Judge(gemini)
    gemini.close()
