import argparse
import asyncio
import sys
from pathlib import Path

from agentqa.agent.loop import run_case
from agentqa.contracts import load_case
from agentqa.llm.adapter import LLMAdapter
from agentqa.llm.openai_adapter import OpenAICompatAdapter
from agentqa.platform.trace_store import write_trace
from agentqa.verify.checker import check_all


def build_llm() -> LLMAdapter:
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
    trace = asyncio.run(
        run_case(case, llm, base_url=args.base_url, headless=not args.headed, checker=check_all)
    )
    path = write_trace(trace, Path(args.out))
    print(f"{trace.status.upper()} {trace.case_name} -> {path}")
    return 0 if trace.status == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
