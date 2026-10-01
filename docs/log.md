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

**Đang làm:** S1 của Tình xong (T1.1–T1.4; T1.5 bỏ theo T-14), đã vào `develop1`; Hoàng kiểm B2, B4 khi pull. Tiếp theo: S2, T2.1 `pricing.py` đầy đủ (`quote`, B3).

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

### 2026-10-01 · pull develop1 + B0 chốt + kiểm B1 từ Hoàng · nhận B1
- Nhánh/PR: pull `develop1`; S0 đã vào thẳng `develop1` (`b586fa9`, không qua PR, chép từ log Hoàng); H1.1 vào qua PR #2 `hoang/space` (`c69d3fe` merge, `f413efc` H1.1)
- Đã làm: chạy phần "Người nhận kiểm tra" của B1; đọc nhanh `sim/space.py` (hex, torus, `D`, `rings`, `T[a,b,h]`, `eta_in`, `find_pickup`, `quote_eta`) và `tests/test_space.py`; đọc H-04 trong `decisions.md`
- Test: `pytest -q --basetemp=$LOCALAPPDATA/Temp/pytest-tình` → 229 passed (py3.11, 5,5 s); `tests/test_space.py` 37 passed; `test_clusters_of_seven_have_spec_sizes` cho [3, 3, 4, 6, 7, 7, 7] đúng spec. Thư mục tmp mặc định `C:\Users\E7480\AppData\Local\Temp\pytest-of-E7480` bị khóa quyền nên phải truyền `--basetemp`
- Lệch spec / quyết định mới: không; đồng ý H-04 (thêm trường vào `SpaceTime`, `find_pickup` dùng chung cho báo giá và M5)
- Bàn giao: nhận B1; B0 không mở PR theo kế hoạch (S0 ở trên nói sẽ mở PR, kết cục commit thẳng)
- Còn lại / bước tiếp: T1.1 `budget.py` đầy đủ (enforce, bất biến theo kỳ, reset) + test ledger trong `test_pricing.py`; sau đó T1.2 `monitor.py`

### 2026-10-01 · T1.1 · budget.py đầy đủ · xong
- Nhánh/PR: commit thẳng `develop1` (không PR, như B0); Hoàng kiểm B2 sau khi pull
- Đã làm: `sim/budget.py`: thêm `resolve_budget_usd(cfg, pilot_spent_by_period_usd)` (B theo `budget.mode`: `fixed` → `fixed_usd`; `fraction_of_all_on` → `fraction × trung bình chi tiêu mỗi kỳ` của pilot, spec §4.3), `check_invariant` luôn bắt tổng âm kể cả khi `enforce=false`, kiểm `warmup_s ≥ 0`; API sổ (`reserve/commit/settle/release_*`, `period_of`, `totals`) giữ nguyên hợp đồng B0. "Reset ngày" = mỗi kỳ có sổ riêng theo T-03, không reset lúc 00:00. `tests/test_pricing.py` (+5): kỳ chéo d→d+1 và cool-down, kỳ mới có đủ B, sổ dựng từ `Clock` (2 ngày default và tiny 120 phút), bất biến dưới 6.000 bước ngẫu nhiên có sổ đối chiếu độc lập (2.957 session, 721 bị chặn, 3.043 chuyển trạng thái), `resolve_budget_usd`
- Test: `pytest -q --basetemp=$LOCALAPPDATA/Temp/pytest-tình` → 234 passed (py3.11, 5,3 s); test chậm: không chạy
- Lệch spec / quyết định mới: không
- Bàn giao: giao B2; người nhận kiểm tra: `pytest -q tests/test_pricing.py` pass (23 test), API đúng docstring các stub `choice.py`/`trips.py`/`cancel.py` (`commit`/`release_reserved` ở bước 6, `settle` ở bước 1, `release_committed` ở bước 3/8)
- Còn lại / bước tiếp: test "bất biến 1 ngày trên engine thật" để S3 (T3.1) khi có B5; T1.2 `monitor.py`

