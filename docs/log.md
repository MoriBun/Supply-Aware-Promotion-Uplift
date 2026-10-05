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

**Đang làm:** S4 đã gộp vào `develop` (PR #12; PR #13 của Hoàng cũng đã gộp, `develop1` ở `723a994`). Gate P6 đạt theo quyết định T-31 của Tình, **chờ mentor xác nhận**. Rà soát kết quả simulator xong: ba câu hỏi mở Q26–Q28 chờ Tình, Hoàng và mentor; mục log và `decisions.md` của lần rà soát **chưa commit** (Tình tự commit). Còn lại của S4: gắn tag dữ liệu; báo mentor T-31, Q24, Q26–Q28. Tiếp theo: S5, T5.1 bảng N/V dưới cùng B (random, heuristic; τ̂ khi có B8).

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

### 2026-10-01 · S1 · nhận H1.3, H1.4 của Hoàng (PR #5 `develop2 → develop`) · nhận
- Nhánh/PR: pull `develop` (`7636d01`) vào `develop1`
- Đã làm: đọc `choice.py` (H-06: voucher trong logit lấy từ `voucher_cents`, `p_request_treat` dùng cùng cách làm tròn; `decide` cộng `waiting`, `n_requests`; session bị chặn quyết định như không voucher), `supply.py` (H-08), đổi quy trình nhánh H-07; chạy `test_choice.py` (18) và `test_supply.py` (12) trong bộ test chung
- Test: `pytest -q` → 321 passed trước khi làm S2 (py3.11)
- Lệch spec / quyết định mới: không; đồng ý H-06, H-07, H-08
- Bàn giao: nhận (không có mã B); `pricing.quote` (T2.1) viết theo đúng cột mà `choice.decide` đọc (`quoted_fare_usd`, `quoted_eta_min`, `voucher_cents`)
- Còn lại / bước tiếp: S2

### 2026-10-01 · T2.1 · pricing.quote + lớp voucher đầy đủ · xong (chưa commit)
- Nhánh/PR: `develop1`, chưa commit (Tình commit); vào PR S2 `develop1 → develop`
- Đã làm: `sim/pricing.py`: `VoucherLayer.quote` — giá gốc từ `T[pu, do, h]`, ETA báo theo quy tắc M5 trên `cells.idle` thật (`quote_eta_by_cell`, một lần tìm xe cho mỗi ô có session), dựng `SessionBatch` chỉ cột quan sát + 4 uniform, gọi `decide` (chính sách → ngân sách theo `session_id`), ghi lại đủ cột bước "quote" của `schema.md` kể cả trường thí nghiệm (`cluster_id`, `block`, `in_burnin` theo `open_time`), cộng `n_offers` (T-15). `policies/fixed.py` giữ nguyên S0. `tests/test_pricing.py` +6: giá/ETA/cột với all_off, `quote_eta_by_cell` theo idle thật, all_on cấp voucher và đếm offer, chặn ngân sách theo thứ tự `session_id` trong tick, CRN all_on/all_off (A2(c) mức session), engine chạy cầu thật qua lớp voucher (B3: all_off cho N, V = 0 như stub, all_on đặt nhiều hơn, cùng seed cho cùng kết quả)
- Test: `pytest -q tests/test_pricing.py` → 29 passed; toàn bộ xem T2.4
- Lệch spec / quyết định mới: không (T-25c cho `in_burnin` theo session)
- Bàn giao: giao B3 (`pricing.py` + `fixed` + `monitor.py`); người nhận kiểm tra: `pytest -q tests/test_pricing.py tests/test_monitor.py`; `test_engine_runs_with_real_demand_through_the_voucher_layer` pass; sau đó bỏ `demand_scale = 0` trong `test_engine.py` được
- Còn lại / bước tiếp: Tích hợp 1 khi có B5

### 2026-10-01 · T2.2 · experiment.py (M10) · xong (chưa commit)
- Nhánh/PR: `develop1`, chưa commit; PR S2
- Đã làm: `sim/experiment.py`: `cluster_ids` (cấp 1 / 7 / all; tâm `(q+5r) mod 7 = 0`, gán ô vào tâm gần nhất, hòa lấy id nhỏ), `block_of`, `in_burnin` (T-15, vector hóa), `cluster_on` (CELLSLOT `(SWITCHBACK, mã cấp, cụm, block)`), `rider_arm` (RIDER `(rider_id)`), `effective_level` (global = một cụm). `tests/test_experiment.py` (+7): cụm phủ kín không chồng, R = 3 ra [3, 3, 4, 6, 7, 7, 7], mỗi ô cách tâm ≤ 1; block/burn-in; tỷ lệ bật ≈ p_on ±3% trên 2.000 block, tất định theo seed, mã cấp nằm trong khóa; arm rider cố định, ≈ p_on ±2% trên 20.000 rider
- Test: `pytest -q tests/test_experiment.py` → 7 passed
- Lệch spec / quyết định mới: T-25a
- Bàn giao: không
- Còn lại / bước tiếp: T2.3

### 2026-10-01 · T2.3 · legacy.py, threshold.py, policies/experiment.py, factory · xong (chưa commit)
- Nhánh/PR: `develop1`, chưa commit; PR S2
- Đã làm: `LegacyPolicy` (luật slack trễ + ε từ CELLSLOT, nhắm rider qua `LegacyHiddenView` với `u_latent`, lát explore; `propensity` NaN/`explore_p`/0 theo T-24), `ThresholdPolicy` (ŝ `persistence`/`ar` có chặn trần, `promo_on = not (ŝ < θ)`, hysteresis, điểm `score_fn(batch, ŝ theo session)` ≥ κ; κ = −∞ khi config `auto`; chỉ `slack`, Q19), `ExperimentPolicy` (switchback cụm/toàn hệ, `rider_ab`), `make_policy(cfg, world, rng, theta, kappa)`. `tests/test_policies.py` +12: θ = 0 không cắt, θ lớn cắt mọi ô hữu hạn, inf/NaN giữ bật; điểm/κ/NaN; score_fn thấy ŝ của ô từng session; hysteresis 19 → 0 lần đổi; `ar` chặn inf và dùng lag slot ngày đầu; legacy khớp số rút CELLSLOT và chỉ dùng luồng này; nhắm theo `u_latent`; explore bất kể trạng thái ô; experiment policy khớp M10
- Test: `pytest -q tests/test_policies.py` → 27 passed
- Lệch spec / quyết định mới: T-23 (a–d), T-24, T-25 (b, d); câu hỏi mở Q19
- Bàn giao: không
- Còn lại / bước tiếp: T2.4

### 2026-10-01 · T2.4 · runner: evaluate, gte, sweep_theta, calibrate_budget, κ auto, generate · xong (chưa commit)
- Nhánh/PR: `develop1`, chưa commit; PR S2
- Đã làm: `sim/runner.py`: `calibrate_budget` (pilot all_on seed `run_seed + pilot_seed_offset`, B = `fraction × chi tiêu trung bình mỗi kỳ`; `fixed` → `fixed_usd`), `kappa_from_pilot` + `kappa_auto` (T-23e), `resolve_kappa`, `evaluate` (`sweep.n_seeds`, T-22), `gte` + `gte_summary` (ghép cặp theo seed), `sweep_theta` (một κ mỗi θ, cùng B) + `theta_sweep_table` (`N_se`, `is_argmax`), `generate` (`generate.days`, legacy có B / experiment không, log full; bảng observed/hidden/market để T3.2), `calibrate_budget_table`, `metadata_table` → `meta/run_metadata` (gồm `config_yaml`, `git_sha`, κ, B). `sim/logger.py`: thêm `theta_sweep`, `META_COLUMNS`, `write_metadata`, `git_sha`. `sim/cli.py`: mọi mode chạy được, in tóm tắt; `NotImplementedError`/`ValueError` → exit 1. `tests/fakes.py`: `fake_run` theo chính sách (tỷ lệ phát, `offer_*` cho κ auto, cực trị nhẹ tại θ = 0,5). `tests/test_runner.py` +10, `tests/test_cli.py` 7 (gte và sweep chạy engine thật với cầu thật trên tiny), `tests/test_schema_contract.py` kiểm thêm `theta_sweep`, `run_metadata`
- Test: `pytest -q --basetemp=$LOCALAPPDATA/Temp/pytest-tình` → 358 passed (py3.11, 36,0 s); `test_runner.py` 24, `test_cli.py` 7; test chậm: không chạy
- Lệch spec / quyết định mới: T-22 (chốt Q17), T-23 (e, f)
- Bàn giao: không
- Còn lại / bước tiếp: Tích hợp 1 + Gate P2 khi Hoàng xong H2.1–H2.4 (B5): bỏ `demand_scale = 0` ở `test_engine.py`, chạy A2(a)(c), `throughput_curve` thật; T3.2 logger đủ bảng để `generate` ghi observed/hidden/market

### 2026-10-01 · S2 · nhận B5 (`engine.run` thật, PR #7 `develop2 → develop`) và Gate P2 · nhận B5, gate P2 đạt (ý kiến Tình)
- Nhánh/PR: pull `develop` (`b815fe8`) vào `develop1`
- Đã làm: đọc H-09…H-13, `engine.py` (không đổi so với hợp đồng), `trips.py`/`cancel.py` (gọi `settle`/`release_committed` đúng chỗ, dùng `MarketMonitor.on_*`), 14 test tích hợp của Hoàng (chạy trên `pricing.quote` thật). Hoàng sửa 2 test của tôi theo hành vi thật (H-13b): đồng ý. Gate P2 (số liệu trong mục của Hoàng, cấu hình chưa hiệu chỉnh): đường throughput có đỉnh tại `demand_scale` 1,25 và giảm còn 0,83 × đỉnh; slack < 0,06 ở vùng giảm; tiêu chí 4 của A1 lệch nhẹ (ETA nhảy 3,44 phút giữa 1,25 và 1,5, đúng chỗ slack sụp 0,23 → 0,06; vài bước giảm 0,025 phút ở vùng bão hòa). Theo `plan.md` P2 là gate "xem đồ thị có đoạn giảm", còn 4 tiêu chí A1 kiểm ở P3 sau hiệu chỉnh → **Tình: gate P2 đạt**; đề nghị H3.2 xem lại tiêu chí 4 sau hiệu chỉnh (thêm mốc 1,375 nếu cần), nếu vẫn > 3 phút thì báo mentor, không nới tiêu chí
- Test: `pytest -q` → 414 passed (py3.11, 50 s) trước khi làm S3
- Lệch spec / quyết định mới: không; đồng ý H-09…H-13
- Bàn giao: nhận B5
- Còn lại / bước tiếp: S3

### 2026-10-01 · T3.1 · tích hợp P4 trên engine thật · xong (chưa commit)
- Nhánh/PR: `develop1`, chưa commit (Tình commit); PR S3 `develop1 → develop`
- Đã làm: `tests/test_acceptance.py` (+15, file A2/A3 của Tình): bất biến `spent + committed + reserved ≤ B` kiểm **sau bước 9 của mọi tick** trong 1 ngày `default.yaml`, all_on có B từ `calibrate_budget` thật (B = 0,3 × chi tiêu all_on; chặn nhiều hơn phát); sổ sau lượt chạy: không voucher → không dòng, không đặt → RELEASED, Completed → SPENT, Abandoned/Cancelled/Truncated → RELEASED, `committed = reserved = 0` ở cả hai kỳ, `spent` kỳ 0 = tổng voucher order hoàn thành trong cửa sổ, kỳ −1 = warm-up; session bị chặn quyết định theo `p_request_control` (H-06d); 2 ngày tiny với B nhỏ: hai kỳ đều chi, đều ≤ B, đều có chặn và có phát lại ("reset ngày", T-03); `smoke_day` cho legacy, threshold, experiment (N > 0, không order mở, không Truncated, ≤ 30 s) kèm kiểm tra cơ chế/propensity (legacy: explore ≈ 5%, propensity NaN đúng chỗ nhắm rider; threshold: `promo_on = not (ŝ < θ)`, 0 < share_cells_off < 1; experiment: cụm 0–6, block ≥ 1, burn-in ≈ 25%, propensity = p_on); A2(a) cùng seed cùng kết quả cho 3 chính sách; A2(c) 3 chính sách gặp cùng session
- Test: `pytest -q tests/test_acceptance.py` → 15 passed (43 s: 4 lượt 1 ngày thật + pilot); toàn bộ xem T3.3
- Lệch spec / quyết định mới: không
- Bàn giao: không
- Còn lại / bước tiếp: A2(b), A3 ở T4.2 (cần κ auto trên engine thật và B sau hiệu chỉnh)

### 2026-10-01 · T3.2 · logger.py đủ bảng · xong (chưa commit)
- Nhánh/PR: `develop1`, chưa commit; PR S3
- Đã làm: `sim/logger.py`: `RUN_TABLES` (cột + dtype trên đĩa của `observed/riders|sessions|orders`, `market/slot_snapshots`, `hidden/riders_hidden|sessions_hidden`, suy từ `SESSION_COLUMNS`/`ORDER_COLUMNS`/`SNAPSHOT_FIELDS`), `sessions_frames`/`orders_frame`/`riders_frames`/`snapshots_frame` (giải mã cột mã sang string, float32 cho số rút sẵn, `run_id` + `seed` ở mọi bảng), `run_tables`, `write_run`; assert lúc import: không cột ẩn nào trong bảng observed/market. `sim/runner.py`: `write_full_runs` — `generate` ghi thẳng dưới `--out`, các mode nhiều seed với `--log-level full` ghi `<out>/runs/<run_id>/` (T-26). `tests/test_logger.py` (+13): `generate` 2 ngày tiny legacy trên engine thật → đủ 6 bảng + results + meta; cột và kiểu Arrow trên đĩa khớp `schema.md` cho từng bảng; **`test_no_hidden_leak`** (không cột ẩn ở observed/market, `p_request_*`/`direct_request_effect_fixed_market`/`propensity_true` chỉ ở hidden); số dòng, khóa lượt chạy, hai kỳ ngân sách; cột mã là string; giá trị khớp buffer; nhiều seed mỗi lượt một thư mục
- Test: `pytest -q tests/test_logger.py` → 13 passed (7,5 s)
- Lệch spec / quyết định mới: T-26
- Bàn giao: không (B7a dùng `generate` này ở T4.1)
- Còn lại / bước tiếp: T3.3

### 2026-10-01 · T3.3 · khung đánh giá tuần 5 (`analysis/`) · xong (chưa commit)
- Nhánh/PR: `develop1`, chưa commit; PR S3
- Đã làm: `analysis/io.py` (`load_run` không bao giờ trả `hidden/`, `load_hidden` riêng, `completed_outcome`), `analysis/metrics.py` (`value_table`: N/V/chi tiêu với SE và CI theo seed; `paired_difference` ghép cặp theo seed cho A2(b); `bootstrap_mean_ci`; `uplift_curve` Qini/uplift thô gộp điểm trùng; `qini_auuc`), T-27. `tests/test_analysis.py` (+10): ví dụ tay (Qini = 0,875, hệ số 0,375), gộp trùng, điểm hằng = đường ngẫu nhiên, NaN khi thiếu nhánh, điểm đúng uplift thật thắng điểm nhiễu trên 20.000 mẫu mô phỏng, CI/hiệu ghép cặp, nạp lượt chạy thật (tiny, all_on) không có bảng ẩn, nối `x_freq` từ `observed/riders`
- Test: `pytest -q --basetemp=$LOCALAPPDATA/Temp/pytest-tình` → 452 passed (py3.11, 98 s; từ 414); `test_analysis.py` 10 passed; test chậm: không chạy
- Lệch spec / quyết định mới: T-27; chỉ dùng numpy/pandas, chưa thêm extras `[analysis]` (pyproject là file chung, để khi cần sklearn/lightgbm ở S5)
- Bàn giao: không
- Còn lại / bước tiếp: PR S3; S4: T4.1 (cần B6), T4.2

### 2026-10-02 · S3 · nhận B6 (`default.yaml` đã hiệu chỉnh, PR #9) và Gate P3 · nhận B6, gate P3 đạt (ý kiến Tình)
- Nhánh/PR: fast-forward `develop` (`930875e`) vào `develop1`
- Đã làm: chạy phần "Người nhận kiểm tra" của B6; đọc H-14…H-18 và thay đổi của Hoàng trong file của tôi (`monitor.py`: slack = 0 khi ô không có xe rảnh; 3 test bỏ giá trị ghi cứng). Rà `threshold.py`, `legacy.py` với H-14: không phải sửa code (ŝ = 0 < θ → tắt; θ = 0 vẫn không cắt ô nào), ghi T-28 đính chính T-23b/T-24b
- Test: `pytest -q` → 452 passed, 3 deselected (py3.11, 102 s); `pytest -q -m slow tests/test_acceptance_core.py` → 3 passed (A1, A5, CAL; 204 s vì chạy cùng lúc với việc sinh dữ liệu; phần A5 gồm pilot + 3 lượt hết 27 s). `config_hash(default.yaml) = cb27f5348011` khớp H-17
- Lệch spec / quyết định mới: T-28; đồng ý H-14…H-18
- Bàn giao: nhận B6. Gate P3: A1 đạt 4/4, A5 và CAL trong khoảng trên máy tôi → **Tình: gate P3 đạt**
- Còn lại / bước tiếp: T4.1

### 2026-10-02 · T4.1 · calibrate_budget lại + sinh dữ liệu B7a · xong (chưa commit)
- Nhánh/PR: `develop1`, chưa commit (Tình commit); PR S4 `develop1 → develop`
- Đã làm: `calibrate_budget` trên config mới → **B = 5.545,80 USD/kỳ** (pilot all_on seed 9000). `generate` 28 ngày, `run_seed = 0`, vào `runs/b7a/`: `legacy_28d` (có B), `switchback_c1_28d`, `switchback_c7_28d`, `switchback_all_28d`, `rider_ab_28d` (không ngân sách); `gte` 10 seed. Mới: `analysis/check_dataset.py` (schema + kiểu trên đĩa, không rò cột ẩn, khớp chéo session/order/results, `config_hash`; in bảng markdown), `analysis/check_budget.py` (báo cáo chi tiêu theo kỳ so với B; sửa giả định sai "session bị chặn thì ô phải bật": lát explore của legacy phát bất kể ô), `docs/datasets.md` (bảng bộ dữ liệu, lệnh sinh lại, cách kiểm), `tests/test_analysis.py` +3, `sim/cli.py` sửa một dòng thông báo cũ
- Test: `pytest -q --basetemp=$LOCALAPPDATA/Temp/pytest-tình` → 455 passed, 3 deselected (89 s). `check_dataset` trên 7 thư mục: OK. `check_budget` trên `legacy_28d`: 28 kỳ đều ≤ B (lớn nhất 5.545,68), 450 session bị chặn
- Số liệu: mọi bộ `generate` có 718.749 session (CRN giữa các thiết kế), không order Truncated. N hoàn thành trong 28 ngày: legacy 108.410 (chi 152.342,5 USD, phát 23,2%); switchback cụm 1: 114.932; cụm 7: 114.040; all: 113.990; rider_ab: 115.116. GTE (10 seed, 1 ngày): N_on 4.652,5, N_off 3.439,6, **GTE = +1.212,9** (SE 14,2). Thời gian: 240–272 giây mỗi bộ, 5 bộ song song; tổng 266 MB
- Lệch spec / quyết định mới: T-29 (quy ước B7a: cùng seed, thư mục, cách tái lập)
- Bàn giao: giao B7a; người nhận kiểm tra: sinh lại theo lệnh trong `docs/datasets.md` (hoặc nhận bản sao `runs/b7a`), `python -m analysis.check_dataset …` báo OK, số session/order/N khớp bảng. Sự cố: lệnh nền đầu tiên sai cú pháp shell làm 4 bộ thí nghiệm không khởi động; phát hiện sau ~1 phút qua log, chạy lại bằng script, không có dữ liệu sai nào được ghi
- Còn lại / bước tiếp: T4.2 (κ auto, A2(b), A3, sweep θ, Gate P6); T4.3 sinh lại legacy nếu B đổi, B7b

### 2026-10-02 · T4.2 · P6: κ auto, A2(b), A3, sweep θ, đường N(π_θ) · dở (chờ mentor, Q23) · gate P6 không đạt
- Nhánh/PR: `develop1`, chưa commit (Tình commit); PR S4
- Đã làm: `tests/test_acceptance.py` +3 test `slow` và hàm đo (`kappa_auto_spend`, `a2b_variances`, `a3_switches`); `analysis/plots.py` (`plot_theta_sweep`, `plot_throughput`, CLI) + 1 test; `pyproject.toml` thêm extra `analysis = ["matplotlib>=3.8"]` (file chung, T-30, chờ Hoàng duyệt). Chạy sweep tham chiếu `runs/p6/sweep_theta` (12 θ × 10 seed, 271 s) và 5 sweep chẩn đoán `runs/p6/sens_*` (5 seed)
- Test: `pytest -q` → 456 passed, 6 deselected (py3.11, 108 s); `pytest -q -m slow tests/test_acceptance.py` → 3 passed (190 s)
- Nghiệm thu (`config_hash = cb27f5348011`, B = 5.545,80): **κ auto đạt**: κ = −2,748, chi/B = 0,99991; 0,99995; 0,99999 (yêu cầu 0,85–1,0). **A2(b) đạt** (20 seed, all_on có B so với threshold θ = 0,3 có B): Var CRN 1.434,45; Var seed độc lập 5.925,40; tỷ lệ 0,242 ≤ 0,5; N trung bình 3.700,4 so với 3.891,8. **A3 (thông tin):** θ = 0,35, h = 0: 25,97; 26,97; 26,16; 26,08; 23,97 lần/ô/ngày, trung vị 26,08 > 12 → h = 0,1: trung vị 25,38 (N 3.882,8 → 3.886,6): hysteresis 0,1 gần như không giảm dao động
- **Gate P6 không đạt trên lưới mặc định:** N(π_θ) = 3.844,6 (θ = 0); 3.877,0 (0,1); 3.883–3.893 (0,2–1,25); 3.899,3 (1,5, lớn nhất); 3.893,8 (2,0); SE 16–23. Ghép cặp theo seed: θ = 1,5 hơn θ = 0 là +54,7 ± 7,9, hơn θ = 2 chỉ +5,5 ± 4,1 → tăng một bậc rồi phẳng, không có cực đại bên trong lưới; chi/B = 1,00 ở mọi θ. Bậc tăng trùng với việc tắt 24,8% (ô, slot) không có xe rảnh. Chẩn đoán: lưới tới 30 → giảm từ θ = 10 (3.828) và θ = 30 (3.694); `fraction` 0,6 → cực đại tại θ = 0,4 (4.283 so với 4.187 ở θ = 2); `fraction` 0,1 và voucher 30% → phẳng; `demand_scale` 1,5 → tăng đều tới mép lưới (+242 ± 31)
- Lệch spec / quyết định mới: T-30; câu hỏi mở **Q23** (3 phương án, đề xuất giữ B và kéo dài `sweep.theta_grid`). Không nới tiêu chí, không tự chọn θ\*
- Bàn giao: không
- Còn lại / bước tiếp: dừng, chờ mentor trả lời Q23 (theo `phan_cong.md` §7); Hoàng xem đồ thị `runs/p6/sweep_theta/results/theta_sweep.png` (sinh lại bằng `python -m analysis.plots theta_sweep runs/p6/sweep_theta --gte runs/b7a/gte`)

### 2026-10-02 · T4.3 · sweep tham chiếu, B7b · dở (chờ Gate P6)
- Nhánh/PR: `develop1`, chưa commit
- Đã làm: ghi sweep `runs/p6/sweep_theta` vào `docs/datasets.md` như **bản tạm** của B7b (bảng 12 θ, κ, lệnh sinh lại) cùng bảng 5 sweep chẩn đoán
- Test: `python -m analysis.check_dataset runs/p6/sweep_theta` → OK (thư mục chỉ có results + meta)
- Lệch spec / quyết định mới: không
- Bàn giao: chưa giao B7b
- Còn lại / bước tiếp: sau khi mentor chốt Q23: nếu B giữ nguyên thì sweep này (hoặc bản lưới kéo dài) là sweep tham chiếu và `legacy_28d` giữ nguyên; nếu B đổi thì chạy lại `calibrate_budget`, sinh lại `legacy_28d` và sweep; gắn tag commit + `config_hash`, điền cột B7(b)

### 2026-10-02 · T4.2 · đính chính: Gate P6 trên lưới θ tham chiếu · xong · gate P6 đạt (quyết định T-31 của Tình, chờ mentor xác nhận)
- Nhánh/PR: `develop1` (fast-forward lên `c62800e`), chưa commit (Tình commit); PR S4
- Đã làm: chốt Q23 bằng T-31 (giữ B, lưới θ kéo dài, θ\* là tập, regret theo N); mục "gate P6 không đạt" ở trên chỉ đúng cho lưới mặc định 0–2. Thêm `config/sweep_reference.yaml` (16 mốc θ tới 30, không sửa `default.yaml`); `analysis/metrics.py`: `t_quantile`, `theta_star_set` (so sánh bội với cái tốt nhất, Bonferroni, phân vị t), `theta_star_interval`, `theta_star_gaps`, `sweep_regret`; `analysis/plots.py`: tô khoảng θ\*, trục đặt mốc cách đều khi lưới trải rộng; `tests/test_analysis.py` +4
- Test: `pytest -q` → 460 passed, 6 deselected (py3.11, 93 s); test chậm không chạy lại (`sim/` không đổi kể từ lần 3 passed)
- Số liệu (sweep tham chiếu 16 θ × 30 seed, B = 5.545,80, 480 lượt, 702 s): N = 3.848,4 (θ = 0); 3.889,8 (0,4); 3.894,3 (1,0); **3.901,7 (1,5, lớn nhất)**; 3.897,4 (2); 3.889,5 (3); 3.883,2 (5); 3.837,2 (10); 3.693,0 (30). Tập θ\* (95% đồng thời) = {0,4; 0,5; 0,6; 0,8; 1,0; 1,5; 2,0}, bao [0,4; 2], loại 1,25 (Q24). Regret: θ = 0: +53,3 ± 4,8 (1,37%); θ = 0,35: +14,4 ± 4,1 (0,37%); θ = 30: +208,6 ± 4,3 (5,35%). Với 10 seed tập là [0,1; 5]. 120 lượt chung với sweep cũ cho N, V giống hệt
- Lệch spec / quyết định mới: T-31 (sweep tham chiếu 16 θ × 30 seed thay cho 12 θ × 10 seed của plan P6); câu hỏi mở Q24 (nhiễu κ auto theo θ). **Mentor chưa xác nhận T-31**; quyết định không đổi B nên không thuộc phần `phan_cong.md` §7 giao cho mentor, nhưng kết luận gate cần mentor xem
- Bàn giao: không
- Còn lại / bước tiếp: báo mentor và Hoàng T-31, Q24 kèm `runs/b7b/sweep_theta_ref/results/theta_sweep.png`

### 2026-10-02 · T4.3 · sweep tham chiếu + độ nhạy, B7b · xong (chưa commit, chưa gắn tag)
- Nhánh/PR: `develop1`, chưa commit; PR S4
- Đã làm: `runs/b7b/sweep_theta_ref` (16 θ × 30 seed) và 4 sweep độ nhạy 16 θ × 10 seed: `sens_fraction_0p1`, `sens_fraction_0p6`, `sens_voucher_0p3`, `sens_demand_1p5`; `docs/datasets.md` mục B7b bản chính thức (bảng theo θ, tập θ\*, regret, lệnh sinh lại, cách dùng). B không đổi (5.545,80) nên **không sinh lại `legacy_28d`**
- Test: `python -m analysis.check_dataset` trên 5 thư mục `runs/b7b/*` → OK
- Số liệu độ nhạy (θ tốt nhất; khoảng θ\*; regret của θ = 0): `fraction` 0,1: 0,6; [0; 10]; +18,0 ± 5,5 (0,50%). `fraction` 0,6: 0,4; [0,2; 1]; +64,2 ± 8,2 (1,49%). Voucher 30%: 1,5; [0,3; 5]; +70,3 ± 5,5 (1,75%). `demand_scale` 1,5: 2; [0,4; 2]; +230,9 ± 16,3 (4,10%). θ = 0,4 và 0,6 thuộc tập θ\* ở cả năm kịch bản
- Lệch spec / quyết định mới: T-31
- Bàn giao: giao B7b; người nhận kiểm tra: sinh lại theo lệnh trong `docs/datasets.md` (cần `pip install -e ".[analysis]"` để vẽ), `check_dataset` báo OK, N theo θ khớp bảng
- Còn lại / bước tiếp: Tình commit rồi gắn tag dữ liệu (ví dụ `data-b7-cb27f5348011`); `runs/p6/` là bản chẩn đoán cũ, xóa được

### 2026-10-02 · rà soát · tính hợp lý của kết quả simulator · xong (chờ quyết định Q26–Q28)
- Nhánh/PR: `develop1` (`723a994`, sau PR #12 và #13); chỉ thêm vào `docs/log.md` và `docs/decisions.md`, chưa commit (Tình commit)
- Đã làm: 6 script chẩn đoán **ngoài repo** ở `runs/audit/scripts`, kết quả ở `runs/audit/out` (không commit); không đổi code, config, dữ liệu. Điểm oracle trong script đọc tham số ẩn, chỉ để chẩn đoán, không phải chính sách của dự án
- Test: `pytest -q` → 477 passed, 8 deselected (py3.11, 114 s); test chậm không chạy
- Đạt (`config_hash = cb27f5348011`): thời gian xe theo trạng thái cộng đủ (rảnh 42,2%; đi đón 13,1%; chở 28,4%; điều chuyển 16,4%); ETA báo 3,64 so với ETA lúc ghép 3,81 phút; tỷ lệ hủy tăng đều theo ETA đón (0,7% dưới 3 phút → 61,1% từ 12 phút); điểm tốt hơn cho N cao hơn (so với `random`, θ = 0, 10 seed: oracle +259,4 ± 10,3; `heuristic_low_freq` +48,8 ± 8,4; oracle đảo −172,7 ± 5,9); độ chệch thiết kế đúng thứ tự (rider A/B +1.647; cụm 1: +1.633; cụm 7: +1.513; toàn hệ +1.313; GTE +1.212,9); `legacy_28d` không trôi (−0,71 chuyến/ngày trên 3.871,8). Độ nhạy điều chuyển xe, `stay` so với `static_weights` (5 seed): N `all_off` 3.413,8 so với 3.437,0; GTE +1.193,8 ± 22,3 so với +1.198,8 ± 27,1; slack trung bình 4,78 so với 3,38. 0,70% chuyến hoàn thành bắt đầu khi chuyến trước của cùng rider chưa xong
- Cần quyết: κ auto một lượt pilot chi 1,113 × B khi không chặn, ngân sách cạn từ khoảng 22h (**Q26**). Bậc thang dưới cùng B: `all_on` có ngân sách 3.682,5 → điểm `random` +113,3 ± 3,3 → `heuristic_low_freq` +48,8 ± 8,4 → tầng ô θ = 0,5: +36,6 ± 4,7; lợi ích tầng ô là dồn ngân sách và mất khi hàm điểm đủ tốt; slack theo ô dự báo mức phục vụ kém hơn slack cụm và toàn hệ (**Q27**). Hai dải CAL về tỷ lệ căng/dư và giá mỗi phút không có nguồn dữ liệu (**Q28**, nối Q25)
- Lệch spec / quyết định mới: không quyết định gì; ba câu hỏi mở Q26, Q27, Q28
- Bàn giao: không
- Còn lại / bước tiếp: Tình, Hoàng và mentor xem Q26–Q28 trước S5; nếu đồng ý Q26 thì sửa `runner.kappa_auto`, thêm test, chạy lại sweep B7b

---

## 2. Hoàng

**Đang làm:** S4 xong và đã gộp vào `develop` (PR #13); đã kéo `develop` (`a5ccc50`, PR #14) về `develop2`. Q24, Q26–Q28 đã chốt (H-21…H-23); Gate P6 chờ mentor xác nhận T-31. S5: H5.1 xong (giao B8). Tiếp theo: H5.2 DR-learner; H5.3 sau khi chốt ŝ (H-22) và chạy lại B7b (H-21).

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

### 2026-10-01 · T1.1 · budget.py đầy đủ · nhận B2
- Nhánh/PR: commit của Tình trên `develop1`, đã có trong `develop` (`db9efd1`)
- Đã làm: chạy phần "Người nhận kiểm tra" của B2; đối chiếu API sổ với chỗ `choice.py` gọi (`commit`, `release_reserved`, `entry`, `totals`)
- Test: `pytest -q tests/test_pricing.py` → 23 passed (py3.12)
- Lệch spec / quyết định mới: không
- Bàn giao: nhận B2
- Còn lại / bước tiếp: `settle` và `release_committed` sẽ dùng ở H2.2 (`trips.py`, `cancel.py`)

### 2026-10-01 · H1.3 · choice.py (M4) · xong
- Nhánh/PR: `develop2 → develop`, review: Tình
- Đã làm: `sim/choice.py` (`request_probability`, `decide`: quyết định đặt xe, ghi `p_request_*` ẩn, tạo order Waiting, `commit`/`release_reserved` trên sổ, cộng `cells.waiting` và `n_requests`); `tests/test_choice.py` (+18). Phần `state.py` của H1.3 đã có từ hợp đồng B0. Sửa quy trình nhánh trong `CLAUDE.md`, `phan_cong.md`, `plan.md` (H-07)
- Test: `pytest -q` → 282 passed (py3.12); test chậm: không chạy. `decide` cho 1 ngày mô phỏng, mọi session có voucher: 0,28 giây
- Lệch spec / quyết định mới: H-06, H-07 trong `decisions.md`
- Bàn giao: không
- Số liệu tham khảo (chưa phải CAL; ETA báo cố định 4 phút, giá tự tính): tỷ lệ đặt không voucher 18,9% (mục tiêu P3: 13–17%), có voucher 26,1% (+38,0%), giá trung bình 21,27 USD
- Còn lại / bước tiếp: H1.4 `supply.py`

### 2026-10-01 · H1.4 · supply.py (M8), bảng tóm tắt thế giới · xong
- Nhánh/PR: `develop2 → develop` (một PR cho H1.3 và H1.4), review: Tình
- Đã làm: `sim/supply.py` (`init_drivers`: xe đang trong ca lúc t = 0 thì rảnh tại ô xuất phát; `update`: hết ca chỉ rời khi rảnh, vào ca tại ô xuất phát; `shift_mode = always_on`); `sim/population.py` thêm `on_shift`, `online_by_hour`, `describe_world`; `tests/test_supply.py` (+12, phần M8)
- Test: `pytest -q` → 294 passed (py3.12); test chậm: không chạy
- Lệch spec / quyết định mới: H-08 trong `decisions.md`; câu hỏi mở Q17 (`early_exit_enabled` chưa cài)
- Bàn giao: không
- Số liệu tham khảo (cấu hình mặc định): số xe trong ca theo giờ thấp nhất 6 xe lúc 06:00, 18 xe lúc 07:00, 31 xe lúc 08:00 (cầu cao điểm sáng 1,40–1,70), cao nhất 61 xe lúc 14:00 và 21:00; 43/120 xe trong ca lúc 00:00
- Còn lại / bước tiếp: S2: H2.1 `matching.py`, H2.2 `trips.py` + `cancel.py`, H2.3 `reposition.py`, H2.4 `engine.py`

### 2026-10-01 · S1 · gộp `develop` vào `develop2`, đính chính số câu hỏi mở · xong
- Nhánh/PR: merge `origin/develop` (`eb96ab9`, gồm T1.2, T1.3, T1.4 của Tình) vào `develop2`; PR `develop2 → develop`, review: Tình
- Đã làm: xử lý conflict ở `docs/decisions.md`: giữ đủ H-06, H-07, H-08 và T-21; mục "Câu hỏi mở" giữ Q17 của Tình (`evaluate` dùng `n_seeds` nào), câu về `supply.early_exit_enabled` đổi thành **Q18**; sửa thông báo lỗi trong `sim/supply.py` theo số mới. Tạo `.venv` (py3.12) và cài `pip install -e ".[dev]"`
- Test: `pytest -q` trong `.venv` → 321 passed (py3.12, numpy 2.5.3, pandas 3.0.6, pyarrow 25.0.1)
- Lệch spec / quyết định mới: không
- Bàn giao: không
- Đính chính: mục "H1.4" ở trên ghi "câu hỏi mở Q17"; số đúng là **Q18**
- Còn lại / bước tiếp: S2, H2.1 `matching.py`

### 2026-10-01 · T1.4 · mode throughput_curve trên engine giả · nhận B4
- Nhánh/PR: commit của Tình, đã có trong `develop` (`eb96ab9`) và `develop2`
- Đã làm: chạy phần "Người nhận kiểm tra" của B4
- Test: `pytest -q tests/test_runner.py` → 14 passed (py3.12, `.venv`)
- Lệch spec / quyết định mới: không
- Bàn giao: nhận B4
- Còn lại / bước tiếp: chạy `throughput_curve` trên engine thật ở Gate P2 (cuối S2)

### 2026-10-01 · H2.1 · matching.py (M5) · xong
- Nhánh/PR: commit trên `develop2`; PR `develop2 → develop` cuối S2, review: Tình
- Đã làm: `sim/matching.py` (`match`: FIFO theo thứ tự order, tìm xe bằng `SpaceTime.find_pickup`, hàng đợi xe theo `idle_since`, ghi cột bước "match", chốt `trip_time_min` lúc ghép, cập nhật `cells` và bộ đếm slot qua `MarketMonitor.on_matched`); `tests/test_matching.py` (+16)
- Test: `pytest -q` → 337 passed (py3.12, `.venv`); test chậm: không chạy. Một lần gọi `match`: 300 order chờ, 60 xe rảnh → 0,64 ms; 300 order chờ, không xe → 0,03 ms
- Lệch spec / quyết định mới: H-09 trong `decisions.md`
- Bàn giao: không
- Còn lại / bước tiếp: H2.2 `trips.py`, `cancel.py`

### 2026-10-01 · H2.2 · trips.py (M6), cancel.py (M7) · xong
- Nhánh/PR: commit trên `develop2`; PR `develop2 → develop` cuối S2, review: Tình
- Đã làm: `sim/trips.py` (`advance`: đón, trả, thanh toán, `ledger.settle`, xe repositioning tới nơi); `sim/cancel.py` (`expire_waiting`: bỏ chờ quá `max_wait`; `en_route`: hủy theo hazard tích lũy so với `e_cancel`, xe rảnh tại ô xuất phát hoặc ô khách; `cancel_hazard_per_min`); `tests/test_trips_cancel.py` (+16)
- Test: `pytest -q` → 353 passed (py3.12, `.venv`); test chậm: không chạy
- Lệch spec / quyết định mới: H-10 trong `decisions.md`
- Bàn giao: không
- Số liệu tham khảo (chưa phải CAL hay gate; 1 ngày + 3 giờ cool-down, cấu hình mặc định, không voucher, không repositioning, giá và ETA báo tự điền bằng `base_fare_usd` và `space.quote_eta` thay cho `pricing.quote`): 30.397 session, 3.956 request (13,0%); 2.659 hoàn thành (67,2%), 255 bỏ chờ, 1.042 hủy khi xe đang đến (26,3%); ETA đón trung bình 9,6 phút; slack trung bình 0,40; 6,3% session được báo `no_supply`; tỷ lệ hoàn thành theo giờ đặt: 03h 91%, 07h 33%, 08h 37%, 12h 70%, 18h 51%, 21h 78%. Thời gian chạy 2,1 giây (spawn 1,39; quote 0,30; match 0,13; decide 0,11; advance 0,05; en_route 0,04)
- Còn lại / bước tiếp: H2.3 `reposition.py`

### 2026-10-01 · H2.3 · reposition.py (M9) · xong
- Nhánh/PR: commit trên `develop2`; PR `develop2 → develop` cuối S2, review: Tình
- Đã làm: `sim/reposition.py` (`step`: xe rảnh đủ `max_idle_min` đi sang một ô kề rút theo `w_z`, luồng DRIVER khóa `(driver_id, reposition_count)`; `mode = stay` và `enabled = false` không làm gì); `tests/test_supply.py` phần M9 (+10, tổng 22)
- Test: `pytest -q` → 363 passed (py3.12, `.venv`); test chậm: không chạy
- Lệch spec / quyết định mới: H-11 trong `decisions.md`
- Bàn giao: không
- Số liệu tham khảo (cùng cách chạy tay như mục H2.2, 1 ngày + 3 giờ cool-down): `static_weights` 469 lượt điều xe, 0,05 giây; 3.923 request, 2.636 hoàn thành, 1.032 hủy, 255 bỏ chờ, ETA đón 9,53 phút, slack 0,32. `stay`: 3.956 request, 2.659 hoàn thành, 1.042 hủy, 255 bỏ chờ, ETA 9,58 phút, slack 0,40
- Còn lại / bước tiếp: H2.4 `engine.py` + 4 test tích hợp; cần B3 (`pricing.quote`) để engine chạy có session

### 2026-10-01 · H2.4 · engine chạy thật + 4 test tích hợp · xong (chờ B3 để tích hợp 1)
- Nhánh/PR: commit trên `develop2`; PR `develop2 → develop` cuối S2, review: Tình
- Đã làm: `tests/test_integration.py` (+14): `test_smoke_day`, `test_conservation`, `test_cooldown`, `test_driver_state_consistency` cho `all_off` và `all_on`, cộng test Truncated, thứ tự thời gian của order, cùng seed cùng kết quả, hai chính sách gặp cùng session. `engine.py` không phải sửa: vòng lặp 10 bước, warm-up, cool-down, Truncated của hợp đồng B0 chạy đúng với 7 bước thật của Hoàng
- Test: `pytest -q` → 377 passed (py3.12, `.venv`, 36 giây); test chậm: không chạy
- Lệch spec / quyết định mới: H-12 trong `decisions.md`. Bước 5 (`pricing.quote`, T2.1) chưa có, nên file test thay nó bằng `quote_stand_in` (giá gốc, ETA theo `space.quote_eta`, `all_on` cấp voucher cho mọi session); gỡ khi nhận B3
- Bàn giao: giao B5 (`engine.run` thật); người nhận kiểm tra: 4 test tích hợp pass, `RunResult` đủ trường
- Số liệu tham khảo, `engine.run` với bước báo giá tạm, 1 seed (chưa phải gate):
  - 1 ngày `default.yaml`: `all_off` N = 2.642, 3.917 request, 255 bỏ chờ, 1.020 hủy, ETA đón 9,52 phút, slack 0,19, V = 10.448 USD, 2,34 giây. `all_on` không ngân sách: N = 2.489, 5.156 request, 1.407 bỏ chờ, 1.260 hủy, ETA 10,91 phút, slack 0,08, V = 1.715 USD, voucher 8.559 USD, 2,39 giây
  - Xem trước đường throughput (thiết lập T-08: `always_on`, giờ 18 cố định, `all_off`): `completed_per_h` theo `demand_scale` 0,25 → 100,6; 0,5 → 191,5; 0,75 → 270,1; 1,0 → 329,7; **1,25 → 335,5 (đỉnh)**; 1,5 → 296,1; 1,75 → 283,4; 2,0 → 283,4; 3,0 → 286,9; 4,0 → 282,1 (= 0,841 × đỉnh). Slack 0,68 ở 1,0; 0,19 ở 1,25; 0,04–0,05 từ 1,5 trở lên. ETA đón 3,1 phút ở 0,25 lên 11,7 phút ở 4,0
  - Thời gian: `spawn` chiếm khoảng 65–70% (1,5 giây trong 2,3 giây ở mức mặc định; 5,8–10,3 giây ở `demand_scale` 1,75–2,0 với 105.019–120.269 session)
- Còn lại / bước tiếp: nhận B3, gỡ `quote_stand_in`, Tích hợp 1 và Gate P2 cùng Tình

### 2026-10-01 · T2.1 · pricing.quote, lớp voucher, monitor · nhận B3
- Nhánh/PR: commit của Tình trong `develop` (`9fec911`, PR #6), đã gộp vào `develop2`
- Đã làm: chạy phần "Người nhận kiểm tra" của B3. So `engine.run` 1 ngày `default.yaml` giữa `pricing.quote` thật và bản tạm `quote_stand_in`: `all_off` N = 2.642, V = 10448,4375 ở cả hai; `all_on` N = 2.489, V = 1715,087646484375 ở cả hai; các cột `status`, `driver_id`, `pickup_time_s`, `dropoff_time_s`, `voucher_cents` của mọi order giống hệt
- Test: `pytest -q tests/test_pricing.py tests/test_monitor.py` → pass (nằm trong 414 passed của cả bộ)
- Lệch spec / quyết định mới: không
- Bàn giao: nhận B3
- Còn lại / bước tiếp: không

### 2026-10-01 · S2 · gộp `develop` vào `develop2`, Tích hợp 1 · xong
- Nhánh/PR: merge `origin/develop` (`9fec911`: T2.1–T2.4 của Tình) vào `develop2`; PR `develop2 → develop` (H2.1–H2.4 + lần gộp này), review: Tình
- Đã làm: xử lý conflict ở `docs/decisions.md` (giữ đủ H-09…H-12 và T-22…T-25). Gỡ `quote_stand_in` và fixture `patched_quote` khỏi `tests/test_integration.py`: 14 test tích hợp chạy trên `pricing.quote` thật. Sửa 2 test của Tình viết khi lõi còn là stub (kỳ vọng N = 0, mọi order bị Truncated): `tests/test_pricing.py::test_engine_runs_with_real_demand_through_the_voucher_layer` và `tests/test_cli.py::test_gte_and_sweep_with_real_demand`; giữ các kiểm tra về voucher, CRN, tính tất định, thay kỳ vọng "không ghép được" bằng "có order hoàn thành, không order nào bị Truncated". `tests/test_engine.py` vẫn chạy với `demand_scale = 0` vì các test đó kiểm vòng lặp trên thị trường rỗng; sửa lại chú thích
- Test: `pytest -q` → 414 passed (py3.12, `.venv`, 46 giây); test chậm: không chạy
- Lệch spec / quyết định mới: H-13 trong `decisions.md`
- Bàn giao: B5 đã giao đủ (bước 5 dùng `pricing.quote` thật)
- Còn lại / bước tiếp: Gate P2

### 2026-10-01 · Gate P2 · đường throughput trên simulator thật · dở (chờ Tình và Hoàng cùng xem)
- Nhánh/PR: chạy trên `develop2` sau Tích hợp 1 (chưa commit lúc chạy); kết quả ở `runs/p2_throughput/results/throughput_curve.parquet` (không commit)
- Đã làm: `python -m sim run --mode throughput_curve --config config/default.yaml --out runs/p2_throughput` (`config_hash = 126e0c67a0ad`; 16 mức `demand_scale` × 3 seed = 48 lượt; `all_off`, `always_on`, giờ 18 cố định; tham số `[assume]` chưa hiệu chỉnh)
- Test: lệnh chạy hết 60 giây, không lỗi
- Số liệu (trung bình 3 seed, `completed_per_h`): 0,25 → 97,0; 0,5 → 188,5; 0,75 → 267,4; 1,0 → 326,4; **1,25 → 341,4 (đỉnh, cả 3 seed)**; 1,5 → 299,1; 1,75 → 284,5; 2,0 → 284,8; 3,0 → 287,3; 4,0 → 283,2. Tỷ lệ mức cao nhất / đỉnh: 0,830 (từng seed: 0,841; 0,824; 0,825). `mean_slack`: 0,738 ở 1,0; 0,226 ở 1,25; 0,057 ở 1,5; 0,042–0,043 từ 1,75 trở lên. ETA đón: 3,1 phút ở 0,25; 7,2 ở 1,25; 11,7 ở 4,0. Tỷ lệ hủy khi xe đang đến cao nhất 31,8% ở 1,75; tỷ lệ bỏ chờ 61,5% ở 4,0
- Đối chiếu 4 tiêu chí A1 của `tests.md` (cấu hình chưa hiệu chỉnh): (1) có đỉnh: đạt; (2) mức cao nhất ≤ 0,95 × đỉnh: đạt (0,830); (3) slack < 0,45 ở vùng giảm: đạt (lớn nhất 0,057); (4) ETA tăng đơn điệu, không bước nhảy > 3 phút: **chưa đạt**: bước nhảy lớn nhất 3.44 phút giữa `demand_scale` 1,25 và 1,5; và ở vùng bão hòa (từ 1,75) ETA đi ngang quanh 11,5–11,7 phút, có 3 bước giảm nhỏ (nhiều nhất 0.025 phút)
- Lệch spec / quyết định mới: không
- Bàn giao: không
- Còn lại / bước tiếp: Tình và Hoàng cùng xem bảng này (và đồ thị, khi có `matplotlib` theo T-13) rồi ghi "gate P2 đạt" hoặc "không đạt"; sau đó S3: H3.1 (A5), H3.2 (CAL + A1)

### 2026-10-01 · H3.1 · A5 với all_on · xong
- Nhánh/PR: commit trên `develop2`; PR cuối S3, review: Tình
- Đã làm: `tests/test_acceptance_core.py` (đánh dấu `slow`): `test_a5_one_simulated_day_within_the_time_limit` và hàm đo `measure_runtime`; kèm sẵn hàm đo và test của CAL (`calibration_metrics`) và A1 (`throughput_summary`, `a1_checks`) cho H3.2
- Test: `pytest -q` → 414 passed (py3.12, `.venv`). A5: 1 job `evaluate`, `policy.name = all_on`, có ngân sách B = 2.609,96 USD (pilot), 1 tiến trình, 3 lần: 6,73; 6,69; 6,91 giây, trung vị **6,73 giây** ≤ 30 giây. Profile lần 3: spawn 4,66; quote 1,17; match 0,35; decide 0,29; advance 0,16; en_route 0,10; monitor 0,05; expire 0,04; reposition 0,04; supply 0,03
- Lệch spec / quyết định mới: không. Không tối ưu gì, nên cách rút số ngẫu nhiên giữ nguyên
- Bàn giao: không
- Còn lại / bước tiếp: H3.2; H4.1 đo lại A5 với chính sách mặc định

### 2026-10-01 · H3.2 · CAL + A1 · dở (chờ chốt Q20, Q21, Q22)
- Nhánh/PR: `develop2`, chưa đổi `default.yaml`
- Đã làm: đo CAL ban đầu (5 seed, `all_off` và `all_on` không ngân sách, theo cách đọc sát chữ `tests.md` §4); phân tích vì sao P(đặt) ở ô "dư cung" thấp bất thường; ghi 3 câu hỏi mở
- Test: không đổi code `sim/`
- Số liệu CAL ban đầu (`config_hash = 126e0c67a0ad`): P(đặt) không voucher ở slot slack > 1 = 4,78% (mục tiêu 13–17%); tăng request = +104,7% (35–70%); giá gốc trung bình đơn hoàn thành = 16,47 USD (17,2–21,0); tỷ lệ (ô, slot) slack < 0,35 = 53,9% (10–35%); tỷ lệ slack > 1 = 40,2% (30–80%). 4/5 ngoài khoảng
- Chẩn đoán (1 seed, `all_off`): thị trường mặc định quá căng: 73,0% session ở ô có slack < 0,35; trung bình 0,10 xe rảnh mỗi (ô, slot); 40,9 xe online trung bình; slack toàn hệ theo slot có trung vị 0,07, chỉ 13,5% số slot > 1. Phân loại theo slot trước cùng ô: P(đặt) = 19,6% (slack hữu hạn > 1), 14,7% (0,35–1), 12,8% (< 0,35), 10,9% (I = 0, E = 0)
- Lệch spec / quyết định mới: Q20, Q21, Q22 trong `decisions.md` (câu hỏi mở)
- Bàn giao: không
- Còn lại / bước tiếp: chốt Q20–Q22; sau đó chỉnh theo thứ tự `tests.md` §4 (`alpha0`; `beta_price_per_usd`, `delta0`; `per_min_usd`; `fleet_size`, `demand_scale`), rồi A1 tiêu chí 4 (bước nhảy ETA 3,44 phút)

### 2026-10-01 · H3.2 · CAL + A1, hiệu chỉnh `default.yaml` · xong (chờ Gate P3)
- Nhánh/PR: `develop2`; PR `develop2 → develop` cuối S3, review: Tình
- Đã làm: chốt Q20, Q21, Q22 (H-15, H-14, H-16). Sửa `sim/monitor.py`: I = 0 thì slack = 0. Viết lại `calibration_metrics` theo `slack_lag_slot` và cột ẩn `p_request_*`; sửa `tests.md` §4, spec §4.11, `schema.md`. Hiệu chỉnh 5 tham số trong `config/default.yaml` (H-17). Sửa 4 test ghi cứng giá trị cũ (H-18)
- Test: `pytest -q` → 414 passed (py3.12, `.venv`, 44 giây). `pytest -q -m slow tests/test_acceptance_core.py` → 3 passed (A1, A5, CAL; 96 giây)
- Tham số: `fleet_size` 120 → 240; `demand_scale` 1,0 → 0,85; `alpha0` 0,475 → 0,35; `delta0` 0,15 → 0,25; `per_min_usd` 1,4 → 1,70. `config_hash = cb27f5348011`
- CAL (5 seed, `all_off`), trước → sau (cùng cách đo H-14…H-16): P(đặt) ở ô dư cung 17,21% → **15,35%** [13–17]; tăng request +36,4% → **+50,6%** [35–70]; giá trung bình 16,47 → **19,03 USD** [17,2–21,0]; (ô, slot) slack < 0,35: 80,5% → **27,9%** [10–35]; slack > 1: 13,5% → **63,3%** [30–80]. Kiểm thêm: `run_seed` 100 và 200, `world_seed` 7 đều trong khoảng
- A1 (3 seed, `completed_per_h` theo `demand_scale`): 0,25 → 80,3; 1,0 → 317,7; 2,0 → 598,9; 3,0 → 780,2; **3,25 → 781,2 (đỉnh)**; 3,5 → 735,1; 3,75 → 671,6; 4,0 → 659,8 (= 0,845 × đỉnh). Slack ở vùng giảm ≤ 0,095. ETA đón 2,06 → 9,85 phút, bước nhỏ nhất +0,012, lớn nhất +1,871 phút. Đạt cả 4 tiêu chí
- A5 (`all_on`, B = 5.545,80 USD/kỳ): 6,14; 7,07; 7,01 giây; trung vị 7,01 giây
- 1 ngày, seed 0: `all_off` 25.859 session, 3.716 request, N = 3.506, 2 bỏ chờ, 208 hủy, ETA 3,84 phút, slack 3,23, V = 16.015 USD. `all_on` không ngân sách: 5.226 request, N = 4.722, 53 bỏ chờ, 451 hủy, ETA 5,01, slack 1,34, V = 3.785, voucher 18.892 USD. `all_on` có ngân sách B: 4.176 request, N = 3.759, V = 11.774, voucher 5.544 USD
- Theo giờ (5 seed, `all_on` không ngân sách trừ `all_off`): N tăng ở 22/24 giờ (tổng +1.199 chuyến/ngày); **giảm ở 07h (−15,4) và 08h (−6,4)**, khi chỉ có 31 và 57 xe trong ca và tỷ lệ hoàn thành của `all_on` còn 53% và 67%
- Lệch spec / quyết định mới: H-14…H-18
- Bàn giao: giao B6 (`default.yaml` đã hiệu chỉnh); người nhận kiểm tra: A1, A5, CAL đạt (`pytest -q -m slow tests/test_acceptance_core.py`), bảng hiệu chỉnh ở H-17, `config_hash` mới
- Ghi chú rủi ro cho Gate P6: sau hiệu chỉnh, voucher chỉ làm giảm số chuyến ở 2 giờ cao điểm sáng. Biên độ θ có thể cải thiện N(π_θ) vì vậy nhỏ khi không có ngân sách; cần xem đường N(π_θ) dưới ngân sách B
- Còn lại / bước tiếp: Tình review và chạy lại `calibrate_budget` (B đổi từ 2.609,96 lên 5.545,80 USD/kỳ); S4: H4.1

### 2026-10-01 · S3 · gộp `develop` vào `develop2` · xong
- Nhánh/PR: merge `origin/develop` (`87fbdab`, PR #8: T3.1, T3.2, T3.3 của Tình) vào `develop2`; PR `develop2 → develop` (H3.1, H3.2 + lần gộp này), review: Tình
- Đã làm: xử lý conflict ở `docs/decisions.md` (giữ đủ H-13…H-18 và T-26, T-27). Không phải sửa code hay test nào: phần S3 của Tình (`logger.py`, `analysis/`, `tests/test_acceptance.py`, `tests/test_logger.py`, `tests/test_analysis.py`) chạy đúng trên `default.yaml` đã hiệu chỉnh và định nghĩa slack mới (H-14)
- Test: `pytest -q` → 452 passed (py3.12, `.venv`, 89 giây); `pytest -q -m slow` → 3 passed (A1, A5, CAL; 97 giây)
- Lệch spec / quyết định mới: không
- Bàn giao: không
- Còn lại / bước tiếp: Tình review PR, xác nhận H-14 (đổi `monitor.py`) và chạy lại `calibrate_budget` với `config_hash = cb27f5348011`; hai người ghi kết quả Gate P3

### 2026-10-02 · H4.1 · A5 với chính sách mặc định (threshold, κ auto) · xong
- Nhánh/PR: commit trên `develop2`; PR `develop2 → develop` cuối S4, review: Tình
- Đã làm: `tests/test_acceptance_core.py`: thêm `evaluate_job` (dựng đúng job của `runner.evaluate`: B từ pilot, κ auto) và chạy `test_a5_one_simulated_day_within_the_time_limit` cho cả `all_on` và `threshold`
- Test: `pytest -q -m slow tests/test_acceptance_core.py` → 4 passed (py3.12, `.venv`). A5, `config_hash = cb27f5348011`, 1 tiến trình, 3 lần: `threshold` (θ = 0,35, `heuristic_low_freq`, κ auto = −2,748, B = 5.545,80 USD/kỳ): 6,61; 6,47; 6,53 giây, trung vị **6,53 giây** ≤ 30. `all_on` có ngân sách: 3,11; 2,53; 2,69 giây, trung vị 2,69 giây. Hai pilot (B và κ) mất 13,0 giây, không tính vào A5
- Lệch spec / quyết định mới: không
- Bàn giao: không
- Số liệu tham khảo (1 seed, cùng B): `threshold` N = 3.980, 4.214 request, V = 12.977 USD, voucher 5.545 USD, 31,3% (ô, slot) tắt, 25,97 lần đổi trạng thái mỗi ô mỗi ngày; `all_on` N = 3.759, 4.176 request, V = 11.774 USD, voucher 5.544 USD; `all_off` N = 3.506
- Còn lại / bước tiếp: H4.2 (cần B7a)

### 2026-10-02 · T4.1 · bộ dữ liệu B7a · nhận B7a
- Nhánh/PR: `develop` (`364136b`, PR #10) đã gộp vào `develop2`, không conflict
- Đã làm: sinh lại 7 thư mục `runs/b7a/` bằng đúng lệnh trong `docs/datasets.md` (5 bộ `generate` chạy song song, mỗi bộ 198–200 giây); chạy `analysis.check_dataset` và `analysis.check_budget`
- Test: `check_dataset` 7/7 OK. Khớp bảng của Tình ở mọi bộ: 718.749 session; order 115.232 / 124.374 / 123.841 / 124.043 / 124.557; N hoàn thành 108.410 / 114.932 / 114.040 / 113.990 / 115.116; `config_hash` trong metadata trùng; GTE = +1.212,9 (SE 14,2); B = 5.545,80 USD. `check_budget`: mọi kỳ trong ngân sách
- Lệch spec / quyết định mới: không
- Bàn giao: nhận B7a
- Ghi chú cho Tình: `python -m analysis.check_dataset` báo `UnicodeEncodeError` trên console Windows mặc định (cp1252) khi in tiếng Việt; phải đặt `PYTHONIOENCODING=utf-8`
- Còn lại / bước tiếp: H4.2

### 2026-10-02 · H4.2 · ước lượng trên B7a: hiệu ứng theo slack, A4, θ̂, τ̂(x) nền · xong
- Nhánh/PR: commit trên `develop2`; PR `develop2 → develop` cuối S4, review: Tình
- Đã làm: `analysis/estimate.py` (`experiment_frame`, `effect_by_bin` với bootstrap theo đơn vị (cụm, block), `sign_changes`, `theta_hat`, `naive_total_effect`); `analysis/scores.py` (`fit_tau_strata` trên lát explore của legacy, hai hàm điểm `tau_x_baseline` và `tau_per_dollar_baseline`) và bảng `analysis/models/tau_x_baseline.json`; `tests/test_estimate.py` (+17 nhanh, +1 chậm cho A4)
- Test: `pytest -q` → 472 passed, 1 skipped (py3.12, `.venv`, 109 giây); `pytest -q -m slow tests/test_estimate.py` → 1 passed
- A4 (`switchback_c7_28d`, tứ phân vị của `slack_lag_slot`, bỏ burn-in): hiệu ứng lên tỷ lệ hoàn thành mỗi session +0,0500; +0,0645; +0,0751; +0,0813, **0 lần đổi dấu**. Tỷ lệ session ở nhánh bật trong 4 nhóm: 57,1%; 58,2%; 47,6%; 35,9% (thiết kế là 50%): `slack_lag_slot` đã bị chính nhánh của block tác động. Với slack ngay trước block (`cell_pre`): +0,0440; +0,0533; +0,0678; +0,0643, tỷ lệ bật 48,4–51,0%, 0 lần đổi dấu
- Hiệu ứng theo slack toàn hệ trước block (`switchback_all_28d`): +0,0042 [−0,0134; +0,0196] ở slack < 0,05; +0,0334 [0,0153; 0,0506] ở 0,6–1; +0,0680 [0,0525; 0,0825] ở slack ≥ 5; 0 lần đổi dấu
- θ̂ (điểm hiệu ứng cắt 0, không ngân sách): 0,0, khoảng tin cậy [0; 0,289] với slack toàn hệ trên switchback toàn hệ (58,8% mẫu bootstrap cho 0); 0,0 [0; 0] với slack theo ô ở cả ba thiết kế
- So thiết kế, hiệu ứng tổng quy ra chuyến/ngày (GTE thật +1.212,9): cụm 1: +1.633,2 [1.576,4; 1.691,3]; cụm 7: +1.513,0 [1.420,0; 1.601,7]; toàn hệ: +1.312,7 [1.101,7; 1.513,6]
- Confounding trong `legacy_28d`: hiệu ứng lên tỷ lệ hoàn thành, so thô có/không voucher = +0,1018; trên lát explore (35.993 session ngẫu nhiên hóa) = +0,0695 (SE 0,0039)
- Hàm điểm dưới cùng B = 5.545,80 USD, π_θ với θ = 0,35, κ auto, 5 seed, N trung bình: `tau_per_dollar_baseline` 3.896,0; `heuristic_low_freq` 3.882,8; `tau_x_baseline` 3.862,4; `random` 3.813,4
- Lệch spec / quyết định mới: H-19 trong `decisions.md`
- Bàn giao: hàm điểm cho B8 đã sẵn (`analysis.scores:tau_x_baseline`, `analysis.scores:tau_per_dollar_baseline`); giao chính thức ở H5.1 kèm parquet dự đoán
- Còn lại / bước tiếp: H4.3; ở S5 hai người chốt định nghĩa ŝ và chỉ số căng cung dùng chung cho θ̂ và θ\*

### 2026-10-02 · thăm dò · cung cầu theo giờ so với NYC TLC · xong (chờ quyết định Q24)
- Nhánh/PR: `develop2`; đi cùng PR cuối S4
- Đã làm: `analysis/tlc_hourly.py` (đọc `runs/tlc/fhvhv_tripdata_2024-03.parquet`, 508 MB, không commit; so đường cầu, thời gian chờ, số xe bận theo giờ với 5 ngày `all_off` của simulator). Không đổi tham số nào
- Test: không thêm test (script phụ thuộc file dữ liệu ngoài); `python -m analysis.tlc_hourly` chạy hết, ghi `runs/tlc/hourly_comparison.csv`
- Số liệu: xem Q24 trong `decisions.md`. Tóm tắt: chờ trung bình 3,54 phút (TLC) so với 3,52 (sim); cầu theo giờ tương quan 0,85 (0,92 với ngày thường); chờ theo giờ thực tế 2,76–4,85 phút, simulator 2,11–8,28 phút; cung lúc 7h bằng 70% đỉnh (TLC) so với 25% (sim)
- Lệch spec / quyết định mới: câu hỏi mở Q24
- Bàn giao: không
- Còn lại / bước tiếp: Hoàng, Tình và mentor chốt Q24 trước S5

### 2026-10-02 · quyết định · chốt Q24 · xong
- Nhánh/PR: `develop2`; đi cùng PR cuối S4
- Đã làm: chốt Q24 theo phương án giữ nguyên (H-20): không đổi `hour_profile`, lịch ca, `default.yaml`, hay bộ B7a
- Test: không đổi code
- Lệch spec / quyết định mới: H-20
- Bàn giao: không
- Còn lại / bước tiếp: ghi hạn chế này vào báo cáo (S6); H4.3 chờ T4.2, T4.3 của Tình

### 2026-10-02 · H4.3 · review P6 và P8 · xong
- Nhánh/PR: đọc `origin/develop` (`c62800e`, PR #11: T4.2, T4.3 của Tình); chưa gộp vào `develop2` vì lần merge trước (`364136b`) chưa commit
- Đã làm: (P8) nhận B7a, xem mục riêng. (P6) chạy lại sweep tham chiếu `python -m sim run --mode sweep_theta --config config/default.yaml --out runs/p6/sweep_theta` và đối chiếu với bảng trong `docs/datasets.md`; chạy 3 test `slow` của T4.2; đọc Q23 của Tình, 5 sweep chẩn đoán, thay đổi `pyproject.toml` (T-30). Đổi câu hỏi mở của Hoàng về TLC từ Q23 thành **Q24** vì trùng số với Q23 của Tình
- Test: `pytest -q -m slow tests/test_acceptance.py` → 3 passed (92 giây): κ auto, A2(b), A3. Sweep tái lập: N trung bình của cả 12 θ trùng bảng của Tình đến 0,1 chuyến (3.844,6 ở θ = 0 … 3.899,3 ở θ = 1,5 … 3.893,8 ở θ = 2); hiệu ghép cặp θ = 1,5 trừ θ = 0: +54,7 ± 7,9; trừ θ = 0,1: +22,3 ± 7,5; trừ θ = 2: +5,5 ± 4,1; κ từng θ trùng (−2,349 … −3,404); `config_hash = cb27f5348011`, B = 5.545,80
- Ý kiến review: đồng ý kết luận "Gate P6 không đạt trên lưới mặc định" và cách đọc của Tình (ngân sách tiêu hết ở mọi θ; bậc tăng duy nhất đến từ việc tắt 24,8% (ô, slot) không có xe rảnh). Khớp với H4.2: hiệu ứng voucher dương và giảm đều theo độ căng, θ̂ không ngân sách = 0 [0; 0,289]. Với Q23 của Tình: ủng hộ phương án (A), và đề nghị đưa bảng chẩn đoán (`fraction` 0,1 / 0,3 / 0,6; `demand_scale` 1,0 / 1,5) thành kết quả chính "θ\* phụ thuộc B và độ căng thị trường", thay vì chỉ báo một khoảng θ\*. Duyệt T-30 (`matplotlib` trong extra `[analysis]`)
- Lệch spec / quyết định mới: không
- Bàn giao: B7b chưa nhận (Tình chưa giao, chờ Gate P6)
- Còn lại / bước tiếp: mentor trả lời Q23; khi có B7b thì làm phần θ̂ so với θ\* của H5.3

### 2026-10-02 · S4 · gộp `develop` vào `develop2` · xong
- Nhánh/PR: merge `origin/develop` (`c62800e`, PR #11: T4.2, T4.3 của Tình) vào `develop2`; PR `develop2 → develop` (H4.1, H4.2, H4.3 + hai lần gộp), review: Tình
- Đã làm: gộp tự động, không conflict (chỉ `docs/datasets.md`, `docs/decisions.md`, `docs/log.md` đổi). Số câu hỏi mở không còn trùng: Q23 của Tình (Gate P6, còn mở), Q24 của Hoàng (TLC, đã chốt bằng H-20)
- Test: `pytest -q` → 472 passed, 1 skipped (py3.12, `.venv`, 117 giây)
- Lệch spec / quyết định mới: không
- Bàn giao: không
- Còn lại / bước tiếp: gửi mentor Q23; S5

### 2026-10-02 · T4.3 · sweep tham chiếu B7b · nhận B7b
- Nhánh/PR: `origin/develop` (`fb354b1`, PR #12: T4.2 đính chính, T4.3) đã gộp vào `develop2`; conflict ở `docs/decisions.md` (H-19, H-20 và T-31 cùng thêm vào cuối bảng), giữ cả ba dòng
- Đã làm: sinh lại sweep tham chiếu `python -m sim run --mode sweep_theta --config config/default.yaml --config config/sweep_reference.yaml --set sweep.n_seeds=30 --out runs/b7b/sweep_theta_ref` (16 θ × 30 seed = 480 lượt); chạy `analysis.check_dataset`; tính lại tập θ\* bằng `analysis.metrics.theta_star_set`. Chưa sinh lại 4 sweep độ nhạy `sens_*`
- Test: `pytest -q` → 476 passed, 1 skipped (py3.12, `.venv`, 111 giây). `check_dataset runs/b7b/sweep_theta_ref` → OK. N trung bình của cả 16 θ trùng bảng trong `docs/datasets.md` (lệch lớn nhất 0,0): 3.848,4 (θ = 0); 3.889,8 (0,4); 3.901,7 (1,5, lớn nhất); 3.837,2 (10); 3.693,0 (30). `config_hash = c27ac66f7c2c`, B = 5.545,80. Tập θ\* = {0,4; 0,5; 0,6; 0,8; 1,0; 1,5; 2,0}, khoảng [0,4; 2], mốc bị loại bên trong: 1,25: trùng với Tình
- Lệch spec / quyết định mới: không
- Bàn giao: nhận B7b (phần sweep tham chiếu)
- Còn lại / bước tiếp: H5.3 so θ̂ với θ\*

### 2026-10-02 · Gate P6 · ý kiến của Hoàng về T-31 · gate P6 đạt trên lưới tham chiếu (chờ mentor xác nhận)
- Nhánh/PR: `develop2`
- Đã làm: đọc T-31, Q24 của Tình và bảng B7b; đối chiếu với kết quả H4.2
- Test: xem mục "nhận B7b"
- Ý kiến: (1) Trên lưới tham chiếu 0–30, đường N(π_θ) có đủ ba đoạn tăng, phẳng, giảm và cực đại nằm bên trong lưới, nên tiêu chí của Gate P6 trong `plan.md` thỏa. (2) Đồng ý báo cáo θ\* là một tập và chấm θ̂ bằng regret theo N. (3) T-31 thay lưới θ và số seed của plan P6 (12 θ × 10 seed thành 16 θ × 30 seed), nên kết luận gate cần mentor xác nhận; không đổi B, không sinh lại B7a. (4) Đồng ý với Q24 của Tình rằng chênh lệch khoảng 10 chuyến/ngày giữa các θ lân cận trong đoạn phẳng là nhiễu của κ auto
- Số liệu liên quan H4.2: θ̂ không ngân sách = 0 [0; 0,289] nằm **ngoài** tập θ\*. Regret theo N (`analysis.metrics.sweep_regret`, 30 seed): θ = 0: 53,27 ± 4,82 chuyến/ngày (1,37%); θ = 0,3: 17,00 ± 4,52; θ = 0,35 (mặc định): 14,43 ± 4,10; θ = 0,4: 11,87 ± 4,22
- Lệch spec / quyết định mới: không
- Bàn giao: không
- Còn lại / bước tiếp: Tình và Hoàng báo mentor T-31 và Gate P6

### 2026-10-02 · đính chính · số câu hỏi mở của Hoàng về TLC là Q25
- Nhánh/PR: `develop2`
- Đã làm: Q24 trên `develop` là câu hỏi của Tình về nhiễu κ auto. Câu hỏi của Hoàng về hình dạng cung cầu theo giờ so với NYC TLC (đã chốt bằng H-20) đổi thành **Q25** trong `decisions.md` và `analysis/tlc_hourly.py`. Các mục log của Hoàng ở trên ghi "Q24" cho câu hỏi này: đọc là Q25
- Test: không đổi code chạy
- Lệch spec / quyết định mới: không
- Bàn giao: không
- Còn lại / bước tiếp: không

### 2026-10-05 · Q24, Q26–Q28 · chốt theo đề xuất của Tình · xong
- Nhánh/PR: `develop2` (đã kéo `develop` ở `a5ccc50`)
- Đã làm: Hoàng đồng ý toàn bộ đề xuất của Tình nên đóng Q26 (gộp Q24), Q27, Q28 thành H-21, H-22, H-23 trong `decisions.md`; sửa spec D12 và §6 (κ auto lặp đến điểm bất động, chung seed pilot); thêm ghi chú H-23 vào `tests.md` §4
- Test: không đổi code
- Lệch spec / quyết định mới: H-21 (lệch spec §6, D12 cũ; đã sửa spec), H-22, H-23
- Bàn giao: không. Việc kéo theo cho Tình: cài H-21 trong `sim/runner.py` (khóa YAML số lần lặp), chạy lại sweep B7b
- Còn lại / bước tiếp: H5.1 giao B8; chốt định nghĩa ŝ với Tình theo H-22 trước H5.3

### 2026-10-05 · H5.1 · giao B8: hàm điểm τ̂ nền và parquet dự đoán · xong
- Nhánh/PR: `develop2` (PR cuối S5, hoặc PR sớm nếu Tình cần trước)
- Đã làm: `analysis/scores.py`: `predict_frame`, `SCORE_FUNCTIONS`, CLI `predict <run dir> <out.parquet>`; `tests/test_estimate.py` (+4: nạp hàm điểm trong tiến trình `spawn` ×2, `predict_frame` khớp hàm điểm và tất định, CLI không có cột ẩn); `runs/b8/predictions_<bộ>.parquet` cho 5 bộ B7a (718.749 dòng mỗi bộ); mục B8 trong `datasets.md`
- Test: `pytest -q` → 480 passed, 1 skipped (py3.12 `.venv`); chạy thật `evaluate` với `score_fn=analysis.scores:tau_per_dollar_baseline`, 2 seed, 2 tiến trình: N = 3.932,5 (se 60,5), chi 5.545,80 = B
- Số liệu cho T5.2: Qini (`qini_coef`, `rider_ab_28d`, trong cửa sổ) `tau_x_baseline` +846,4; `tau_per_dollar_baseline` −633,9; `heuristic_low_freq` −985,9. Dưới cùng B (H4.2) thứ tự N lại ngược: per_dollar 3.896,0 > heuristic 3.882,8 > tau_x 3.862,4, là ví dụ "Qini cao hơn mà N thấp hơn"
- Lệch spec / quyết định mới: không
- Bàn giao: giao B8; người nhận kiểm tra: `pytest -q tests/test_estimate.py`
- Còn lại / bước tiếp: H5.2 DR-learner

