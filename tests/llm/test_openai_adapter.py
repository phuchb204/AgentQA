import json
from types import SimpleNamespace

import pytest

from agentqa.llm.openai_adapter import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    ActionDecision,
    LLMFormatError,
    OpenAICompatAdapter,
    _extract_json,
    _to_action,
)


class _StubCompletions:
    def __init__(self, content: str):
        self.content = content
        self.last_kwargs = None

    async def create(self, **kwargs):
        self.last_kwargs = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))],
            usage=SimpleNamespace(prompt_tokens=11, completion_tokens=7),
        )


def _build_adapter(content: str):
    adapter = OpenAICompatAdapter(base_url="http://stub", api_key="k", model="m1")
    stub = _StubCompletions(content)
    adapter._client = SimpleNamespace(chat=SimpleNamespace(completions=stub))
    return adapter, stub


async def test_decide_parses_plain_json_and_usage():
    payload = json.dumps({"type": "click", "target": "#add-btn", "value": "", "rationale": "vì cần thêm"})
    adapter, stub = _build_adapter(payload)
    result = await adapter.decide("sys", "usr")
    assert result.action.type == "click"
    assert result.action.target == "#add-btn"
    assert result.action.value is None
    assert result.input_tokens == 11
    assert result.output_tokens == 7
    assert stub.last_kwargs["model"] == "m1"
    assert stub.last_kwargs["messages"][0] == {"role": "system", "content": "sys"}
    assert stub.last_kwargs["messages"][1] == {"role": "user", "content": "usr"}


async def test_decide_parses_fenced_json():
    content = 'Đây là hành động:\n```json\n{"type": "finish"}\n```'
    adapter, _ = _build_adapter(content)
    result = await adapter.decide("sys", "usr")
    assert result.action.type == "finish"


async def test_decide_raises_format_error_on_garbage():
    adapter, _ = _build_adapter("không có JSON ở đây")
    with pytest.raises(LLMFormatError):
        await adapter.decide("sys", "usr")


def test_extract_json_rejects_missing_object():
    with pytest.raises(LLMFormatError):
        _extract_json("xyz")


def test_to_action_maps_empty_strings_to_none():
    action = _to_action(ActionDecision(type="navigate", target="http://x", value="", rationale=""))
    assert action.target == "http://x"
    assert action.value is None


def test_from_env_reads_zen_defaults(monkeypatch):
    monkeypatch.setenv("AGENTQA_LLM_API_KEY", "test-key")
    monkeypatch.delenv("AGENTQA_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("AGENTQA_LLM_MODEL", raising=False)
    adapter = OpenAICompatAdapter.from_env()
    assert adapter.model == DEFAULT_MODEL
    assert DEFAULT_BASE_URL == "https://opencode.ai/zen/v1"


def test_from_env_requires_key_for_remote(monkeypatch):
    monkeypatch.delenv("AGENTQA_LLM_API_KEY", raising=False)
    monkeypatch.setenv("AGENTQA_LLM_BASE_URL", "https://opencode.ai/zen/v1")
    with pytest.raises(RuntimeError):
        OpenAICompatAdapter.from_env()


def test_from_env_allows_missing_key_for_localhost(monkeypatch):
    monkeypatch.delenv("AGENTQA_LLM_API_KEY", raising=False)
    monkeypatch.setenv("AGENTQA_LLM_BASE_URL", "http://localhost:11434/v1")
    adapter = OpenAICompatAdapter.from_env()
    assert adapter.model == DEFAULT_MODEL
