from uuid import uuid4

from src.clients.chatbot_client import ChatbotClient


class Conversation:
    """Sends turns in order under one session_id and keeps the transcript for error messages."""

    def __init__(self, client: ChatbotClient, session_id: str | None = None):
        self.client = client
        self.session_id = session_id or f"conv-{uuid4().hex[:12]}"
        self.turns: list[tuple[str, str]] = []

    def say(self, message: str) -> str:
        answer = self.client.send(message, session_id=self.session_id).answer
        self.turns.append((message, answer))
        return answer

    def transcript(self) -> str:
        return "\n".join(
            f"[{i}] USER: {user}\n    BOT: {bot}" for i, (user, bot) in enumerate(self.turns, 1)
        )
