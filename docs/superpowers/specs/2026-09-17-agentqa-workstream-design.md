# AgentQA — Thiết kế tổ chức dự án & phân chia workstream

- **Ngày:** 2026-09-17
- **Trạng thái:** Đã duyệt qua brainstorming (5 section, chốt từng phần)
- **Phạm vi:** Thiết kế **tổ chức** dự án — phạm vi đề tài, phân chia workstream, tổ chức repo, quy trình git, tài liệu, milestone. Thiết kế kỹ thuật chi tiết từng module sẽ nằm ở `docs/design/` (giai đoạn sau, qua writing-plans).
- **Vai trò:** W1, W2, W3 là tên gọi 3 workstream/thành viên xuyên suốt tài liệu; điền tên thật khi tạo repo.

## 1. Bối cảnh & ràng buộc

- Đồ án tốt nghiệp (HVBCVT — CNTT/HTTT), nhóm 3 người, thời lượng ~12 tuần.
- Ràng buộc từ thầy: nhóm từ 2–5 người; với 3 người thì **khối lượng/kỹ thuật phải đủ nặng và sâu cho từng người**, làm trong hơn 2 tháng.
- Cả 3 thành viên trình độ tương đương, **đều dùng AI coding assistant** để hỗ trợ viết code.
- Có ngân sách gọi LLM API; máy đủ chạy nền tảng (Chromium, song song), **không đủ mạnh chạy AI local** (Ollama chỉ là lựa chọn tiết kiệm khi dev, không dùng cho thí nghiệm chính).
- Hệ thống AgentQA: nền tảng test web bằng computer-use agent (hybrid observation a11y-first, assertion sinh thành code, self-healing đo lường được, ngân sách token cứng). 3 research question: RQ1 (hybrid vs vision-first: token/cost/time), RQ2 (self-healing khi UI đổi), RQ3 (detection/stability/cost vs baseline).
- **Giả định thiết kế:** tiêu chí "đủ nặng và sâu" được hiểu theo chuẩn khắt khe — mỗi người có một workstream kỹ thuật riêng đủ dày để tự bảo vệ trước hội đồng. Nếu thầy xác nhận nhẹ hơn thì chỉ nới ra, không phải làm lại.

## 2. D1 — Chia 3 workstream neo vào RQ

Khi viết code không còn là phần khó (nhờ AI assistant), phần được chấm dồn vào **thiết kế vấn đề + thí nghiệm + số liệu**. Do đó mỗi workstream = 1 RQ = 1 vòng đời đầy đủ: thiết kế → code lõi → thí nghiệm → số liệu → chương báo cáo.

### 2.1. W1 — Observation & Policy (RQ1)
Sở hữu: vòng đời browser session; bộ quan sát hybrid (a11y ≤ 8KB + DOM, ảnh chỉ khi cần); policy LLM chọn action; budget controller (cap token/step/run, quy tắc escalate lên vision); action executor. W1 viết luôn **chế độ vision-first** — vừa là fallback vừa là baseline RQ1.
Số liệu: token/cost/time/step-count trên suite chuẩn.

### 2.2. W2 — Verification & Healing (RQ2)
Sở hữu: `AssertionSpec` (schema + sinh assertion từ ngôn ngữ tự nhiên thành code chạy được); checker thực thi assertion; self-healing locator (ngữ nghĩa → vision); **mutation generator** (đột biến UI có kiểm soát + ground truth); metric healing (detection / false-heal / recovery).
Số liệu: suite chạy trên các biến thể UI đột biến; tỉ lệ phát hiện đúng, healing đúng, false-heal.

### 2.3. W3 — Measurement Platform (RQ3)
Sở hữu: orchestrator + run lifecycle; worker pool chạy song song; `RunTrace` thống nhất; kế toán token/cost/time; **experiment runner** (ma trận: chế độ × suite × mutation × model); lưu artifacts; reproducibility (pin model version, seed, lưu raw output); thống kê.
UI web mỏng 3 trang (trigger run / trace viewer / export) — W3 chủ trì, W1–W2 thêm view đặc thù phần mình.

### 2.4. Đối tượng test
- 1 **web app mẫu tĩnh** (HTML/JS, dữ liệu giả bằng localStorage) do nhóm tự viết, có **script sinh UI variants** — để thí nghiệm tái lập được. Dựng trong giai đoạn skeleton; taxonomy + biến thể đột biến do W2 sở hữu.
- Vài trang public chỉ để tham chiếu realism, **không dùng làm số liệu chính**.

### 2.5. Interface đóng băng
Pydantic models trong `src/agentqa/contracts/`: `ObservationSnapshot`, `Action`, `StepResult`, `AssertionSpec` / `AssertionResult`, `RunTrace`, `MutationSpec`.
Luật: đổi schema = PR có mô tả ảnh hưởng + review + bump version; conflict ở contracts cấm tự chọn phe mình.

### 2.6. Walking skeleton (W1–W2)
1 test case tiếng Việt → Chromium → PASS/FAIL + trace thô, chạy được trên máy cả 3. Chưa Redis/MinIO/Langfuse/realtime WS.

