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

**Đang làm:** S1. H1.2 `population.py`, `demand.py` xong, chờ Tình review. Tiếp theo: H1.3 `choice.py`.

### 2026-09-30 · S0 · kiểm tra config và hàm cửa sổ/kỳ ngân sách · xong
- Nhánh/PR: `hoang/config-checks → develop1` (#1), merge `1ae4dc9`, review: Tình
- Đã làm: `config.py` kiểm `warmup_min` là bội của `block_min` (H-01), `window_min` ≤ 1440 hoặc bội của 1440 (H-02); thêm `eval_window_min(cfg)`, `budget_period_min(cfg)` (H-03); chốt L1–L13 và T-17 trong `decisions.md`; sửa `spec.md` §9, `plan.md`, `phan_cong.md` mục 6
- Test: `pytest -q` → 107 passed (+8 trong `test_config.py`)
- Lệch spec / quyết định mới: H-01, H-02, H-03
- Bàn giao: không
- Còn lại / bước tiếp: review B0; H1.1 `space.py`
- *(Mục này do Tình ghi hộ từ commit `726f662`; Hoàng sửa nếu thiếu.)*

### 2026-10-01 · S0 · hợp đồng + khung chạy được · nhận B0
- Nhánh/PR: commit `b586fa9` của Tình, vào thẳng `develop1` (không qua PR); kiểm tra sau khi đã gộp
- Đã làm: chạy phần "Người nhận kiểm tra" của B0; đọc `rng.py` (thứ tự rút số, `session_id`), `engine.py` (vòng lặp, `RunResult`, `build_context`), chữ ký trong `state.py`, và stub 7 bước của Hoàng. Chưa đọc từng dòng `budget.py`, `pricing.py`, `policies/`
- Test: `pytest -q` → 192 passed (py3.12); `tests/test_engine.py` và `tests/test_schema_contract.py` → 23 passed
- Lệch spec / quyết định mới: không; đồng ý T-19, T-20
- Bàn giao: nhận B0
- Còn lại / bước tiếp: gộp `develop1 → main` (gate P0 kèm hợp đồng); H1.1

### 2026-10-01 · H1.1 · space.py (M1) · xong
- Nhánh/PR: `hoang/space → develop1`, review: Tình
- Đã làm: `sim/space.py` (lưới hex, torus, `D`, bảng ô kề, `rings`, `T[a,b,h]`, `eta_in`, `find_pickup`, `quote_eta`; mảng chỉ đọc; giữ tên trường của hợp đồng B0); `tests/test_space.py` (+37)
- Test: `pytest -q` → 229 passed (py3.12); test chậm: không chạy. `build_space` 0,7 ms; `quote_eta` 6–15 µs mỗi lần gọi
- Lệch spec / quyết định mới: H-04 trong `decisions.md` (thêm trường vào `SpaceTime`, `find_pickup` dùng chung cho báo giá và M5)
- Bàn giao: giao B1; người nhận kiểm tra: `tests/test_space.py` pass, trong đó `test_clusters_of_seven_have_spec_sizes` cho [3, 3, 4, 6, 7, 7, 7]
- Còn lại / bước tiếp: H1.2 `population.py`, `demand.py`

### 2026-10-01 · H1.2 · population.py, demand.py (M2) · xong
- Nhánh/PR: `hoang/h1-2-demand → develop1`, review: Tình
- Đã làm: `sim/population.py` (trọng số ô, rider kèm biến ẩn, lịch ca tài xế, bảng lấy mẫu rider và ô đích; mảng chỉ đọc); `sim/demand.py` (`spawn`: Poisson theo (ô, tick), chọn rider, chọn đích, rút sẵn số theo `SESSION_DRAW_ORDER`); `tests/test_demand.py` (+30); `tests/test_engine.py` chạy khung với `demand_scale = 0`
- Test: `pytest -q` → 259 passed (py3.12); test chậm: không chạy. Đo 1 ngày mô phỏng, cấu hình mặc định, 30.397 session: `spawn` 1,56 giây (DEMAND 0,72; SESSION 0,54), `build_world` 20 ms
- Lệch spec / quyết định mới: H-05 trong `decisions.md`. Giữ một bộ sinh số cho mỗi session, không dùng SESSION_BATCH
- Bàn giao: không. Ghi chú cho Tình: `pricing.quote` (T2.1) chưa nhận session, nên engine chỉ chạy được với `demand_scale = 0` đến khi có B3
- Còn lại / bước tiếp: H1.3 `choice.py`
