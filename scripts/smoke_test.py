from src.clients.chatbot_client import ChatbotClient


def main():
    client = ChatbotClient()
    assert client.health(), "Bot is not running. Start it with uvicorn first."
    result = client.send("How much does the Pro plan cost?")
    print("ANSWER :", result.answer)
    print("SOURCES:", result.sources)
    print("LATENCY:", result.latency_ms, "ms")
    client.close()


if __name__ == "__main__":
    main()
