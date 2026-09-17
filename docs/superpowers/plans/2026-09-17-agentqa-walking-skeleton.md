# AgentQA Walking Skeleton (W1–W2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dựng walking skeleton của AgentQA — 1 test case tiếng Việt chạy end-to-end qua Chromium bằng LLM thật (OpenAI-compatible), trả về PASS/FAIL + trace JSON, kèm CI xanh, chạy trên máy cả 3 thành viên.

**Architecture:** Monorepo một package Python (`src/agentqa/`) với 6 lớp: `contracts` (Pydantic models đóng băng, là hợp đồng giữa 3 workstream) → `llm` (adapter OpenAI-compatible + FakeLLM) → `agent` (observe → LLM decide → Playwright execute) và `verify` (assertion checker) → `platform` (ghi trace) → `cli` (entry point). `apps/demo-site` là web app tĩnh làm đối tượng test, có script sinh UI variants. Ranh giới lớp được enforce bằng import-linter trong CI.

**Tech Stack:** Python 3.12 · uv · pydantic v2 · openai SDK (base_url override — chạy được DeepSeek/Zen/Gemini-compat/OpenRouter/Ollama) · Playwright Chromium (async) · pytest + pytest-asyncio · ruff · import-linter · GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-17-agentqa-workstream-design.md`

## Global Constraints

- Python >= 3.12. Mọi lệnh chạy qua `uv run` (hoặc `uv sync` trước). Script phải chạy trên Windows (máy dev) lẫn Linux (CI) — dùng `pathlib`, không hardcode path.
- Dependencies: `openai>=1.0`, `playwright>=1.48`, `pydantic>=2.7`, `pyyaml>=6.0`. Dev: `pytest>=8`, `pytest-asyncio>=0.24`, `ruff>=0.6`, `import-linter>=2.0`.
- LLM mặc định: `AGENTQA_LLM_BASE_URL=https://opencode.ai/zen/v1`, `AGENTQA_LLM_MODEL=deepseek-v4-flash`, key ở `AGENTQA_LLM_API_KEY`. **Không import `anthropic`** — toàn bộ đi qua `openai` SDK + base_url.
- **Cấm gọi LLM API thật trong test/CI** — test chỉ dùng `FakeLLM` hoặc stub client. Gọi API thật chỉ khi chạy tay.
- Luật import (enforce bằng import-linter): `contracts` là lá (không import module nào khác trong `agentqa`); `llm` chỉ import `contracts`; `agent`, `verify` chỉ import `contracts` + `llm`; `platform`, `cli` được import tất cả. `agent` và `verify` không import nhau.
- `contracts` v1 đóng băng sau Task 4: mọi thay đổi phải PR + review + bump version.
- Hằng số: `MAX_OBSERVATION_BYTES = 8192`; `TestCase.max_steps` mặc định 20.
- Action semantics: `navigate` → `target` là URL; `click` → `target` là selector Playwright; `fill` → `target` selector + `value` nội dung; `finish` kết thúc loop.
- Ngôn ngữ: code/commit/test name/comment-free — tiếng Anh; UI demo-site + goal kịch bản — tiếng Việt.
- Commit theo Conventional Commits, prefix `feat|fix|chore|docs|test` + scope (ví dụ `feat(contracts): ...`).

## Ownership map (ai làm task nào)

| Task | Owner gợi ý | Ghi chú |
|---|---|---|
| 1, 2, 11, 12, 13, 14 | W3 (integration owner) | hạ tầng, CI, CLI, docs |
| 3, 4 | cả nhóm | 2 buổi sync ngắn để chốt contracts trước khi merge |
| 5, 7, 8, 10 | W1 | lớp agent + LLM |
| 6, 9 | W2 | demo-site, variants, checker |

---

### Task 1: Bootstrap repo & tooling

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `README.md`
- Create: `src/agentqa/__init__.py`
- Create: `src/agentqa/contracts/__init__.py` (rỗng, sẽ điền ở Task 3–4); `src/agentqa/llm/__init__.py`; `src/agentqa/agent/__init__.py`; `src/agentqa/verify/__init__.py`; `src/agentqa/platform/__init__.py`

- [ ] **Step 1: Tạo `pyproject.toml`**

```toml
[project]
name = "agentqa"
version = "0.1.0"
description = "AI-agent web testing platform (graduation project)"
requires-python = ">=3.12"
dependencies = [
    "openai>=1.0",
    "playwright>=1.48",
    "pydantic>=2.7",
    "pyyaml>=6.0",
]

[project.scripts]
agentqa = "agentqa.cli:main"

[dependency-groups]
dev = [
    "pytest>=8",
    "pytest-asyncio>=0.24",
    "ruff>=0.6",
    "import-linter>=2.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.importlinter]
root_packages = ["agentqa"]

[[tool.importlinter.contracts]]
name = "contracts is a leaf"
type = "forbidden"
source_modules = ["agentqa.contracts"]
forbidden_modules = ["agentqa.llm", "agentqa.agent", "agentqa.verify", "agentqa.platform", "agentqa.cli"]

[[tool.importlinter.contracts]]
name = "llm depends only on contracts"
type = "forbidden"
source_modules = ["agentqa.llm"]
forbidden_modules = ["agentqa.agent", "agentqa.verify", "agentqa.platform", "agentqa.cli"]

[[tool.importlinter.contracts]]
name = "agent depends only on contracts and llm"
type = "forbidden"
source_modules = ["agentqa.agent"]
forbidden_modules = ["agentqa.verify", "agentqa.platform", "agentqa.cli"]

[[tool.importlinter.contracts]]
name = "verify depends only on contracts and llm"
type = "forbidden"
source_modules = ["agentqa.verify"]
forbidden_modules = ["agentqa.agent", "agentqa.platform", "agentqa.cli"]
```

