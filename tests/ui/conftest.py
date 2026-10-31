import pytest

from src.pages.chat_page import ChatPage


@pytest.fixture
def chat_page(page, bot_server) -> ChatPage:
    """A fresh browser page with the chat UI already open."""
    return ChatPage(page, base_url=bot_server).open()