### 2.7. Anti-scope (ghi rõ vào báo cáo là "không làm")
Multi-tenant, phân quyền phức tạp, plugin CI, tích hợp bên thứ ba, public SaaS.
**Hoãn có chủ đích** (chỉ bật nếu còn thời gian, qua adapter): Redis → hàng đợi Postgres/in-process trước; MinIO → artifacts trên disk; Langfuse → trace trong Postgres; realtime WS → polling; Next.js giữ nhưng cấm vượt 3 trang ở giai đoạn lõi.

## 3. D2 — Tổ chức repo

Monorepo, một package Python duy nhất + web tách riêng:

```
AgentQA/
├─ src/agentqa/
│  ├─ contracts/   # Pydantic models chung — không phụ thuộc module nào
│  ├─ llm/         # adapter OpenAI-compatible (DeepSeek/Zen/Gemini/OpenRouter/Ollama) + đếm token — lá, dùng chung
│  ├─ agent/       # W1: observation, policy, budget, executor
│  ├─ verify/      # W2: assertion, healing, mutation generator
│  ├─ platform/    # W3: orchestrator, queue, workers, metrics, experiment runner
│  └─ api/         # W3: FastAPI (mỏng)
├─ apps/
│  ├─ web/         # Next.js mỏng: 3 trang
│  └─ demo-site/   # web app mẫu tĩnh + script sinh variants
├─ experiments/
│  ├─ rq1/ rq2/ rq3/   # config + script phân tích từng người
│  └─ (raw artifacts không commit; chỉ commit CSV/figures tổng hợp)
├─ docs/           # overview, design, adr, runbooks, weekly, report
├─ infra/          # docker-compose, scripts
└─ .github/workflows/
```

| Vùng | Chủ sở hữu | Luật phụ thuộc |
|---|---|---|
| `contracts/` | cả nhóm | đổi = PR + review + bump version |
| `agent/`, `experiments/rq1/` | W1 | chỉ import contracts, llm |
| `verify/`, `experiments/rq2/` | W2 | chỉ import contracts, llm |
| `platform/`, `api/`, `apps/web/`, `experiments/rq3/` | W3 | được import tất cả |
| `apps/demo-site/` | skeleton: cả nhóm, sau: W2 (variants) | — |
| `.github/`, `infra/` | W3 (integration owner) | — |

- Luật "chỉ import contracts" **enforce bằng import-linter trong CI**.
- CODEOWNERS route review đúng người.
- Tooling: Python + uv (1 pyproject gốc) · ruff (lint + format) · pytest · pnpm cho web · docker-compose (chỉ Postgres + app; Redis/MinIO để sau). Script chạy được cả Windows (máy dev) lẫn Linux (CI).
- Secrets: `.env.example` commit, `.env` ignore; key LLM riêng mỗi người cho dev; thí nghiệm dùng key riêng + cap chi tiêu ở console provider.

## 4. D3 — Git & review

**GitHub Flow** (main + nhánh ngắn hạn). Không Git Flow, không develop.

- `main` bảo vệ: cấm push trực tiếp, cấm force-push; vào qua PR + 1 approval + CI xanh; squash merge.
- Nhánh: `feat/w1-<desc>`, `fix/w2-<desc>`, `chore/ci-<desc>`; sống ≤ 3 ngày; rebase main mỗi ngày.
- PR discipline: 1 PR = 1 mục đích, cố gắng < ~400 dòng diff; mô tả what / why / cách tự verify; **không merge code mình không đọc hiểu**; code AI sinh phải kèm test; reviewer là owner vùng bị đụng (contracts: ai cũng review được).
- CI mỗi PR (< 5 phút): ruff · pytest unit · import-linter · build web nếu web đổi. **Cấm gọi LLM API thật trong CI** → adapter LLM phải có **chế độ replay fixture** (record 1 lần, CI phát lại).
- E2E thật (agent chạy demo-site): label `e2e` hoặc chạy đêm, không chạy mọi PR.
- Issues: label `rq1/rq2/rq3` + milestone `W1..W12`; mỗi người tự mở issue cho việc mình làm (bằng chứng phân công cá nhân cho báo cáo).
- Tag snapshot: `v0.1-skeleton` (hết W2) · `v0.5-core` (hết W8) · `v1.0-defense` (đóng băng trước bảo vệ 1 tuần).
- Ngôn ngữ: commit/PR/branch/issue tiếng Anh; docs học thuật tiếng Việt.

## 5. D4 — Tài liệu & báo cáo

**Tài liệu kỹ thuật (trong repo `docs/`):**
- `docs/overview.md` — bản handoff hệ thống, cập nhật thường xuyên (AI assistant của cả 3 đọc file này).
- `docs/adr/` — Architecture Decision Records, mỗi quyết định 1 trang (bối cảnh / quyết định / đã cân nhắc / hệ quả). Dùng để trả lời hội đồng.
- `docs/runbooks/` — setup dev; chạy 1 thí nghiệm; tái lập bảng số trong báo cáo; demo cho thầy.
- `AGENTS.md` ở root — nội quy cho AI coding assistant của cả nhóm (branch naming, luật import, lệnh test).