- [ ] **Step 2: Tạo `.gitignore`**

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.env
experiments/runs/
apps/demo-site/variants/*
!apps/demo-site/variants/.gitkeep
node_modules/
playwright-report/
```

- [ ] **Step 3: Tạo `.env.example`**

```
AGENTQA_LLM_API_KEY=
AGENTQA_LLM_BASE_URL=https://opencode.ai/zen/v1
AGENTQA_LLM_MODEL=deepseek-v4-flash
# Alternatives:
# DeepSeek direct: base_url=https://api.deepseek.com, model=deepseek-v4-flash
# OpenRouter:      base_url=https://openrouter.ai/api/v1
# Gemini compat:   base_url=https://generativelanguage.googleapis.com/v1beta/openai/
# Ollama local:    base_url=http://localhost:11434/v1, model tuỳ máy, key bỏ trống
```

- [ ] **Step 4: Tạo `README.md` ngắn + các file `__init__.py` rỗng**

`README.md` nội dung: tên dự án, 1 câu mô tả, trỏ tới `docs/runbooks/dev-setup.md`, lệnh test (`uv run pytest`), lệnh chạy 1 case (`uv run agentqa run --case experiments/cases/login_todo.yaml --base-url <url>`).

Tạo `src/agentqa/__init__.py` với `__version__ = "0.1.0"` và 5 file `__init__.py` rỗng trong `contracts/`, `llm/`, `agent/`, `verify/`, `platform/`.

- [ ] **Step 5: Sync & verify**

Run: `uv sync; uv run ruff check .; uv run lint-imports; uv run python -c "import agentqa; print(agentqa.__version__)"`
Expected: sync OK, ruff "All checks passed", lint-imports "Contracts: 4 kept, 0 broken", in ra `0.1.0`.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .gitignore .env.example README.md src
git commit -m "chore: bootstrap agentqa package with uv, ruff, pytest, import-linter"
```

---

### Task 2: GitHub remote, CODEOWNERS, branch protection

**Files:**
- Create: `CODEOWNERS`

**Interfaces:**
- Produces: repo remote `origin` với `main` được bảo vệ — mọi task sau đi qua PR.

- [ ] **Step 1: Tạo `CODEOWNERS`** (thay 3 handle thật của nhóm vào trước khi commit)

```
/src/agentqa/contracts/  @w1-handle @w2-handle @w3-handle
/src/agentqa/llm/        @w1-handle
/src/agentqa/agent/      @w1-handle
/src/agentqa/verify/     @w2-handle
/src/agentqa/platform/   @w3-handle
/src/agentqa/api/        @w3-handle
/apps/demo-site/         @w2-handle
/experiments/rq1/        @w1-handle
/experiments/rq2/        @w2-handle
/experiments/rq3/        @w3-handle
/.github/                @w3-handle
/infra/                  @w3-handle
```

- [ ] **Step 2: Tạo repo private + push**

Run:
```bash
git add CODEOWNERS; git commit -m "chore: add CODEOWNERS mapping workstreams to paths"
gh repo create agentqa --private --source . --push
```
Nếu máy chưa có `gh` (hoặc chưa login): tạo repo private trên github.com bằng tay, rồi `git remote add origin <url>; git push -u origin main`.

- [ ] **Step 3: Bật branch protection cho `main`** (làm trên GitHub web: Settings → Rules → Rulesets → New ruleset → Target: main)

Bật: Require a pull request before merging (1 approval), Require status checks to pass (sẽ chọn check CI ở Task 13), Block force pushes.

- [ ] **Step 4: Verify**

Run: `git remote -v; git log --oneline -3`
Expected: có `origin`, 2 commit gần nhất là bootstrap + CODEOWNERS.

---

### Task 3: Contracts v1 — core models (observation / action / step)

**Files:**
- Create: `src/agentqa/contracts/core.py`
- Modify: `src/agentqa/contracts/__init__.py`
- Test: `tests/contracts/test_core.py`

**Interfaces:**
- Produces:
  - `ObservationSnapshot(mode, url, title, text, element_count, size_bytes, truncated)`
  - `Action(type: Literal["navigate","click","fill","finish"], target: str | None, value: str | None, rationale: str)`
  - `StepResult(index, action, ok, error: str | None, duration_ms, input_tokens, output_tokens, observation_bytes)`

- [ ] **Step 1: Viết test thất bại**

`tests/contracts/test_core.py`:
```python
from agentqa.contracts import Action, ObservationSnapshot, StepResult

def test_observation_snapshot_roundtrip():
    snap = ObservationSnapshot(
        mode="a11y", url="http://x/login", title="Đăng nhập",
        text="URL: http://x/login", element_count=3, size_bytes=42, truncated=False,
    )
    restored = ObservationSnapshot.model_validate_json(snap.model_dump_json())
    assert restored == snap

def test_action_allows_optional_target():
    action = Action(type="finish")
    assert action.target is None
    assert action.value is None
    assert action.rationale == ""

def test_step_result_keeps_error_on_failure():
    step = StepResult(
        index=0, action=Action(type="click", target="#missing"), ok=False,
        error="Timeout", duration_ms=120, input_tokens=10, output_tokens=5,
        observation_bytes=100,
    )
    assert step.ok is False
    assert step.error == "Timeout"
```

- [ ] **Step 2: Chạy test cho FAIL**

Run: `uv run pytest tests/contracts/test_core.py -v`
Expected: FAIL — `ImportError: cannot import name 'Action'`.

- [ ] **Step 3: Viết implementation tối thiểu**

`src/agentqa/contracts/core.py`:
```python
from typing import Literal

from pydantic import BaseModel

ObservationMode = Literal["a11y", "vision", "hybrid"]
ActionType = Literal["navigate", "click", "fill", "finish"]


class ObservationSnapshot(BaseModel):
    mode: ObservationMode
    url: str
    title: str
    text: str
    element_count: int
    size_bytes: int
    truncated: bool


class Action(BaseModel):
    type: ActionType
    target: str | None = None
    value: str | None = None
    rationale: str = ""


class StepResult(BaseModel):
    index: int
    action: Action
    ok: bool
    error: str | None = None
    duration_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    observation_bytes: int = 0
```

`src/agentqa/contracts/__init__.py`:
```python
from agentqa.contracts.core import (
    Action,
    ActionType,
    ObservationMode,
    ObservationSnapshot,
    StepResult,
)

__all__ = [
    "Action",
    "ActionType",
    "ObservationMode",
    "ObservationSnapshot",
    "StepResult",
]
```

- [ ] **Step 4: Chạy test cho PASS**

Run: `uv run pytest tests/contracts/test_core.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/agentqa/contracts tests/contracts/test_core.py
git commit -m "feat(contracts): add core observation, action and step models"
```

---

### Task 4: Contracts v1 — verify / trace / case models + loader

**Files:**
- Create: `src/agentqa/contracts/verify.py`
- Create: `src/agentqa/contracts/trace.py`
- Create: `src/agentqa/contracts/case.py`
- Modify: `src/agentqa/contracts/__init__.py`
- Test: `tests/contracts/test_verify_trace_case.py`

**Interfaces:**
- Consumes: `Action`, `StepResult` từ Task 3.
- Produces:
  - `AssertionSpec(id, kind: Literal["text_visible","url_contains"], value, description)`; `AssertionResult(assertion_id, status: Literal["passed","failed","error"], detail)`
  - `MutationChange(kind, selector, before, after)`; `MutationSpec(id, variant, description, changes, ground_truth)`
  - `RunMetrics(llm_calls, input_tokens, output_tokens, duration_s)`; `RunVersions(app, model, prompt)`; `RunTrace(run_id, case_name, status, started_at, finished_at, steps, assertions, metrics, versions, error)`
  - `TestCase(name, start_path, goal, max_steps=20, assertions=[])`; `load_case(path) -> TestCase` (đọc YAML)

- [ ] **Step 1: Viết test thất bại**

`tests/contracts/test_verify_trace_case.py`:
```python
from pathlib import Path

from agentqa.contracts import (
    AssertionResult,
    AssertionSpec,
    MutationSpec,
    RunMetrics,
    RunTrace,
    RunVersions,
    TestCase,
    load_case,
)


def test_run_trace_defaults_are_serializable():
    trace = RunTrace(
        run_id="r1", case_name="login", status="failed",
        started_at="2026-09-17T00:00:00+00:00", finished_at="2026-09-17T00:00:01+00:00",
        metrics=RunMetrics(), versions=RunVersions(app="0.1.0", model="fake", prompt="v1"),
    )
    assert trace.steps == []
    assert trace.assertions == []
    assert trace.error == ""
    assert '"r1"' in trace.model_dump_json()

def test_assertion_result_status_is_checked():
    result = AssertionResult(assertion_id="a1", status="passed", detail="ok")
    assert result.status == "passed"

def test_mutation_spec_holds_ground_truth():
    spec = MutationSpec(id="m1", variant="id-change", ground_truth="Add button still works")
    assert spec.changes == []
    assert spec.ground_truth.startswith("Add")

def test_load_case_from_yaml(tmp_path: Path):
    case_file = tmp_path / "case.yaml"
    case_file.write_text(
        "name: login\n"
        "start_path: login.html\n"
        'goal: "Đăng nhập và thêm việc"\n'
        "max_steps: 15\n"
        "assertions:\n"
        "  - id: a1\n"
        "    kind: text_visible\n"
        '    value: "Mua sữa"\n',
        encoding="utf-8",
    )
    case = load_case(case_file)
    assert case.name == "login"
    assert case.max_steps == 15
    assert case.assertions == [AssertionSpec(id="a1", kind="text_visible", value="Mua sữa")]

def test_load_case_rejects_missing_fields(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("name: x\n", encoding="utf-8")
    try:
        load_case(bad)
        raise AssertionError("expected validation error")
    except ValueError:
        pass
```

- [ ] **Step 2: Chạy test cho FAIL**

Run: `uv run pytest tests/contracts/test_verify_trace_case.py -v`
Expected: FAIL — chưa có các tên import trên.

- [ ] **Step 3: Viết implementation tối thiểu**

`src/agentqa/contracts/verify.py`:
```python
from typing import Literal

from pydantic import BaseModel

AssertionKind = Literal["text_visible", "url_contains"]
AssertionStatus = Literal["passed", "failed", "error"]


class AssertionSpec(BaseModel):
    id: str
    kind: AssertionKind
    value: str
    description: str = ""


class AssertionResult(BaseModel):
    assertion_id: str
    status: AssertionStatus
    detail: str = ""


class MutationChange(BaseModel):
    kind: str
    selector: str | None = None
    before: str | None = None
    after: str | None = None


class MutationSpec(BaseModel):
    id: str
    variant: str
    description: str = ""
    changes: list[MutationChange] = []
    ground_truth: str = ""
```

`src/agentqa/contracts/trace.py`:
```python
from typing import Literal

from pydantic import BaseModel

from agentqa.contracts.core import StepResult
from agentqa.contracts.verify import AssertionResult

RunStatus = Literal["passed", "failed", "error"]


class RunMetrics(BaseModel):
    llm_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    duration_s: float = 0.0


class RunVersions(BaseModel):
    app: str
    model: str
    prompt: str


class RunTrace(BaseModel):
    run_id: str
    case_name: str
    status: RunStatus
    started_at: str
    finished_at: str
    steps: list[StepResult] = []
    assertions: list[AssertionResult] = []
    metrics: RunMetrics = RunMetrics()
    versions: RunVersions
    error: str = ""
```

`src/agentqa/contracts/case.py`:
```python
from pathlib import Path

import yaml
from pydantic import BaseModel

from agentqa.contracts.verify import AssertionSpec


class TestCase(BaseModel):
    name: str
    start_path: str
    goal: str
    max_steps: int = 20
    assertions: list[AssertionSpec] = []


def load_case(path: Path) -> TestCase:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"case file must contain a mapping: {path}")
    return TestCase.model_validate(raw)
```

Cập nhật `src/agentqa/contracts/__init__.py` để re-export toàn bộ tên trên (giữ nguyên các tên Task 3).

- [ ] **Step 4: Chạy test cho PASS**

Run: `uv run pytest tests/contracts -v`
Expected: toàn bộ passed.

- [ ] **Step 5: Commit + freeze contracts v1**

```bash
git add src/agentqa/contracts tests/contracts
git commit -m "feat(contracts): freeze v1 for verify, trace, case models and case loader"
```

Sau commit này: mọi thay đổi `contracts/` phải qua PR có review + ghi rõ ảnh hưởng.

---

### Task 5: LLM layer — adapter OpenAI-compatible + FakeLLM

**Files:**
- Create: `src/agentqa/llm/adapter.py`
- Create: `src/agentqa/llm/fake.py`
- Create: `src/agentqa/llm/openai_adapter.py`
- Test: `tests/llm/test_adapter.py`
- Test: `tests/llm/test_fake.py`
- Test: `tests/llm/test_openai_adapter.py`

**Interfaces:**
- Consumes: `Action` (Task 3).
- Produces:
  - `LLMResult(action: Action, input_tokens: int, output_tokens: int)`
  - `LLMAdapter` Protocol: attribute `model: str`, method `async decide(system: str, user: str) -> LLMResult`
  - `FakeLLM(actions: list[Action], input_tokens=10, output_tokens=5)` — có `.calls: list[str]`
  - `ActionDecision(type, target, value, rationale)` + `_to_action(decision) -> Action`
  - `OpenAICompatAdapter.from_env()`; `LLMFormatError`; `DEFAULT_BASE_URL`, `DEFAULT_MODEL`

- [ ] **Step 1: Viết test thất bại cho FakeLLM + adapter models**

`tests/llm/test_fake.py`:
```python
import pytest

from agentqa.contracts import Action
from agentqa.llm.fake import FakeLLM


async def test_fake_llm_returns_scripted_actions_in_order():
    llm = FakeLLM([Action(type="finish")])
    result = await llm.decide("system", "user")
    assert result.action.type == "finish"
    assert result.input_tokens == 10
    assert llm.calls == ["user"]


async def test_fake_llm_raises_when_script_exhausted():
    llm = FakeLLM([])
    with pytest.raises(RuntimeError):
        await llm.decide("system", "user")
```

`tests/llm/test_openai_adapter.py`:
```python
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
```

- [ ] **Step 2: Chạy test cho FAIL**

Run: `uv run pytest tests/llm -v`
Expected: FAIL — module chưa tồn tại.

- [ ] **Step 3: Viết implementation tối thiểu**

`src/agentqa/llm/adapter.py`:
```python
from typing import Protocol

from pydantic import BaseModel

from agentqa.contracts import Action


class LLMResult(BaseModel):
    action: Action
    input_tokens: int = 0
    output_tokens: int = 0


class LLMAdapter(Protocol):
    model: str

    async def decide(self, system: str, user: str) -> LLMResult: ...
```

`src/agentqa/llm/fake.py`:
```python
from agentqa.contracts import Action
from agentqa.llm.adapter import LLMResult


class FakeLLM:
    def __init__(self, actions: list[Action], input_tokens: int = 10, output_tokens: int = 5):
        self.model = "fake"
        self._actions = list(actions)
        self._input_tokens = input_tokens
        self._output_tokens = output_tokens
        self.calls: list[str] = []

    async def decide(self, system: str, user: str) -> LLMResult:
        self.calls.append(user)
        if not self._actions:
            raise RuntimeError("FakeLLM has no scripted actions left")
        return LLMResult(
            action=self._actions.pop(0),
            input_tokens=self._input_tokens,
            output_tokens=self._output_tokens,
        )
```

`src/agentqa/llm/openai_adapter.py`:
```python
import json
import os
import re
from typing import Literal

from openai import AsyncOpenAI
from pydantic import BaseModel

from agentqa.contracts import Action
from agentqa.llm.adapter import LLMResult

DEFAULT_BASE_URL = "https://opencode.ai/zen/v1"
DEFAULT_MODEL = "deepseek-v4-flash"


class LLMFormatError(RuntimeError):
    pass


class ActionDecision(BaseModel):
    type: Literal["navigate", "click", "fill", "finish"]
    target: str = ""
    value: str = ""
    rationale: str = ""


def _to_action(decision: ActionDecision) -> Action:
    return Action(
        type=decision.type,
        target=decision.target or None,
        value=decision.value or None,
        rationale=decision.rationale,
    )


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end <= start:
        raise LLMFormatError(f"no JSON object found in LLM output: {cleaned[:200]!r}")
    try:
        payload = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMFormatError(f"invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise LLMFormatError("LLM output JSON is not an object")
    return payload


class OpenAICompatAdapter:
    def __init__(self, *, base_url: str, api_key: str, model: str):
        self.model = model
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    @classmethod
    def from_env(cls) -> "OpenAICompatAdapter":
        base_url = os.environ.get("AGENTQA_LLM_BASE_URL", DEFAULT_BASE_URL)
        api_key = os.environ.get("AGENTQA_LLM_API_KEY", "")
        if not api_key and "localhost" not in base_url and "127.0.0.1" not in base_url:
            raise RuntimeError(
                "AGENTQA_LLM_API_KEY is required (set it in .env; Ollama local does not need one)"
            )
        return cls(
            base_url=base_url,
            api_key=api_key or "not-needed",
            model=os.environ.get("AGENTQA_LLM_MODEL", DEFAULT_MODEL),
        )

    async def decide(self, system: str, user: str) -> LLMResult:
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = response.choices[0].message.content or ""
        payload = _extract_json(content)
        try:
            decision = ActionDecision.model_validate(payload)
        except Exception as exc:
            raise LLMFormatError(f"invalid action payload: {payload!r}") from exc
        usage = response.usage
        return LLMResult(
            action=_to_action(decision),
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
        )
```

- [ ] **Step 4: Chạy test cho PASS**

Run: `uv run pytest tests/llm -v`
Expected: toàn bộ passed (không gọi mạng — client bị thay bằng stub).

- [ ] **Step 5: Commit**

```bash
git add src/agentqa/llm tests/llm
git commit -m "feat(llm): add openai-compatible adapter with json extraction and fake adapter"
```

---

### Task 6: Demo-site tĩnh + script sinh variants

**Files:**
- Create: `apps/demo-site/base/login.html`
- Create: `apps/demo-site/base/index.html`
- Create: `apps/demo-site/base/app.js`
- Create: `apps/demo-site/tools/gen_variants.py`
- Create: `apps/demo-site/variant-specs/id-change.json`
- Create: `apps/demo-site/variants/.gitkeep`
- Test: `tests/demo_site/test_gen_variants.py`

**Interfaces:**
- Produces: `generate_variant(base_dir: Path, out_dir: Path, spec: dict) -> Path` (spec: `{"name": str, "changes": [{"file","before","after"}]}`), raise `ValueError` nếu pattern không tồn tại.

- [ ] **Step 1: Viết test thất bại**

`tests/demo_site/test_gen_variants.py`:
```python
import json
from pathlib import Path

import pytest

from gen_variants import generate_variant


def _make_base(tmp_path: Path) -> Path:
    base = tmp_path / "base"
    base.mkdir()
    (base / "index.html").write_text('<input id="new-todo"><button id="add-btn">Thêm</button>', encoding="utf-8")
    (base / "app.js").write_text('document.getElementById("add-btn");', encoding="utf-8")
    return base


def test_generate_variant_replaces_patterns_in_all_files(tmp_path: Path):
    base = _make_base(tmp_path)
    spec = {
        "name": "id-change",
        "changes": [
            {"file": "index.html", "before": 'id="new-todo"', "after": 'id="task-input"'},
            {"file": "index.html", "before": 'id="add-btn"', "after": 'id="create-task"'},
            {"file": "app.js", "before": '"add-btn"', "after": '"create-task"'},
        ],
    }
    out = generate_variant(base, tmp_path / "variants", spec)
    html = (out / "index.html").read_text(encoding="utf-8")
    js = (out / "app.js").read_text(encoding="utf-8")
    assert 'id="task-input"' in html
    assert 'id="create-task"' in html
    assert '"create-task"' in js
    assert 'id="add-btn"' not in html
    assert 'id="new-todo"' in (base / "index.html").read_text(encoding="utf-8")


def test_generate_variant_raises_on_missing_pattern(tmp_path: Path):
    base = _make_base(tmp_path)
    spec = {"name": "bad", "changes": [{"file": "index.html", "before": "không-tồn-tại", "after": "x"}]}
    with pytest.raises(ValueError):
        generate_variant(base, tmp_path / "variants", spec)
```

Lưu ý: test import `gen_variants` — thêm `pythonpath` cho pytest trong `pyproject.toml`: `[tool.pytest.ini_options] pythonpath = ["apps/demo-site/tools"]` (sửa mục đã tạo ở Task 1, thêm dòng này cạnh `testpaths`).

- [ ] **Step 2: Chạy test cho FAIL**

Run: `uv run pytest tests/demo_site -v`
Expected: FAIL — `ModuleNotFoundError: gen_variants`.

- [ ] **Step 3: Viết implementation**

`apps/demo-site/tools/gen_variants.py`:
```python
import json
import shutil
import sys
from pathlib import Path


def generate_variant(base_dir: Path, out_dir: Path, spec: dict) -> Path:
    target = Path(out_dir) / spec["name"]
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(base_dir, target)
    for change in spec.get("changes", []):
        file_path = target / change["file"]
        original = file_path.read_text(encoding="utf-8")
        if change["before"] not in original:
            raise ValueError(f"pattern not found in {change['file']}: {change['before']!r}")
        file_path.write_text(original.replace(change["before"], change["after"]), encoding="utf-8")
    return target


def main() -> None:
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    site_dir = Path(__file__).resolve().parents[1]
    result = generate_variant(site_dir / "base", site_dir / "variants", spec)
    print(result)


if __name__ == "__main__":
    main()
```

`apps/demo-site/base/login.html`:
```html
<!doctype html>
<html lang="vi">
<head><meta charset="utf-8"><title>Đăng nhập</title></head>
<body>
  <h1>Đăng nhập</h1>
  <form id="login-form">
    <label for="username">Tên đăng nhập</label>
    <input id="username" name="username" type="text">
    <label for="password">Mật khẩu</label>
    <input id="password" name="password" type="password">
    <button id="login-btn" type="submit">Đăng nhập</button>
  </form>
  <p id="login-error"></p>
  <script src="app.js"></script>
</body>
</html>
```

`apps/demo-site/base/index.html`:
```html
<!doctype html>
<html lang="vi">
<head><meta charset="utf-8"><title>Việc cần làm</title></head>
<body>
  <h1>Việc cần làm</h1>
  <p id="greeting"></p>
  <input id="new-todo" type="text" placeholder="Việc mới">
  <button id="add-btn">Thêm</button>
  <ul id="todo-list"></ul>
  <script src="app.js"></script>
</body>
</html>
```

`apps/demo-site/base/app.js`:
```js
const STORAGE_TODOS = "agentqa_todos";
const STORAGE_USER = "agentqa_user";

function getTodos() {
  return JSON.parse(localStorage.getItem(STORAGE_TODOS) || "[]");
}

function renderTodos() {
  const list = document.getElementById("todo-list");
  if (!list) return;
  list.innerHTML = "";
  for (const item of getTodos()) {
    const li = document.createElement("li");
    li.textContent = item;
    li.addEventListener("click", () => li.classList.toggle("done"));
    list.appendChild(li);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", (event) => {
      event.preventDefault();
      localStorage.setItem(STORAGE_USER, document.getElementById("username").value);
      window.location.href = "index.html";
    });
  }
  const addBtn = document.getElementById("add-btn");
  if (addBtn) {
    if (!localStorage.getItem(STORAGE_USER)) {
      window.location.href = "login.html";
      return;
    }
    const input = document.getElementById("new-todo");
    document.getElementById("greeting").textContent = "Xin chào " + localStorage.getItem(STORAGE_USER);
    addBtn.addEventListener("click", () => {
      const value = input.value.trim();
      if (!value) return;
      const todos = getTodos();
      todos.push(value);
      localStorage.setItem(STORAGE_TODOS, JSON.stringify(todos));
      input.value = "";
      renderTodos();
    });
    renderTodos();
  }
});
```

`apps/demo-site/variant-specs/id-change.json`:
```json
{
  "name": "id-change",
  "changes": [
    {"file": "index.html", "before": "id=\"new-todo\"", "after": "id=\"task-input\""},
    {"file": "index.html", "before": "id=\"add-btn\"", "after": "id=\"create-task\""},
    {"file": "app.js", "before": "getElementById(\"add-btn\")", "after": "getElementById(\"create-task\")"},
    {"file": "app.js", "before": "getElementById(\"new-todo\")", "after": "getElementById(\"task-input\")"}
  ]
}
```

- [ ] **Step 4: Chạy test cho PASS + chạy thật generator**

Run: `uv run pytest tests/demo_site -v; uv run python apps/demo-site/tools/gen_variants.py apps/demo-site/variant-specs/id-change.json; uv run python -c "from pathlib import Path; print('create-task' in Path('apps/demo-site/variants/id-change/index.html').read_text(encoding='utf-8'))"`
Expected: test passed; generator in ra đường dẫn variant; dòng cuối in `True`.

- [ ] **Step 5: Commit**

```bash
git add apps/demo-site tests/demo_site pyproject.toml
git commit -m "feat(demo-site): add static demo app and ui variant generator"
```

---

### Task 7: Browser observation thô (a11y-ish, cap 8KB)

**Files:**
- Create: `src/agentqa/agent/observation.py`
- Test: `tests/conftest.py` (fixtures dùng chung: static server + Playwright page)
- Test: `tests/agent/test_observation.py`

**Interfaces:**
- Consumes: `ObservationSnapshot` (Task 3).
- Produces: `observe(page: Page, mode: str = "a11y") -> ObservationSnapshot`; `MAX_OBSERVATION_BYTES = 8192`.

- [ ] **Step 1: Viết test thất bại**

`tests/conftest.py`:
```python
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from playwright.async_api import async_playwright

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_SITE_DIR = REPO_ROOT / "apps" / "demo-site" / "base"


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):  # noqa: ANN002
        pass


@pytest.fixture()
def demo_server():
    handler = partial(_QuietHandler, directory=str(DEMO_SITE_DIR))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    yield f"http://{host}:{port}"
    server.shutdown()
    thread.join(timeout=5)


@pytest.fixture()
async def page():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        yield page
        await browser.close()
```

`tests/agent/test_observation.py`:
```python
from agentqa.agent.observation import MAX_OBSERVATION_BYTES, observe


async def test_observe_captures_elements_and_metadata(page):
    await page.set_content("<button id='b'>Nhấn</button><a href='/x'>Link</a><p>nội dung</p>")
    snapshot = await observe(page)
    assert "button#b" in snapshot.text
    assert "Link" in snapshot.text
    assert snapshot.element_count == 2
    assert snapshot.mode == "a11y"
    assert snapshot.truncated is False


async def test_observe_truncates_large_pages(page):
    await page.set_content(f"<p>{'x' * 20000}</p><input id='name'>")
    snapshot = await observe(page)
    assert snapshot.truncated is True
    assert snapshot.size_bytes == MAX_OBSERVATION_BYTES
    assert len(snapshot.text.encode("utf-8")) <= MAX_OBSERVATION_BYTES
    assert snapshot.element_count == 1
```

- [ ] **Step 2: Chạy test cho FAIL**

Run: `uv run pytest tests/agent/test_observation.py -v`
Expected: FAIL — module chưa tồn tại.

- [ ] **Step 3: Viết implementation**

`src/agentqa/agent/observation.py`:
```python
from playwright.async_api import Page

from agentqa.contracts import ObservationSnapshot

MAX_OBSERVATION_BYTES = 8192

_ELEMENTS_JS = """
els => els.map(e => ({
  tag: e.tagName.toLowerCase(),
  id: e.id || "",
  text: (e.innerText || e.value || e.placeholder || e.getAttribute("aria-label") || "")
          .trim().slice(0, 80)
}))
"""


async def observe(page: Page, mode: str = "a11y") -> ObservationSnapshot:
    url = page.url
    title = await page.title()
    elements = await page.eval_on_selector_all("a, button, input, select, textarea", _ELEMENTS_JS)
    body_text = (await page.inner_text("body")).strip()
    lines = [f"- {e['tag']}#{e['id']}: {e['text']}" for e in elements]
    text = (
        f"URL: {url}\nTITLE: {title}\n"
        f"ELEMENTS ({len(elements)}):\n" + "\n".join(lines) + "\nPAGE TEXT:\n" + body_text
    )
    encoded = text.encode("utf-8")
    truncated = len(encoded) > MAX_OBSERVATION_BYTES
    if truncated:
        text = encoded[:MAX_OBSERVATION_BYTES].decode("utf-8", errors="ignore")
    return ObservationSnapshot(
        mode=mode,
        url=url,
        title=title,
        text=text,
        element_count=len(elements),
        size_bytes=min(len(encoded), MAX_OBSERVATION_BYTES),
        truncated=truncated,
    )
```

- [ ] **Step 4: Chạy test cho PASS**

Run: `uv run pytest tests/agent/test_observation.py -v`
Expected: 2 passed. (Lần đầu cần `uv run playwright install chromium` nếu máy chưa có browser.)

- [ ] **Step 5: Commit**

```bash
git add src/agentqa/agent/observation.py tests/agent
git commit -m "feat(agent): add raw observation with 8kb truncation"
```

---

### Task 8: Action executor (Playwright)

**Files:**
- Create: `src/agentqa/agent/executor.py`
- Test: `tests/agent/test_executor.py`

**Interfaces:**
- Consumes: `Action` (Task 3).
- Produces: `execute(page, action) -> None`; `ActionExecutionError(RuntimeError)`.

- [ ] **Step 1: Viết test thất bại**

`tests/agent/test_executor.py`:
```python
import pytest

from agentqa.agent.executor import ActionExecutionError, execute
from agentqa.contracts import Action


async def test_execute_navigate_loads_login_page(page, demo_server):
    await execute(page, Action(type="navigate", target=f"{demo_server}/login.html"))
    assert page.url.endswith("/login.html")


async def test_execute_fill_sets_input_value(page):
    await page.set_content("<input id='name'>")
    await execute(page, Action(type="fill", target="#name", value="Xin chào"))
    assert await page.input_value("#name") == "Xin chào"


async def test_execute_click_triggers_script(page):
    await page.set_content("<button id='go'>Go</button><script>document.getElementById('go').onclick=()=>{document.title='clicked'}</script>")
    await execute(page, Action(type="click", target="#go"))
    assert await page.title() == "clicked"


async def test_execute_finish_is_noop(page):
    await page.set_content("<p>x</p>")
    await execute(page, Action(type="finish"))
    assert "<p>x</p>" in await page.content()


async def test_execute_click_missing_target_raises(page):
    await page.set_content("<p>x</p>")
    with pytest.raises(ActionExecutionError):
        await execute(page, Action(type="click", target="#missing"))
```

- [ ] **Step 2: Chạy test cho FAIL**

Run: `uv run pytest tests/agent/test_executor.py -v`
Expected: FAIL — chưa có `executor`.

- [ ] **Step 3: Viết implementation**

`src/agentqa/agent/executor.py`:
```python
from playwright.async_api import Page

from agentqa.contracts import Action

ACTION_TIMEOUT_MS = 5000


class ActionExecutionError(RuntimeError):
    pass


async def execute(page: Page, action: Action) -> None:
    try:
        if action.type == "navigate":
            await page.goto(action.target or "")
        elif action.type == "click":
            await page.click(action.target or "", timeout=ACTION_TIMEOUT_MS)
        elif action.type == "fill":
            await page.fill(action.target or "", action.value or "", timeout=ACTION_TIMEOUT_MS)
        elif action.type == "finish":
            return
    except Exception as exc:
        raise ActionExecutionError(str(exc)) from exc
```

Ghi chú: timeout 5s để test bước fail không chờ 30s mặc định; W1 sẽ tinh chỉnh timeout theo step ở W3–5 (knob này nằm trong executor).

- [ ] **Step 4: Chạy test cho PASS**

Run: `uv run pytest tests/agent/test_executor.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add src/agentqa/agent/executor.py tests/agent/test_executor.py
git commit -m "feat(agent): add playwright action executor"
```

---

### Task 9: Assertion checker

**Files:**
- Create: `src/agentqa/verify/checker.py`
- Test: `tests/verify/test_checker.py`

**Interfaces:**
- Consumes: `AssertionSpec`, `AssertionResult` (Task 4).
- Produces: `check(page, spec) -> AssertionResult`; `check_all(page, specs) -> list[AssertionResult]`.

- [ ] **Step 1: Viết test thất bại**

`tests/verify/test_checker.py`:
```python
from agentqa.contracts import AssertionSpec
from agentqa.verify.checker import check, check_all


async def test_text_visible_passes_when_text_present(page):
    await page.set_content("<ul><li>Mua sữa</li></ul>")
    spec = AssertionSpec(id="a1", kind="text_visible", value="Mua sữa")
    result = await check(page, spec)
    assert result.status == "passed"
    assert result.assertion_id == "a1"


async def test_text_visible_fails_when_text_absent(page):
    await page.set_content("<p>khác</p>")
    spec = AssertionSpec(id="a2", kind="text_visible", value="Mua sữa")
    result = await check(page, spec)
    assert result.status == "failed"


async def test_url_contains_uses_current_url(page, demo_server):
    await page.goto(f"{demo_server}/login.html")
    passed = await check(page, AssertionSpec(id="u1", kind="url_contains", value="login.html"))
    failed = await check(page, AssertionSpec(id="u2", kind="url_contains", value="index.html"))
    assert passed.status == "passed"
    assert failed.status == "failed"


async def test_check_all_returns_one_result_per_spec(page):
    await page.set_content("<p>abc</p>")
    specs = [
        AssertionSpec(id="a1", kind="text_visible", value="abc"),
        AssertionSpec(id="a2", kind="text_visible", value="xyz"),
    ]
    results = await check_all(page, specs)
    assert [r.status for r in results] == ["passed", "failed"]
```

- [ ] **Step 2: Chạy test cho FAIL**

Run: `uv run pytest tests/verify -v`
Expected: FAIL — chưa có `checker`.

- [ ] **Step 3: Viết implementation**

`src/agentqa/verify/checker.py`:
```python
from playwright.async_api import Page

from agentqa.contracts import AssertionResult, AssertionSpec


async def check(page: Page, spec: AssertionSpec) -> AssertionResult:
    try:
        if spec.kind == "text_visible":
            visible = await page.is_visible(f"text={spec.value}")
            return AssertionResult(
                assertion_id=spec.id,
                status="passed" if visible else "failed",
                detail=spec.value,
            )
        if spec.kind == "url_contains":
            matched = spec.value in page.url
            return AssertionResult(
                assertion_id=spec.id,
                status="passed" if matched else "failed",
                detail=page.url,
            )
        return AssertionResult(assertion_id=spec.id, status="error", detail=f"unknown kind: {spec.kind}")
    except Exception as exc:
        return AssertionResult(assertion_id=spec.id, status="error", detail=str(exc))


async def check_all(page: Page, specs: list[AssertionSpec]) -> list[AssertionResult]:
    return [await check(page, spec) for spec in specs]
```

- [ ] **Step 4: Chạy test cho PASS**

Run: `uv run pytest tests/verify -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/agentqa/verify tests/verify
git commit -m "feat(verify): add assertion checker for text visibility and url"
```

---

### Task 10: Agent loop + prompts (observe → decide → execute → assert)

**Files:**
- Create: `src/agentqa/agent/prompts.py`
- Create: `src/agentqa/agent/loop.py`
- Test: `tests/agent/test_loop.py`

**Interfaces:**
- Consumes: `observe` (Task 7), `execute`/`ActionExecutionError` (Task 8), `check_all` (Task 9), `LLMAdapter`/`LLMResult` (Task 5), contracts (Task 3–4).
- Produces: `run_case(case, llm, *, base_url, headless=True) -> RunTrace`; `PROMPT_VERSION = "v1"`; `SYSTEM_PROMPT`; `build_user_prompt(goal, snapshot, history) -> str`.

- [ ] **Step 1: Viết test thất bại**

`tests/agent/test_loop.py`:
```python
from pathlib import Path

from agentqa.agent.loop import run_case
from agentqa.contracts import Action, TestCase, load_case
from agentqa.llm.fake import FakeLLM

REPO_ROOT = Path(__file__).resolve().parents[2]


def _login_script() -> list[Action]:
    return [
        Action(type="fill", target="#username", value="demo"),
        Action(type="fill", target="#password", value="demo"),
        Action(type="click", target="#login-btn"),
        Action(type="fill", target="#new-todo", value="Mua sữa"),
        Action(type="click", target="#add-btn"),
        Action(type="finish"),
    ]


def _login_case() -> TestCase:
    return load_case(REPO_ROOT / "experiments" / "cases" / "login_todo.yaml")


async def test_run_case_passes_end_to_end(demo_server):
    llm = FakeLLM(_login_script())
    trace = await run_case(_login_case(), llm, base_url=demo_server)
    assert trace.status == "passed"
    assert trace.case_name == "login_todo"
    assert len(trace.steps) == 5
    assert trace.metrics.llm_calls == 6
    assert trace.metrics.input_tokens == 60
    assert trace.metrics.output_tokens == 30
    assert [a.status for a in trace.assertions] == ["passed", "passed"]
    assert trace.versions.model == "fake"
    assert trace.versions.prompt == "v1"
    assert trace.error == ""


async def test_run_case_fails_when_assertion_not_met(demo_server):
    case = _login_case().model_copy(
        update={"assertions": [case_assertion("Sản phẩm đã giao")]}
    )
    llm = FakeLLM(_login_script())
    trace = await run_case(case, llm, base_url=demo_server)
    assert trace.status == "failed"
    assert trace.assertions[0].status == "failed"


async def test_run_case_marks_failed_step_but_continues(demo_server):
    script = [Action(type="click", target="#khong-ton-tai")] + _login_script()
    llm = FakeLLM(script)
    trace = await run_case(_login_case(), llm, base_url=demo_server)
    assert trace.steps[0].ok is False
    assert trace.steps[0].error is not None
    assert trace.status == "failed"


def case_assertion(value: str):
    from agentqa.contracts import AssertionSpec

    return AssertionSpec(id="a1", kind="text_visible", value=value)
```

Đồng thời tạo case thật `experiments/cases/login_todo.yaml` (file này test dùng):
```yaml
name: login_todo
start_path: login.html
goal: "Đăng nhập bằng tài khoản demo/demo, sau đó thêm việc 'Mua sữa' vào danh sách"
max_steps: 15
assertions:
  - id: todo-visible
    kind: text_visible
    value: "Mua sữa"
  - id: on-index
    kind: url_contains
    value: "index.html"
```

- [ ] **Step 2: Chạy test cho FAIL**

Run: `uv run pytest tests/agent/test_loop.py -v`
Expected: FAIL — chưa có `loop`/`prompts` + case file.

- [ ] **Step 3: Viết implementation**

`src/agentqa/agent/prompts.py`:
```python
from agentqa.contracts import ObservationSnapshot

PROMPT_VERSION = "v1"

SYSTEM_PROMPT = (
    "Bạn là agent kiểm thử web. Bạn nhận mục tiêu kiểm thử và ảnh chụp trạng thái trang "
    "(URL, tiêu đề, danh sách phần tử tương tác, văn bản trang) và quyết định HÀNH ĐỘNG TIẾP THEO.\n"
    "Chỉ trả về MỘT object JSON, không kèm chữ nào khác, đúng định dạng:\n"
    '{"type": "navigate" | "click" | "fill" | "finish", "target": "...", "value": "...", "rationale": "..."}\n'
    "Quy tắc: type=navigate thì target là URL; type=click thì target là selector Playwright "
    "(ưu tiên #id, hoặc text=<nhãn hiển thị>); type=fill thì target là selector và value là nội dung cần gõ; "
    "type=finish khi mục tiêu đã hoàn thành. target/value/rationale luôn là chuỗi (được phép rỗng)."
)


def build_user_prompt(goal: str, snapshot: ObservationSnapshot, history: list[str]) -> str:
    parts = [f"MỤC TIÊU: {goal}", f"TRẠNG THÁI TRANG:\n{snapshot.text}"]
    if history:
        parts.append("CÁC BƯỚC ĐÃ LÀM:\n" + "\n".join(history))
    parts.append("Hành động tiếp theo là gì? Trả về JSON.")
    return "\n\n".join(parts)
```

`src/agentqa/agent/loop.py`:
```python
import time
import uuid
from datetime import datetime, timezone

from playwright.async_api import async_playwright

from agentqa.agent.executor import ActionExecutionError, execute
from agentqa.agent.observation import observe
from agentqa.agent.prompts import PROMPT_VERSION, SYSTEM_PROMPT, build_user_prompt
from agentqa.contracts import (
    AssertionResult,
    RunMetrics,
    RunTrace,
    RunVersions,
    StepResult,
    TestCase,
)
from agentqa.llm.adapter import LLMAdapter
from agentqa.verify.checker import check_all

APP_VERSION = "0.1.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def run_case(
    case: TestCase, llm: LLMAdapter, *, base_url: str, headless: bool = True
) -> RunTrace:
    run_id = f"{case.name}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    started_at = _now()
    t0 = time.perf_counter()
    steps: list[StepResult] = []
    assertions: list[AssertionResult] = []
    history: list[str] = []
    input_tokens = output_tokens = llm_calls = 0
    status = "failed"
    error = ""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        try:
            if case.start_path.startswith("http"):
                start_url = case.start_path
            else:
                start_url = f"{base_url.rstrip('/')}/{case.start_path.lstrip('/')}"
            await page.goto(start_url)
            finished = False
            for index in range(case.max_steps):
                snapshot = await observe(page)
                result = await llm.decide(SYSTEM_PROMPT, build_user_prompt(case.goal, snapshot, history))
                llm_calls += 1
                input_tokens += result.input_tokens
                output_tokens += result.output_tokens
                if result.action.type == "finish":
                    finished = True
                    break
                step_started = time.perf_counter()
                step_error = None
                try:
                    await execute(page, result.action)
                except ActionExecutionError as exc:
                    step_error = str(exc)
                steps.append(
                    StepResult(
                        index=index,
                        action=result.action,
                        ok=step_error is None,
                        error=step_error,
                        duration_ms=int((time.perf_counter() - step_started) * 1000),
                        input_tokens=result.input_tokens,
                        output_tokens=result.output_tokens,
                        observation_bytes=snapshot.size_bytes,
                    )
                )
                outcome = "ok" if step_error is None else f"error: {step_error}"
                history.append(f"bước {index + 1}: {result.action.type} {result.action.target or ''} -> {outcome}")
            assertions = await check_all(page, case.assertions)
            passed = (
                finished
                and all(a.status == "passed" for a in assertions)
                and all(s.ok for s in steps)
            )
            status = "passed" if passed else "failed"
        except Exception as exc:
            status = "error"
            error = str(exc)
        finally:
            await browser.close()

    return RunTrace(
        run_id=run_id,
        case_name=case.name,
        status=status,
        started_at=started_at,
        finished_at=_now(),
        steps=steps,
        assertions=assertions,
        metrics=RunMetrics(
            llm_calls=llm_calls,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_s=round(time.perf_counter() - t0, 3),
        ),
        versions=RunVersions(app=APP_VERSION, model=llm.model, prompt=PROMPT_VERSION),
        error=error,
    )
```

- [ ] **Step 4: Chạy test cho PASS**

Run: `uv run pytest tests/agent/test_loop.py -v`
Expected: 3 passed. Nếu test pass đầu tiên fail ở bước `fill #new-todo` do trang chưa kịp điều hướng: kiểm tra `page.click("#login-btn")` có auto-wait navigation không; nếu flaky, thêm `await page.wait_for_url("**/index.html")` trong executor cho action click (ghi chú lại cho W1 xử lý triệt để ở W3–5).

