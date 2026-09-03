from app.agent import sarjy_agent
from app.agent.sarjy_agent import build_agent


def test_model_override_wins_over_settings_default(monkeypatch):
    monkeypatch.setattr(sarjy_agent.settings, "llm_model", "default-model")
    agent = build_agent([], mcp_ready=False, model="requested-model")
    assert agent.model == "requested-model"


def test_missing_model_falls_back_to_settings_default(monkeypatch):
    monkeypatch.setattr(sarjy_agent.settings, "llm_model", "default-model")
    agent = build_agent([], mcp_ready=False)
    assert agent.model == "default-model"


def test_guardrail_is_attached_by_default(monkeypatch):
    monkeypatch.setattr(sarjy_agent.settings, "input_guardrail_enabled", True)
    agent = build_agent([], mcp_ready=False)
    assert [g.get_name() for g in agent.input_guardrails] == ["sarjy_input_guardrail"]


def test_guardrail_switch_off_removes_it(monkeypatch):
    monkeypatch.setattr(sarjy_agent.settings, "input_guardrail_enabled", False)
    agent = build_agent([], mcp_ready=False)
    assert agent.input_guardrails == []
