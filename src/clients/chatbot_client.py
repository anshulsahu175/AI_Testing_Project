import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config.settings import settings
from src.models.chat import ChatRequest, ChatResponse
from src.utils.logger import get_logger

log = get_logger(__name__)

_retry_network = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=8),
    retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
    reraise=True,
)


class ChatbotClient:
    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        self._client = httpx.Client(
            base_url=base_url or settings.bot_base_url,
            timeout=timeout or settings.request_timeout,
        )

    @_retry_network
    def send_raw(self, payload: dict) -> httpx.Response:
        """Send any payload as-is. Used for negative tests (empty or invalid input)."""
        log.info("POST /chat payload=%s", payload)
        return self._client.post("/chat", json=payload)

    def send(self, message: str, session_id: str | None = None) -> ChatResponse:
        """Send a valid message and return a validated ChatResponse."""
        request = ChatRequest(message=message, session_id=session_id)
        response = self.send_raw(request.model_dump())
        response.raise_for_status()
        return ChatResponse.model_validate(response.json())

    def health(self) -> bool:
        return self._client.get("/health").status_code == 200

    def close(self) -> None:
        self._client.close()