- [ ] **Step 5: Commit**

```bash
git add src/agentqa/agent/prompts.py src/agentqa/agent/loop.py experiments/cases tests/agent/test_loop.py
git commit -m "feat(agent): add plan-act-observe loop with trace output"
```

---

### Task 11: Trace store (platform)

**Files:**
- Create: `src/agentqa/platform/trace_store.py`
- Test: `tests/platform/test_trace_store.py`

**Interfaces:**
- Consumes: `RunTrace` (Task 4).
- Produces: `write_trace(trace: RunTrace, out_dir: Path) -> Path` — ghi `out_dir/<run_id>/trace.json`, trả về đường dẫn file.

- [ ] **Step 1: Viết test thất bại**

`tests/platform/test_trace_store.py`:
```python
import json
from pathlib import Path

from agentqa.contracts import RunMetrics, RunTrace, RunVersions
from agentqa.platform.trace_store import write_trace


def test_write_trace_creates_json_file(tmp_path: Path):
    trace = RunTrace(
        run_id="login_todo-20260917-abc123",
        case_name="login_todo",
        status="passed",
        started_at="2026-09-17T00:00:00+00:00",
        finished_at="2026-09-17T00:00:02+00:00",
        metrics=RunMetrics(llm_calls=6, input_tokens=60, output_tokens=30, duration_s=2.0),
        versions=RunVersions(app="0.1.0", model="fake", prompt="v1"),
    )
    path = write_trace(trace, tmp_path)
    assert path == tmp_path / "login_todo-20260917-abc123" / "trace.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "passed"
    assert data["metrics"]["llm_calls"] == 6
```

