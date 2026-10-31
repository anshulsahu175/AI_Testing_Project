import pytest
from playwright.sync_api import expect

from src.evaluators.reference import fact_coverage
from src.evaluators.rules import contains_any

pytestmark = pytest.mark.ui


def test_page_loads_with_empty_chat(chat_page):
    expect(chat_page.page).to_have_title("AcmeCloud Assistant")
    expect(chat_page.input).to_be_visible()
    expect(chat_page.bot_messages).to_have_count(0)


def test_send_button_disabled_for_blank_input(chat_page):
    expect(chat_page.send_button).to_be_disabled()
    chat_page.input.fill("   ")
    expect(chat_page.send_button).to_be_disabled()
    chat_page.input.fill("Hello")
    expect(chat_page.send_button).to_be_enabled()


def test_question_gets_answer_in_ui(chat_page):
    answer = chat_page.ask("How much does the Pro plan cost?")

    expect(chat_page.user_messages.last).to_contain_text("Pro plan")
    expect(chat_page.input).to_have_value("")
    result = contains_any(answer, ["12"])
    assert result, f"{result.detail}\nANSWER: {answer}"


def test_two_messages_get_two_answers(chat_page):
    chat_page.ask("How much storage does the Free plan include?")
    chat_page.ask("What is the support email?")

    expect(chat_page.user_messages).to_have_count(2)
    expect(chat_page.bot_messages).to_have_count(2)
    assert "support@acmecloud.example" in chat_page.get_last_answer().lower()


def test_ui_answer_matches_api_answer(chat_page, client):
    question = "Which operating systems does the desktop app run on?"
    facts = [["Windows"], ["macOS", "mac"], ["Linux"]]

    ui_answer = chat_page.ask(question)
    api_response = client.send(question)

    # LLM wording differs per call, so compare facts and sources, not exact text.
    assert chat_page.get_last_sources() == api_response.sources
    ui_facts = fact_coverage(ui_answer, facts)
    api_facts = fact_coverage(api_response.answer, facts)
    assert ui_facts.score == api_facts.score == 1.0, (
        f"UI: {ui_facts.detail} | API: {api_facts.detail}\n"
        f"UI ANSWER: {ui_answer}\nAPI ANSWER: {api_response.answer}"
    )
