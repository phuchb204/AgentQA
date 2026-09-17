from pathlib import Path

from agentqa.agent.loop import run_case
from agentqa.contracts import Action, AssertionSpec, TestCase, load_case
from agentqa.llm.fake import FakeLLM
from agentqa.verify.checker import check_all

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


def case_assertion(value: str) -> AssertionSpec:
    return AssertionSpec(id="a1", kind="text_visible", value=value)


async def test_run_case_passes_end_to_end(demo_server):
    llm = FakeLLM(_login_script())
    trace = await run_case(_login_case(), llm, base_url=demo_server, checker=check_all)
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
    case = _login_case().model_copy(update={"assertions": [case_assertion("Sản phẩm đã giao")]})
    llm = FakeLLM(_login_script())
    trace = await run_case(case, llm, base_url=demo_server, checker=check_all)
    assert trace.status == "failed"
    assert trace.assertions[0].status == "failed"


async def test_run_case_marks_failed_step_but_continues(demo_server):
    script = [Action(type="click", target="#khong-ton-tai")] + _login_script()
    llm = FakeLLM(script)
    trace = await run_case(_login_case(), llm, base_url=demo_server, checker=check_all)
    assert trace.steps[0].ok is False
    assert trace.steps[0].error is not None
    assert trace.status == "failed"