- [ ] **Step 2: Chạy test cho FAIL**

Run: `uv run pytest tests/platform -v`
Expected: FAIL — chưa có `trace_store`.

- [ ] **Step 3: Viết implementation**

`src/agentqa/platform/trace_store.py`:
```python
from pathlib import Path

from agentqa.contracts import RunTrace


def write_trace(trace: RunTrace, out_dir: Path) -> Path:
    run_dir = Path(out_dir) / trace.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "trace.json"
    path.write_text(trace.model_dump_json(indent=2), encoding="utf-8")
    return path
```

- [ ] **Step 4: Chạy test cho PASS**

Run: `uv run pytest tests/platform -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add src/agentqa/platform tests/platform
git commit -m "feat(platform): add trace json store"
```

---

### Task 12: CLI runner + 3 case mẫu

**Files:**
- Create: `src/agentqa/cli.py`
- Create: `experiments/cases/add_two_todos.yaml`
- Create: `experiments/cases/fail_demo.yaml`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `run_case` (Task 10), `write_trace` (Task 11), `load_case` (Task 4), `OpenAICompatAdapter.from_env()` (Task 5).
- Produces: `main(argv: list[str] | None = None) -> int` (0 = passed, 1 = failed/error); `build_llm() -> LLMAdapter`.

