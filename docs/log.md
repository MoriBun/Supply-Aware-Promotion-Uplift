# Nhật ký công việc

Mỗi người một mục. Thêm mục con **ở cuối mục của mình**, cập nhật dòng "Đang làm" ở đầu mục. Không sửa mục của người kia, không sửa mục cũ (sai thì thêm mục "đính chính"). Quy tắc và mẫu đầy đủ: `CLAUDE.md`, phần "Nhật ký công việc".

Mẫu:

```
### YYYY-MM-DD · <task> · <tên ngắn> · <xong | dở (chờ …) | hủy | nhận B-x | gate Px đạt/không đạt>
- Nhánh/PR:
- Đã làm:
- Test:
- Lệch spec / quyết định mới:
- Bàn giao:
- Còn lại / bước tiếp:
```

---

## 1. Tình

**Đang làm:** S0, chờ Hoàng review PR hợp đồng (B0). Tiếp theo: T1.1 `budget.py` đầy đủ.

### 2026-09-30 · P0 · khung dự án · xong
- Nhánh/PR: commit `c1eca8a` thẳng vào `develop1` (chưa có quy trình PR)
- Đã làm: `pyproject.toml`, `.gitignore`, `.gitattributes`, `README.md`; `sim/config.py` (YAML nhiều lớp, khóa lạ báo lỗi, `--set`, `config_hash`), `sim/rng.py` (`rng_for`, BLAKE2b, luồng WORLD theo `world_seed`), `sim/cli.py` rỗng; stub 25 module theo spec §3; `.venv` Python 3.11
- Test: `pytest -q` → 90 passed (py3.11 và py3.13)
- Lệch spec / quyết định mới: L1–L10 trong `decisions.md`; đổi tên hai file docs (L10)
- Bàn giao: không
- Còn lại / bước tiếp: Hoàng review P0 (gate P0), gộp `develop1 → main`

### 2026-09-30 · kế hoạch · phân công hai người theo sprint · xong
- Nhánh/PR: commit `f19070b`, `8b1d2ca` vào `develop1`
- Đã làm: `docs/phan_cong.md` (S0–S6, bàn giao B0–B8, sở hữu file, test theo sprint); sửa `plan.md`, `CLAUDE.md` cho phép làm song song; `decisions.md` L11–L13, Q13–Q16; trang artifact để gửi Hoàng và mentor
- Test: không đổi code
- Lệch spec / quyết định mới: L11 (`budget.py` tách riêng), L12 (một lớp voucher ở bước 5), L13 (quy tắc song song)
- Bàn giao: không
- Còn lại / bước tiếp: chốt câu hỏi mở Q1–Q16

### 2026-09-30 · quyết định · chốt Q1–Q16 · xong
- Nhánh/PR: đã vào `develop1` cùng các commit trên
- Đã làm: `decisions.md` T-01…T-18; sửa `spec.md` (15 chỗ), `tests.md`, `schema.md` cho khớp; thêm khóa `time.window_min`, `supply.shift_mode`, `throughput.*`, `runner.n_procs` vào `default.yaml` + `config.py`; `tiny.yaml` dùng `window_min: 120`
- Test: `pytest -q` → 99 passed
- Lệch spec / quyết định mới: T-01…T-18 (T-03 kỳ ngân sách và T-12 all_on có ngân sách là hai điểm dễ tranh luận)
- Bàn giao: không
- Còn lại / bước tiếp: Hoàng đọc và phản đối trong S0 nếu không đồng ý; gửi mentor T-03, T-12, T-14

### 2026-09-30 · S0 · PR hợp đồng + khung chạy được · dở (chờ review B0)
- Nhánh/PR: chưa commit, đang trên working tree `develop1`; sẽ mở `tinh/s0-contract → develop1`, review: Hoàng
- Đã làm: `state.py` (enum, `SESSION_COLUMNS`/`ORDER_COLUMNS`, `SoABuffer`, `DriverState`, bộ đếm, `Clock`, `SimContext`, `decode_codes`); `rng.py` (thứ tự rút số, `session_id`, `CellSlotKind`); `budget.py` (ledger theo kỳ, cent nguyên); `policies/base.py` (`SessionBatch`, `CellDecision`, `OfferDecision`, `SnapshotStore/View`, `LegacyHiddenView`, `Policy`); `pricing.py` (giá, voucher, `VoucherLayer.decide`); `monitor.py` (accumulate/publish/view); `engine.py` (`build_context`, `run` 10 bước, `RunResult`); `policies/fixed.py`, factory; `space.py`/`population.py` stub có shape thật; 7 bước của Hoàng là stub `step(ctx, t)`; `tests/fakes.py` (`make_batch`, `make_context`, `with_forbidden`…)
- Test: `pytest -q` → 192 passed (py3.11 và py3.13); test mới: `test_state`, `test_policies`, `test_pricing`, `test_monitor`, `test_engine`, `test_schema_contract` (+8 trong `test_rng`)
- Lệch spec / quyết định mới: T-19 (nội dung hợp đồng), T-20 (giữ `SimContext`, `budget_blocked` ở `VoucherOutcome`, cột chuỗi là mã int8)
- Bàn giao: giao B0 khi PR được duyệt; người nhận kiểm tra: `pytest -q`, `tests/test_engine.py`, `tests/test_schema_contract.py`
- Còn lại / bước tiếp: commit + mở PR; sau B0 vào T1.1

---

## 2. Hoàng

**Đang làm:** S0, review PR hợp đồng của Tình (B0). Tiếp theo: H1.1 `space.py`.

### 2026-09-30 · S0 · kiểm tra config và hàm cửa sổ/kỳ ngân sách · xong
- Nhánh/PR: `hoang/config-checks → develop1` (#1), merge `1ae4dc9`, review: Tình
- Đã làm: `config.py` kiểm `warmup_min` là bội của `block_min` (H-01), `window_min` ≤ 1440 hoặc bội của 1440 (H-02); thêm `eval_window_min(cfg)`, `budget_period_min(cfg)` (H-03); chốt L1–L13 và T-17 trong `decisions.md`; sửa `spec.md` §9, `plan.md`, `phan_cong.md` mục 6
- Test: `pytest -q` → 107 passed (+8 trong `test_config.py`)
- Lệch spec / quyết định mới: H-01, H-02, H-03
- Bàn giao: không
- Còn lại / bước tiếp: review B0; H1.1 `space.py`
- *(Mục này do Tình ghi hộ từ commit `726f662`; Hoàng sửa nếu thiếu.)*
