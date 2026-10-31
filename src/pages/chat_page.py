from playwright.sync_api import Page, expect

from src.config.settings import settings


class ChatPage:
    """Page Object for the bot's chat web page. Tests talk to this, never to raw selectors."""

    def __init__(self, page: Page, base_url: str | None = None):
        self.page = page
        self.base_url = (base_url or settings.bot_base_url).rstrip("/")
        self.input = page.get_by_test_id("message-input")
        self.send_button = page.get_by_test_id("send-button")
        self.user_messages = page.get_by_test_id("user-message")
        self.bot_messages = page.get_by_test_id("bot-message")
        self.error = page.get_by_test_id("error-message")
        self._expected_answers = 0

    def open(self) -> "ChatPage":
        self.page.goto(f"{self.base_url}/")
        expect(self.input).to_be_visible()
        self._expected_answers = self.bot_messages.count()
        return self

    def send_message(self, text: str) -> None:
        self.input.fill(text)
        self.send_button.click()
        self._expected_answers += 1

    def wait_for_answer(self, timeout_ms: float | None = None) -> None:
        """Auto-wait until the bot reply for the last sent message is on the page."""
        timeout = timeout_ms or settings.request_timeout * 1000
        expect(self.bot_messages).to_have_count(self._expected_answers, timeout=timeout)

    def get_last_answer(self) -> str:
        return self.bot_messages.last.get_by_test_id("message-text").inner_text()

    def get_last_sources(self) -> list[str]:
        text = self.bot_messages.last.get_by_test_id("message-sources").inner_text()
        return [s.strip() for s in text.split(",") if s.strip()]

    def ask(self, text: str) -> str:
        """Send a message, wait for the reply, and return it."""
        self.send_message(text)
        self.wait_for_answer()
        return self.get_last_answer()