- [ ] **Step 1: Viết test thất bại**

`tests/test_cli.py`:
```python
import json
from pathlib import Path

from agentqa.cli import main
from agentqa.contracts import Action
from agentqa.llm.fake import FakeLLM


def _fake_builder(actions: list[Action]):
    def builder() -> FakeLLM:
        return FakeLLM(actions)

    return builder


def test_cli_runs_case_and_exits_zero(monkeypatch, demo_server, tmp_path: Path):
    monkeypatch.setattr(
        "agentqa.cli.build_llm",
        _fake_builder(
            [
                Action(type="fill", target="#username", value="demo"),
                Action(type="fill", target="#password", value="demo"),
                Action(type="click", target="#login-btn"),
                Action(type="fill", target="#new-todo", value="Mua sữa"),
                Action(type="click", target="#add-btn"),
                Action(type="finish"),
            ]
        ),
    )
    exit_code = main(
        [
            "run",
            "--case",
            "experiments/cases/login_todo.yaml",
            "--base-url",
            demo_server,
            "--out",
            str(tmp_path),
        ]
    )
    assert exit_code == 0
    traces = list(tmp_path.glob("*/trace.json"))
    assert len(traces) == 1
    assert json.loads(traces[0].read_text(encoding="utf-8"))["status"] == "passed"


def test_cli_exits_one_on_failed_assertion(monkeypatch, demo_server, tmp_path: Path):
    monkeypatch.setattr(
        "agentqa.cli.build_llm",
        _fake_builder([Action(type="finish")]),
    )
    exit_code = main(
        [
            "run",
            "--case",
            "experiments/cases/fail_demo.yaml",
            "--base-url",
            demo_server,
            "--out",
            str(tmp_path),
        ]
    )
    assert exit_code == 1


def test_all_committed_cases_load():
    from agentqa.contracts import load_case

    case_files = sorted(Path("experiments/cases").glob("*.yaml"))
    assert len(case_files) >= 3
    for case_file in case_files:
        assert load_case(case_file).name
```

