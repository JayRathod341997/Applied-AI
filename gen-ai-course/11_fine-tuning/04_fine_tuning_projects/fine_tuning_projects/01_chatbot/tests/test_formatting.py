from chatbot_ft.data import build_prompt, normalize_text


def test_normalize_text() -> None:
    assert normalize_text("  hello   world  ") == "hello world"


def test_build_prompt_without_input() -> None:
    prompt = build_prompt("Explain overfitting.")
    assert "### Instruction:" in prompt
    assert "### Response:" in prompt
    assert "### Input:" not in prompt


def test_build_prompt_with_input() -> None:
    prompt = build_prompt("Summarize", "This is some input")
    assert "### Input:" in prompt
    assert "This is some input" in prompt