### 2026-10-01 · T1.2 · monitor.py: công bố theo slot, lag, hàng đợi không nhìn trước · xong
- Nhánh/PR: commit thẳng `develop1` (không PR); Hoàng kiểm khi pull
- Đã làm: `sim/monitor.py`: `publish` bắt buộc đúng cuối slot (`published_at_s = (slot+1)·slot_s`, sai → `ValueError`); `view(k)` chỉ tạo được khi slot k−1 là slot vừa công bố (slot k đã công bố → `LookAheadError`, thiếu slot → `RuntimeError`) và không snapshot nào công bố sau đầu slot k (assert hàng đợi spec §4.11); thêm điểm ghi bộ đếm T-15 `on_offers/on_requests/on_matched/on_abandoned/on_cancelled/on_completed(acc, pu_cell, …)` dùng `np.add.at` để nhiều sự kiện cùng ô cùng tick cộng dồn đúng; `n_sessions` do `demand.spawn` cộng (H-05 d), monitor không cộng lại. `tests/test_monitor.py` 5 → 13 test: trung bình theo tick, slack `inf`/utilization NaN khi ô trống, bộ đếm giả theo ô đón rồi reset, lag ngày NaN suốt ngày 1 và đúng slot k−96 suốt ngày 2 (qua store và qua `view.lag_day`), view chỉ thấy `published_at_s ≤ đầu slot k`, publish sai giờ/sai thứ tự/trùng bị từ chối, engine stub công bố đủ slot đúng thứ tự (`demand_scale = 0` đến khi có B3)
- Test: `pytest -q --basetemp=$LOCALAPPDATA/Temp/pytest-tình` → 272 passed (py3.11, 14,6 s); `test_monitor.py` 13 passed; test chậm: không chạy
- Lệch spec / quyết định mới: không. Làm rõ T-15: `n_offers` = session có `arm = 1` (voucher thật sự được phát), đếm theo `open_time`; `slack_cap` để chính sách `ar` tự áp (spec §6), log giữ `inf`
- Bàn giao: không (monitor nằm trong B3, giao giữa S2 cùng `pricing.py`). Nhận code H1.2 của Hoàng (PR #3, review: Tình) khi pull: đọc `demand.py`, H-05; `test_demand.py` 30 passed; `spawn` chỉ dùng `rng_for`, không đọc chính sách/snapshot; không phản đối
- Còn lại / bước tiếp: T1.3 `tests/fakes.py`, `policies/scores.py` + test

### 2026-10-01 · T1.3 · scores.py + đồ giả · xong
- Nhánh/PR: commit thẳng `develop1` (không PR); Hoàng kiểm khi pull
- Đã làm: `sim/policies/scores.py`: `random` → `u_score` rút sẵn (T-07), `heuristic_low_freq` → `−x_freq`, `load_score_fn` (tên có sẵn hoặc `"module:function"`), `import_callable` (nạp động, báo `ValueError` rõ khi sai spec/thiếu module/thiếu hàm/không gọi được), `score_batch` kiểm `s_hat` [n], đầu ra [n] kiểu số, ép float32. `tests/fakes.py`: `make_batch(x_freq=…)`, `fake_score` (nạp qua `"tests.fakes:fake_score"`), `make_run_result`, `fake_run` (engine giả tất định: bướu throughput kiểu WGC theo `demand_scale`, slack giảm/ETA tăng theo cầu, jitter theo seed từ luồng DEMAND nên giống nhau giữa chính sách, `profile` ghi lại config engine nhận được). `tests/test_policies.py` +3
- Test: `pytest -q tests/test_policies.py` → 15 passed; toàn bộ xem T1.4
- Lệch spec / quyết định mới: T-21 (`s_hat` theo session, một loader dùng chung cho score_fn và engine)
- Bàn giao: không
- Còn lại / bước tiếp: T1.4

### 2026-10-01 · T1.4 · runner.py khung + throughput_curve + cli · xong
- Nhánh/PR: commit thẳng `develop1` (không PR); Hoàng kiểm B4 khi pull
- Đã làm: `sim/runner.py`: `run_id` (`<mode>-<config_hash>-<policy>-<theta>-<seed>`), `seeds_for` (`run_seed + i`), `Job` (chỉ dữ liệu pickle được), `execute_job` (worker dựng world từ `world_seed`, `make_policy`, nạp engine từ chuỗi `"module:function"`), `run_jobs` (pool `spawn`, kết quả theo thứ tự job, `n_procs` từ `runner.n_procs`/số lõi, 1 job hoặc 1 proc thì chạy inline), `policy_results_table`, `throughput_curve_table`, `throughput_config` (T-08: all_off, `always_on`, `hour_profile` và `speed_factor_by_hour` hằng tại `reference_hour`), `throughput_jobs`, `run_throughput_curve`, `summarize_throughput`, `run_mode` (mode khác → `NotImplementedError("T2.4")`). `sim/logger.py` tối thiểu: `RESULTS_TABLES` (cột + dtype của `results/policy_results`, `results/throughput_curve`), `cast_table`, `write_results`. `sim/cli.py`: nối `run_mode`, `--out` mặc định `runs/<mode>-<hash>`, in bảng tóm tắt; mode chưa có → exit 1. `tests/test_runner.py` (+14, trên engine giả: thứ tự/tất định, pool spawn == inline, cấu hình T-08 engine nhận được, parquet đúng cột/dtype, bướu A1 trên bảng tóm tắt), `tests/test_schema_contract.py` +1 (bảng results khớp `schema.md`), `tests/test_cli.py` 5 (throughput_curve chạy engine thật với `demand.base_sessions_per_cell_h=0` vì `quote` chưa nhận session, H-05 f)
- Test: `pytest -q --basetemp=$LOCALAPPDATA/Temp/pytest-tình` → 291 passed (py3.11, 22,0 s); `test_runner.py` 14 passed (3,4 s, gồm pool spawn 2 proc); `test_cli.py` 5 passed; test chậm: không chạy
- Lệch spec / quyết định mới: không. Câu hỏi mở Q17 (`evaluate` dùng `n_seeds` nào; đề xuất `sweep.n_seeds`), chặn T2.4, không chặn T1.4
- Bàn giao: giao B4; người nhận kiểm tra: `pytest -q tests/test_runner.py tests/test_cli.py` pass; `python -m sim run --mode throughput_curve --config config/default.yaml --config tests/fixtures/tiny.yaml --set demand.base_sessions_per_cell_h=0 --set runner.n_procs=1 --out runs/thử` ghi `results/throughput_curve.parquet` đúng cột `schema.md`
- Còn lại / bước tiếp: S2 — T2.1 `pricing.quote` (B3), rồi T2.2 `experiment.py`, T2.3 chính sách, T2.4 runner các mode còn lại (cần chốt Q17)

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