- [ ] **Step 2: Chạy test cho FAIL**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL — chưa có `cli` + 2 case file.

- [ ] **Step 3: Viết implementation + case files**

`src/agentqa/cli.py`:
```python
import argparse
import asyncio
import sys
from pathlib import Path

from agentqa.agent.loop import run_case
from agentqa.contracts import load_case
from agentqa.llm.adapter import LLMAdapter
from agentqa.platform.trace_store import write_trace


def build_llm() -> LLMAdapter:
    from agentqa.llm.openai_adapter import OpenAICompatAdapter

    return OpenAICompatAdapter.from_env()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentqa")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="run one test case")
    run_parser.add_argument("--case", required=True)
    run_parser.add_argument("--base-url", required=True, dest="base_url")
    run_parser.add_argument("--out", default="experiments/runs")
    run_parser.add_argument("--headed", action="store_true")

    args = parser.parse_args(argv)

    case = load_case(Path(args.case))
    llm = build_llm()
    trace = asyncio.run(run_case(case, llm, base_url=args.base_url, headless=not args.headed))
    path = write_trace(trace, Path(args.out))
    print(f"{trace.status.upper()} {trace.case_name} -> {path}")
    return 0 if trace.status == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
```

`experiments/cases/add_two_todos.yaml`:
```yaml
name: add_two_todos
start_path: login.html
goal: "Đăng nhập bằng demo/demo, thêm hai việc 'Việc A' và 'Việc B' vào danh sách"
max_steps: 20
assertions:
  - id: first-visible
    kind: text_visible
    value: "Việc A"
  - id: second-visible
    kind: text_visible
    value: "Việc B"
```

