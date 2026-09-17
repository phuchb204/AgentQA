# AgentQA

AI-agent web testing platform (graduation project).

Dev setup: see [`docs/runbooks/dev-setup.md`](docs/runbooks/dev-setup.md).

Run tests:

```bash
uv run pytest
```

Run a single case:

```bash
uv run agentqa run --case experiments/cases/login_todo.yaml --base-url <url>
```
