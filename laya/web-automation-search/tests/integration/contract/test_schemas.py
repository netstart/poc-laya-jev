from __future__ import annotations

"""Testes de contrato para schemas Pydantic e provedores de modelo."""

import pytest
from pydantic import ValidationError

from laya_ultrafast.config.settings import LAYAConfig
from laya_ultrafast.model import AgentAction, create_model_client


class TestAgentAction:
    """Testes para schema AgentAction."""

    def test_click_action_valid(self):
        action = AgentAction(action="CLICK", target_id="btn-1", selector="button#btn")
        assert action.action == "CLICK"
        assert action.target_id == "btn-1"
        assert action.is_valid()

    def test_type_text_action_valid(self):
        action = AgentAction(
            action="TYPE_TEXT",
            target_id="input-1",
            selector="input#txt",
            value="hello world",
        )
        assert action.is_valid()

    def test_select_action_valid(self):
        action = AgentAction(
            action="SELECT",
            target_id="select-1",
            selector="select#lang",
            value="pt-BR",
        )
        assert action.is_valid()

    def test_scroll_down_valid(self):
        action = AgentAction(action="SCROLL_DOWN", direction="down", amount=300)
        assert action.is_valid()

    def test_done_action_valid(self):
        action = AgentAction(action="DONE")
        assert action.is_valid()

    def test_blocked_action_valid(self):
        action = AgentAction(action="BLOCKED", value="Goal not achievable")
        assert action.is_valid()

    def test_click_without_target_invalid(self):
        action = AgentAction(action="CLICK")
        assert not action.is_valid()

    def test_type_text_without_value_invalid(self):
        action = AgentAction(action="TYPE_TEXT", target_id="input-1")
        assert not action.is_valid()

    def test_invalid_action_type(self):
        with pytest.raises(ValidationError):
            AgentAction(action="INVALID_ACTION")

    def test_invalid_direction(self):
        with pytest.raises(ValidationError):
            AgentAction(action="SCROLL_UP", direction="left", amount=100)

    def test_invalid_url(self):
        with pytest.raises(ValidationError):
            AgentAction(action="NAVIGATE", url="not-a-url")

    def test_valid_url(self):
        action = AgentAction(action="NAVIGATE", url="https://example.com")
        assert action.is_valid()


class TestModelFactory:
    """Testes para factory de modelos."""

    def test_create_ollama_client(self):
        config = LAYAConfig(model_provider="ollama", model_name="llama3.1:8b-instruct-q4_K_M")
        client = create_model_client(config)
        assert client.__class__.__name__ == "OllamaClient"

    def test_create_openai_client(self):
        config = LAYAConfig(model_provider="openai", model_name="gpt-4")
        client = create_model_client(config)
        assert client.__class__.__name__ == "OpenAICompatibleClient"

    def test_create_local_client(self):
        config = LAYAConfig(model_provider="local", model_name="model.gguf")
        client = create_model_client(config)
        assert client.__class__.__name__ == "LlamaCppClient"

    def test_invalid_provider_raises(self):
        config = LAYAConfig(model_provider="ollama", model_name="test")
        config.__dict__["model_provider"] = "invalid_provider"
        with pytest.raises(Exception):
            create_model_client(config)


class TestSettings:
    """Testes para configurações."""

    def test_default_config(self):
        config = LAYAConfig()
        assert config.model_provider == "ollama"
        assert config.model_name == "llama3.1:8b-instruct-q4_K_M"
        assert config.max_steps == 25
        assert config.browser_headless is True

    def test_config_from_env(self, monkeypatch):
        monkeypatch.setenv("LAYA_MODEL_NAME", "mistral:7b-instruct-q4_K_M")
        monkeypatch.setenv("LAYA_MAX_STEPS", "50")
        config = LAYAConfig()
        assert config.model_name == "mistral:7b-instruct-q4_K_M"
        assert config.max_steps == 50

    def test_invalid_temperature(self):
        with pytest.raises(ValidationError):
            LAYAConfig(model_temperature=5.0)

    def test_invalid_max_steps(self):
        with pytest.raises(ValidationError):
            LAYAConfig(max_steps=0)

    def test_invalid_provider(self):
        with pytest.raises(ValidationError):
            LAYAConfig(model_provider="invalid")


class TestQuestions:
    """Testes para prompts e parsing."""

    def test_build_prompt_contains_goal(self):
        from laya_ultrafast.questions import build_prompt
        from laya_ultrafast.utils.dom import ElementSnapshot
        
        snapshot = [
            ElementSnapshot(
                id="btn-1", index=0, tag="button", role="button",
                label="Submit", selector="button#submit",
                bbox={"x": 0, "y": 0, "width": 100, "height": 40},
                attrs={}, state={}, is_visible=True,
                is_obstructed=False, is_interactive=True, is_editable=False,
            )
        ]
        prompt = build_prompt(snapshot, "Test goal", history=[])
        assert "Test goal" in prompt
        assert "Submit" in prompt

    def test_parse_action_response_valid_json(self):
        from laya_ultrafast.questions import parse_action_response
        raw = '{"action": "CLICK", "target_id": "btn-1", "selector": "button#btn"}'
        result = parse_action_response(raw)
        assert result["action"] == "CLICK"
        assert result["target_id"] == "btn-1"

    def test_parse_action_response_with_extra_text(self):
        from laya_ultrafast.questions import parse_action_response
        raw = 'Here is the action: {"action": "DONE"}'
        result = parse_action_response(raw)
        assert result["action"] == "DONE"

    def test_validate_action_response_valid(self):
        from laya_ultrafast.questions import validate_action_response
        valid, error = validate_action_response({
            "action": "CLICK",
            "target_id": "btn-1",
            "selector": "button#btn",
        })
        assert valid
        assert error is None

    def test_validate_action_response_invalid(self):
        from laya_ultrafast.questions import validate_action_response
        valid, error = validate_action_response({
            "action": "CLICK",
        })
        assert not valid
        assert error is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])