`experiments/cases/fail_demo.yaml`:
```yaml
name: fail_demo
start_path: login.html
goal: "Đăng nhập bằng demo/demo"
max_steps: 10
assertions:
  - id: impossible
    kind: text_visible
    value: "Sản phẩm đã giao"
```

- [ ] **Step 4: Chạy test cho PASS**

Run: `uv run pytest tests/test_cli.py -v`
Expected: 3 passed.

- [ ] **Step 5: Chạy tay 1 case thật (bước bắt buộc — cần API key trong `.env`)**

Chạy 2 terminal (hoặc 2 lệnh tách biệt):
```bash
uv run python -m http.server 8000 --directory apps/demo-site/base
uv run --env-file .env agentqa run --case experiments/cases/login_todo.yaml --base-url http://127.0.0.1:8000 --headed
```
Expected: in ra `PASSED login_todo -> experiments/runs/.../trace.json`; mở trace thấy `versions.model == "deepseek-v4-flash"` và token > 0. Nếu FAIL: đọc `steps[].error` trong trace + điều chỉnh prompt/action (ghi chú lại — đây là điểm W1 sẽ tinh chỉnh ở W3–5).

- [ ] **Step 6: Commit**

```bash
git add src/agentqa/cli.py experiments/cases tests/test_cli.py
git commit -m "feat(cli): add run entrypoint and sample test cases"
```