**Báo cáo đồ án (`docs/report/`):**
- Viết Markdown theo chương, export Word/PDF bằng pandoc khi nộp.
- Chương 4 tách 4.1 = W1, 4.2 = W2, 4.3 = W3 — mỗi người viết phần + số liệu của mình. Chương chung chia người chủ trì.
- **Truy vết số liệu:** mọi con số trong báo cáo link ngược về script + config trong `experiments/rqX/`.
- Viết song song từ W3: thí nghiệm xong → viết section đó ngay trong tuần; cấm dồn cuối kỳ; cấm copy output AI nguyên văn.
- `docs/weekly/Wxx.md` — nhật ký tuần, mỗi người ~5 dòng (làm gì / vướng gì / tuần sau).
- Trích dẫn: Zotero group library, export `.bib` vào `docs/report/bib/`.

## 6. D5 — Milestones & luật vận hành

Giả định 12 tuần, giữa kỳ ~W6; khi có mốc thật của trường thì remap tuần, không đổi cấu trúc.

| Giai đoạn | Tuần | W1 | W2 | W3 |
|---|---|---|---|---|
| Skeleton | W1–2 | browser session + quan sát thô + vòng lặp LLM đơn giản | assertion + checker cơ bản | contracts v1 + CI + trace JSON + demo-site tĩnh |
| Đào sâu | W3–5 | hybrid obs (a11y ≤ 8KB) + budget controller + action types | AssertionSpec v1 + healing v1 + taxonomy đột biến UI | orchestrator + worker pool song song + kế toán token + UI 3 trang |
| Baseline | W6–8 | vision-first hoàn chỉnh + A/B (RQ1) | mutation generator + đo healing (RQ2) | experiment runner + pipeline tái lập + bảng số tự động (RQ3) |
| Thí nghiệm chính | W9–10 | full run RQ1 | full run RQ2 | full run RQ3 + gate kiểm tra tái lập |
| Viết & băng | W11 | chương 4.1 + mock defense | chương 4.2 + mock defense | chương 4.3 + slide + tag `v1.0-defense` |
| Buffer | W12 | bugfix + rehearsal demo offline | | |

- Sản chung: suite chuẩn 10–20 kịch bản (mỗi người viết kịch bản theo mảng mình, W3 chuẩn hoá format), xong trong W3–5.
- Checkpoint giữa kỳ ~W6: demo suite v1 + **xin thầy xác nhận cấu trúc 3 workstream đủ nặng/sâu**.
- Definition of Done: `v0.1-skeleton` = 1 kịch bản chạy E2E trên máy cả 3 · `v0.5-core` = suite v1 chạy song song + 3 chế độ (hybrid / vision-first / script tĩnh) hoạt động · `v1.0-defense` = số liệu đóng băng + runbook tái lập chạy được.
- Check-in nhóm 2 lần/tuần (≤ 30 phút), mỗi người 3 câu: xong gì / kế tiếp / vướng gì — ghi `docs/weekly/`.
- Trễ mốc cá nhân > 3 ngày → báo nhóm ngay. Thứ tự cắt scope khi trễ: public sites → realtime WS → Langfuse/MinIO → Redis → bớt trang UI.
- Ngân sách: dev dùng model rẻ; full run W9–10 dùng model mạnh; cap ở console provider.
- Mock defense bắt buộc 2 lần (W11, W12): mỗi người tự bảo vệ phần mình trước 2 người kia đóng vai hội đồng.

## 7. Rủi ro & điểm cần xác nhận

| Rủi ro | Xử lý |
|---|---|
| Thầy chưa xác nhận độ sâu 3 workstream | Đưa cấu trúc này cho thầy ở W1–2, xác nhận sớm — sửa sớm rẻ hơn sửa muộn |
| Mốc thật của trường chưa biết | Dùng tuần tương đối; remap khi có lịch |
| Phụ thuộc chéo W2 (mutation) ↔ W3 (harness) | Chốt `MutationSpec` trong contracts ngay W3, trước khi hai bên code sâu |
| LLM flaky / tốn tiền | Replay fixture trong CI; model rẻ khi dev; cap ngân sách |
| AI assistant sinh code ẩu, không ai hiểu | Luật "hiểu mới merge" + test bắt buộc + import-linter + review chéo |
| Scope phình (platform phụ) | Danh sách hoãn + thứ tự cắt đã định ở mục 6 |

## 8. Tiêu chí thành công

1. Ba workstream chạy song song được nhờ contracts đóng băng sớm; không ai chờ ai quá 3 ngày.
2. Mỗi RQ có số liệu tái lập được bằng script, gắn với `experiments/rqX/`.
3. Mỗi thành viên tự bảo vệ được phần mình trong mock defense mà không cần người khác cứu.
4. `v1.0-defense` đóng băng trước bảo vệ 1 tuần; demo chạy offline được.
5. Báo cáo hoàn thành không dồn tuần cuối; mọi số liệu truy vết được.

## 9. Bước tiếp theo

Sau khi spec này được review và duyệt: chuyển sang lập **implementation plan** chi tiết (setup repo, contracts v1, walking skeleton, CI, runbook) bằng quy trình writing-plans.
