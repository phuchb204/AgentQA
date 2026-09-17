# AgentQA

AI-agent web testing platform (graduation project).

Dev setup: see [`docs/runbooks/dev-setup.md`](docs/runbooks/dev-setup.md).

Run tests:

```bash
uv run pytest
```

Run a single case:

```bash
uv run --env-file .env agentqa run --case experiments/cases/login_todo.yaml --base-url <url>
```

## Bắt đầu

Xem `docs/runbooks/dev-setup.md` để setup môi trường, chạy test và chạy 1 case thật; quy trình làm việc nhóm: `docs/runbooks/team-workflow.md`.

## Trạng thái

Walking skeleton (W1–W2): contracts v1 frozen, LLM adapter OpenAI-compatible (Zen mặc định), demo-site + variant generator, agent loop, trace JSON, CLI, CI. Xem plan: `docs/superpowers/plans/2026-09-17-agentqa-walking-skeleton.md`.