---

### Task 13: CI workflow (ruff + import-linter + pytest)

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `infra/docker-compose.yml`

**Interfaces:**
- Produces: check CI tên `test` để gắn vào branch protection (Task 2 Step 3).

- [ ] **Step 1: Tạo `.github/workflows/ci.yml`**

```yaml
name: ci

on:
  pull_request:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync
      - run: uv run ruff check .
      - run: uv run lint-imports
      - run: uv run playwright install --with-deps chromium
      - run: uv run pytest -q
```

- [ ] **Step 2: Tạo `infra/docker-compose.yml`** (chưa dùng ở skeleton — Postgres cho W3)

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: agentqa
      POSTGRES_PASSWORD: agentqa
      POSTGRES_DB: agentqa
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

- [ ] **Step 3: Verify toàn bộ pipeline chạy local**

Run: `uv run ruff check .; uv run lint-imports; uv run pytest -q`
Expected: ruff OK, 4 import contracts kept, toàn bộ test passed (không gọi mạng, không cần API key).

- [ ] **Step 4: Push qua PR + gắn check vào branch protection**

```bash
git checkout -b chore/ci-pipeline
git add .github/workflows/ci.yml infra/docker-compose.yml
git commit -m "chore(ci): add github actions pipeline and postgres compose"
git push -u origin chore/ci-pipeline
gh pr create --fill --base main
```
Expected: CI chạy xanh trên PR; merge; sau đó vào Rulesets của `main` chọn check `test` làm required.

---

### Task 14: Docs, AGENTS.md, runbook + tag `v0.1-skeleton`

**Files:**
- Create: `AGENTS.md`
- Create: `docs/runbooks/dev-setup.md`
- Create: `docs/weekly/W01.md` (template nhật ký tuần)
- Modify: `README.md`

**Interfaces:**
- Produces: DoD của mốc `v0.1-skeleton` — checklist cho cả nhóm verify trước khi tag.

- [ ] **Step 1: Tạo `AGENTS.md`** (nội quy cho AI coding assistant của cả nhóm)

Nội dung gồm: cấu trúc repo + quan hệ lớp; luật import (như Global Constraints); lệnh chuẩn (`uv run pytest`, `uv run ruff check .`, `uv run lint-imports`); quy ước branch `feat/w1-...`; **cấm gọi LLM API thật trong test**; contracts đóng băng — sửa phải nêu ảnh hưởng; commit Conventional Commits.

- [ ] **Step 2: Tạo `docs/runbooks/dev-setup.md`**

Nội dung gồm: cài uv (Windows: `winget install astral-sh.uv`; macOS/Linux: xem docs uv), `uv sync`, `uv run playwright install chromium`, copy `.env.example` → `.env` + điền `AGENTQA_LLM_API_KEY` (Zen: lấy key ở opencode.ai/auth), lệnh chạy test, lệnh chạy 1 case với `.env` (`uv run --env-file .env agentqa run ...` — uv không tự load `.env`), cách đọc trace, cách chạy generator variants, cách bật Postgres khi cần (`docker compose -f infra/docker-compose.yml up -d`).

- [ ] **Step 3: Tạo `docs/weekly/W01.md` template**

```markdown
# Nhật ký tuần W01

## W1
- Làm gì:
- Vướng gì:
- Tuần sau:

## W2
- Làm gì:
- Vướng gì:
- Tuần sau:

## W3
- Làm gì:
- Vướng gì:
- Tuần sau:
```

- [ ] **Step 4: Checklist DoD `v0.1-skeleton` (cả nhóm làm — ghi kết quả vào PR/issue)**

1. `uv run pytest -q` xanh trên máy cả 3 (Windows).
2. Mỗi người tự chạy tay 1 case thật với key Zen của mình, có trace + token > 0.
3. Variant `id-change` chạy được (generator OK) — suite vẫn chạy trên variant này (đối chiếu thủ công).
4. CI xanh trên `main`; branch protection bật.
5. `docs/weekly/W01.md` có nội dung của cả 3.

- [ ] **Step 5: Commit + PR + tag**

```bash
git checkout -b chore/docs-skeleton
git add AGENTS.md docs/runbooks/dev-setup.md docs/weekly/W01.md README.md
git commit -m "docs: add agent rules, dev setup runbook and weekly log template"
git push -u origin chore/docs-skeleton
gh pr create --fill --base main
```
Sau khi merge và DoD xanh: `git checkout main; git pull; git tag v0.1-skeleton; git push origin v0.1-skeleton`

---

## Self-review (đã chạy)

- **Spec coverage:** phạm vi skeleton (mục 2.6 + cột W1–2 bảng milestone) → Task 1–14; contracts v1 → Task 3–4; CI/branch protection/import rules → Task 1, 2, 13; demo-site + variants → Task 6; trace JSON → Task 10–11; runbook/AGENTS/weekly → Task 14. Các mục W3+ (harness, mutation generator, UI, Postgres wiring) nằm ngoài plan này theo thiết kế.
- **Placeholder scan:** không có TBD/TODO; mọi bước code đều có code thật.
- **Type consistency:** `LLMResult`, `ActionDecision`, `_to_action`, `run_case(case, llm, *, base_url, headless)`, `observe`, `execute`, `check_all`, `write_trace`, `load_case` được dùng thống nhất xuyên task; token kỳ vọng trong test loop (6×10/5) khớp giá trị mặc định của `FakeLLM`.
