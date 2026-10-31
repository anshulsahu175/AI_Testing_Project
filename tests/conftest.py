import httpx
import pytest

from src.clients.chatbot_client import ChatbotClient
from src.models.chat import ChatResponse


@pytest.fixture(scope="session")
def client():
    """One shared HTTP client for the whole test session. Stops early if the bot is down."""
    bot = ChatbotClient()
    try:
        is_up = bot.health()
    except httpx.TransportError:
        is_up = False
    if not is_up:
        bot.close()
        pytest.exit(
            "Bot is not running. Start it with: uvicorn bot_app.main:app --port 8000",
            returncode=1,
        )
    yield bot
    bot.close()


@pytest.fixture(scope="session")
def pricing_response(client) -> ChatResponse:
    """One real chat call reused by schema tests, to save free-tier quota."""
    return client.send("How much does the Pro plan cost?", session_id="schema-test")
