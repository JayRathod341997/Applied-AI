from ecommerce_ft.data import build_prompt, normalize_text


def test_normalize_text() -> None:
    assert normalize_text("  delayed   shipment  update ") == "delayed shipment update"


def test_build_prompt_without_context() -> None:
    prompt = build_prompt("Where is my order?")
    assert "### Customer Query:" in prompt
    assert "### Agent Response:" in prompt
    assert "### Product/Order Context:" not in prompt


def test_build_prompt_with_context() -> None:
    prompt = build_prompt("Can I return it?", "Order delivered yesterday")
    assert "### Product/Order Context:" in prompt
    assert "Order delivered yesterday" in prompt

