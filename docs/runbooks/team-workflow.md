# Runbook — Quy trình làm việc nhóm (GitHub Flow)

Áp dụng cho cả 3 thành viên. Repo: https://github.com/phuchb204/agentqa (public).

## Đã tự động — không ai phải nhớ luật

- `main` được bảo vệ: mọi PR cần CI `test` xanh + **chủ repo (Phúc) Approve** mới merge được.
- Cấm force-push và xoá `main`.
- `CODEOWNERS` gán mọi file cho `@phuchb204` → PR tự gắn reviewer.
- CI chạy tự động trên mọi PR: ruff + import-linter + pytest 43 tests (**không gọi LLM API thật**).

## Onboard một lần (sau khi accept invite trên GitHub)

```bash
git clone https://github.com/phuchb204/agentqa.git
cd agentqa
uv sync
uv run playwright install chromium
cp .env.example .env    # điền AGENTQA_LLM_API_KEY (Zen/Go) — xem dev-setup.md §3
uv run pytest -q        # kỳ vọng: 43 passed
```

Trước khi code: đọc `AGENTS.md` (lệnh chuẩn, luật import, contracts frozen) và trỏ AI assistant của bạn vào file này.

## Chu trình mỗi việc

1. Cập nhật main: `git switch main && git pull`
2. Tạo nhánh: `git switch -c feat/w1-<việc>` (prefix `w1|w2|w3|shared`, branch sống ≤ 3 ngày)
3. Làm việc + tự check local: `uv run pytest -q` · `uv run ruff check .` · `uv run lint-imports`
4. Commit: `git commit -m "feat(scope): ..."` (Conventional Commits; scope ∈ contracts, llm, agent, verify, platform, cli, demo-site, ci, docs)
5. Push + mở PR: `git push -u origin <branch>` → `gh pr create --base main --fill`
6. CI xanh → nhờ Phúc Approve → **Squash merge** → nhánh tự xoá
7. Về main mới: `git switch main && git pull` — lặp lại

## Quy tắc chống xung đột

- 1 PR = 1 mục đích, cố gắng < ~400 dòng diff.
- Mỗi ngày rebase nhánh đang làm lên main: `git fetch && git rebase origin/main`.
- Ai merge trước thắng; người sau rebase và tự giải quyết conflict.
- Conflict ở `src/agentqa/contracts/` → **cấm tự chọn phe mình**, gọi nhau cùng giải.
- `contracts/` đã freeze v1: đổi field/kiểu phải nêu rõ ai bị ảnh hưởng + bump version trong PR.

## Việc hằng tuần

- Điền `docs/weekly/Wxx.md`: mỗi người 3 dòng — làm gì / vướng gì / tuần sau.
- Issue: dùng template Task/Bug, gắn label `rq1/rq2/rq3` + milestone `Wxx` để truy vết phân công cho báo cáo.
