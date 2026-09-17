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
