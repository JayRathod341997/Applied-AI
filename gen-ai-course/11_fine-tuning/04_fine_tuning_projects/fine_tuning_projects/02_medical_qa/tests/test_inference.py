"""
Unit / integration tests for src/inference.py and deploy/app.py

Run (no real model needed — tests use mocking):
  cd fine_tuning_projects/02_medical_qa
  pytest tests/test_inference.py -v
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.inference import MedicalQAInference


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _mock_engine() -> MedicalQAInference:
    """Return a MedicalQAInference instance with mocked model + tokenizer."""
    with patch("src.inference.AutoTokenizer") as mock_tok_cls, \
         patch("src.inference.AutoModelForCausalLM") as mock_model_cls:

        # Tokenizer mock
        tok = MagicMock()
        tok.pad_token = "<pad>"
        tok.eos_token = "</s>"
        tok.pad_token_id = 1
        tok.eos_token_id = 2
        tok.return_value = {"input_ids": MagicMock(shape=(1, 10)), "attention_mask": MagicMock()}
        tok.__call__ = MagicMock(return_value={
            "input_ids": MagicMock(shape=(1, 10)),
            "attention_mask": MagicMock(),
        })
        tok.decode = MagicMock(return_value="Hypertension is high blood pressure.")
        mock_tok_cls.from_pretrained.return_value = tok

        # Model mock
        model = MagicMock()
        model.eval.return_value = model
        # generate returns tensor-like: shape [1, 15]
        import torch
        model.generate = MagicMock(return_value=torch.zeros((1, 15), dtype=torch.long))
        mock_model_cls.from_pretrained.return_value = model

        engine = MedicalQAInference.__new__(MedicalQAInference)
        engine.model_path = "fake/path"
        engine.max_new_tokens = 256
        engine.device = "cpu"
        engine.tokenizer = tok
        engine.model = model

        from transformers import GenerationConfig
        engine.generation_config = GenerationConfig(
            max_new_tokens=256, do_sample=True,
            pad_token_id=1, eos_token_id=2,
        )
        return engine


# ── Prompt builder ─────────────────────────────────────────────────────────────

class TestPromptBuilder:
    def setup_method(self):
        self.engine = _mock_engine()

    def test_prompt_without_context(self):
        prompt = self.engine._build_prompt("What is fever?")
        assert "### Question:\nWhat is fever?" in prompt
        assert "### Response:\n" in prompt
        assert "### Context:" not in prompt

    def test_prompt_with_context(self):
        prompt = self.engine._build_prompt("What is fever?", "Patient is 30yo.")
        assert "### Context:\nPatient is 30yo." in prompt

    def test_prompt_ends_with_response_marker(self):
        prompt = self.engine._build_prompt("Q?")
        assert prompt.endswith("### Response:\n")

    def test_empty_context_treated_as_no_context(self):
        prompt_with = self.engine._build_prompt("Q?", "")
        prompt_without = self.engine._build_prompt("Q?")
        assert prompt_with == prompt_without


# ── FastAPI endpoint tests ────────────────────────────────────────────────────

class TestFastAPIEndpoints:
    """Test the FastAPI routes without loading a real model."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        import deploy.app as app_module
        from fastapi.testclient import TestClient

        # Inject mock engine
        mock_eng = _mock_engine()
        mock_eng.answer = MagicMock(return_value="High blood pressure answer.")
        mock_eng.answer_batch = MagicMock(return_value=["Answer 1", "Answer 2"])
        app_module._engine = mock_eng

        self.client = TestClient(app_module.app)

    def test_health_returns_ok(self):
        resp = self.client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["model_loaded"] is True

    def test_answer_endpoint_success(self):
        resp = self.client.post("/answer", json={
            "question": "What are the symptoms of diabetes?",
            "context": ""
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "latency_ms" in data
        assert data["question"] == "What are the symptoms of diabetes?"

    def test_answer_endpoint_short_question_rejected(self):
        resp = self.client.post("/answer", json={"question": "Hi"})
        assert resp.status_code == 422  # Pydantic min_length=5 validation

    def test_batch_endpoint_success(self):
        resp = self.client.post("/answer/batch", json={
            "questions": ["What is hypertension?", "What is diabetes?"]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["answers"]) == 2

    def test_batch_empty_list_rejected(self):
        resp = self.client.post("/answer/batch", json={"questions": []})
        assert resp.status_code == 422

    def test_model_info_endpoint(self):
        resp = self.client.get("/model/info")
        assert resp.status_code == 200
        data = resp.json()
        assert "model_path" in data
        assert "device" in data

    def test_answer_when_engine_none(self):
        import deploy.app as app_module
        from fastapi.testclient import TestClient
        app_module._engine = None
        client = TestClient(app_module.app)
        resp = client.post("/answer", json={"question": "What is fever exactly?"})
        assert resp.status_code == 503
