# AGENTS.md — nội quy cho AI coding assistant

Repo: AgentQA (đồ án tốt nghiệp — nền tảng test web bằng AI agent).
Trước khi code: đọc `README.md`, plan gần nhất trong `docs/superpowers/plans/`, và file này.

## Lệnh chuẩn

- `uv sync` — cài/đồng bộ môi trường
- `uv run pytest -q` — chạy test (**cấm gọi LLM API thật trong test** — dùng `FakeLLM`/stub)
- `uv run ruff check .` — lint, bắt buộc xanh trước commit
- `uv run lint-imports` — kiểm tra luật import, bắt buộc xanh trước commit

## Luật import (import-linter enforce — đừng phá)

- `src/agentqa/contracts/` — module lá, không import gì khác trong `agentqa`
- `src/agentqa/llm/` — chỉ import `contracts`
- `src/agentqa/agent/`, `src/agentqa/verify/` — chỉ import `contracts` + `llm`; **agent và verify KHÔNG import nhau** (checker được truyền vào `run_case` qua tham số `checker` — DI, CLI/test wire)
- `src/agentqa/platform/`, `src/agentqa/cli.py` — được import tự do

## Contracts đóng băng (v1)

`src/agentqa/contracts/` đã freeze. Mọi thay đổi field/kiểu phải: PR có review, mô tả rõ ai bị ảnh hưởng, bump version. Không tự ý đổi tên.

## Quy ước làm việc

- Branch: `feat/<w1|w2|w3|shared>-<mô tả>`, `fix/...`, `chore/...`; sống ngắn, rebase `main` hằng ngày
- Commit: Conventional Commits — `feat(scope): ...` với scope ∈ {contracts, llm, agent, verify, platform, cli, demo-site, ci, docs}
- PR: 1 mục đích/PR, mô tả what/why/cách tự verify; không merge code mình không hiểu; code AI sinh phải kèm test
- Không comment trong code; tên định danh tiếng Anh; chuỗi UI/prompt tiếng Việt theo thiết kế
- Chạy CLI thật cần `.env` — xem `docs/runbooks/dev-setup.md`
