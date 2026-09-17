## What
<!-- Thay đổi gì, ở file/khu vực nào -->

## Why
<!-- Vì sao cần — gắn issue nếu có: Closes #... -->

## How verified
<!-- Lệnh đã chạy + kết quả thật, ví dụ: uv run pytest -q -> 43 passed -->

## Checklist
- [ ] `uv run pytest -q` + `uv run ruff check .` + `uv run lint-imports` đều xanh
- [ ] Không đổi `contracts/` (hoặc: có — ghi rõ ai bị ảnh hưởng + bump version)
- [ ] Không gọi LLM API thật trong test (FakeLLM/stub)
- [ ] Code AI sinh đã đọc hiểu + có test kèm
