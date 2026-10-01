# Nhật ký quyết định

File này ghi lại: mọi lệch khỏi `docs/spec.md`, mọi tham số được thêm hoặc đổi, và mọi câu hỏi chưa chốt.

Quy ước:
- Mỗi mục ghi ngày, nội dung, lý do và người duyệt.
- ID: `L..` là quyết định về khung dự án (P0); `T-..` do Tình chốt, `H-..` do Hoàng chốt. Thêm dòng ở cuối bảng.
- Khi một câu hỏi mở được trả lời: thêm dòng vào Nhật ký, chuyển câu hỏi sang "Câu hỏi đã chốt" kèm quyết định, rồi sửa spec, tests, schema hoặc YAML tương ứng.

---

## Nhật ký

| Ngày | ID | Nội dung | Lý do | Người duyệt |
|---|---|---|---|---|
| 2026-09-30 | L1 | Config nhiều lớp: `--config` được lặp lại, file sau deep-merge đè file trước, rồi mới áp `--set`. `tests/fixtures/tiny.yaml` chỉ chứa các khóa khác `default.yaml`. | Không phải chép lại toàn bộ YAML cho cấu hình test; không đổi ngữ nghĩa tham số. | đã chốt |
| 2026-09-30 | L2 | Dataclass config không có giá trị mặc định: thiếu khóa là lỗi. YAML có khóa trùng cũng là lỗi. | `default.yaml` là nguồn duy nhất của tham số (quy tắc cứng 1). PyYAML mặc định lặng lẽ giữ khóa trùng cuối cùng. | đã chốt |
| 2026-09-30 | L3 | `config_hash` tính trên config **đã chuẩn hóa kiểu**, ví dụ `1` và `1.0` ở trường float cho cùng hash; không tính trên YAML thô. | Hai cách viết cùng một giá trị không được cho hai hash khác nhau. | đã chốt |
| 2026-09-30 | L4 | Kiểm tra khoảng giá trị (spec §9), gồm cả ràng buộc thời gian: `tick_s` chia hết 86400; `slot_min` chia hết 1440; một slot là số nguyên tick; `experiment.block_min` là bội của `slot_min`; `burnin_min < block_min`. | [report Bảng 3]: block switchback là bội số của slot. Spec §2 cần `slot_of_day` nguyên. | đã chốt |
| 2026-09-30 | L5 | `rng`: luồng WORLD băm với `world_seed` thay cho `run_seed`; các luồng khác dùng `run_seed`. Khi gọi WORLD chỉ truyền phần "…" của khóa (ví dụ mã phần thế giới). | Spec §5: WORLD không phụ thuộc `run_seed`. | đã chốt |
| 2026-09-30 | L6 | `hash64` = BLAKE2b 8 byte trên các số nguyên int64 little-endian. Mã luồng cố định: WORLD=1, DEMAND=2, SESSION=3, CELLSLOT=4, RIDER=5, DRIVER=6, SESSION_BATCH=7. Khóa phải là số nguyên (float, str bị từ chối). Test chốt cứng giá trị băm. | Hàm `hash()` của Python không ổn định giữa các tiến trình. Đổi hàm băm sẽ đổi mọi số ngẫu nhiên và làm hỏng khả năng tái lập dữ liệu. | đã chốt |
| 2026-09-30 | L7 | `requires-python >= 3.11` thay vì khóa cứng 3.11. Code viết theo cú pháp 3.11; test chạy bằng `.venv` Python 3.11. | Máy dev đang dùng 3.13 làm mặc định. | đã chốt |
| 2026-09-30 | L8 | Thêm `sim/__main__.py` (không có trong spec §3) để chạy được `python -m sim`. | Spec §7 dùng lệnh `python -m sim run`. | đã chốt |
| 2026-09-30 | L9 | Test tĩnh (`tests/test_rng.py`) cấm trong `sim/`: `import random`, `numpy.random.<hàm>` toàn cục và `default_rng`. Chỉ cho phép `np.random.Generator` (type hint) và `np.random.Philox` (chỉ trong `rng.py`). | Quy tắc cứng 4 (CRN). | đã chốt |
| 2026-09-30 | L10 | Đổi tên `docs/Supply-Aware Promotion Uplift.md` thành `docs/problem_statement.md`, file Survey thành `docs/survey.md`. | Tên có dấu cách, gạch dài và dấu cách trước `.md` gây lỗi khi gõ lệnh và tạo link. | đã chốt |
| 2026-09-30 | L11 | `BudgetLedger` đặt trong file riêng `sim/budget.py` và được re-export từ `sim/state.py`; spec §3 xếp nó trong `state.py`. | `state.py` (Hoàng) và ledger (Tình) có chủ khác nhau; file riêng tránh hai người sửa chung một file. | đã chốt |
| 2026-09-30 | L12 | Bước 5 có **một** lớp voucher trong `pricing.py`: gọi `cell_state` khi đổi slot, gọi `offer`, giữ ngân sách theo thứ tự `session_id`, điền trường thí nghiệm. Ngân sách áp ở một chỗ cho mọi chính sách, kể cả all_on có ngân sách. **Lệch spec §6**, vốn truyền ledger vào `offer`. | Một điểm nối duy nhất giữa lõi (Hoàng) và chính sách (Tình); ngân sách áp giống nhau cho mọi chính sách. | đã chốt |
| 2026-09-30 | L13 | Hai người làm song song theo `docs/phan_cong.md`: mỗi file một chủ, hợp đồng giao diện chốt ở Sprint 0, gate P2/P3/P6 chặn tích hợp và sinh dữ liệu. `plan.md` và CLAUDE.md sửa theo. | Làm tuần tự từng mốc không kịp lịch 5 tuần. | đã chốt |
| 2026-09-30 | T-01 | **Simulator chính là ABM theo `docs/spec.md`.** `marketplace_sim.py` không tồn tại và không được cung cấp. Kết luận "simulator chính là `marketplace_sim.py`" trong `docs/BaoCao_MaNguon.pdf` coi như đã cũ. M9 repositioning giữ bật mặc định với quy tắc tĩnh (Q1). | Không có mã nào khác để dùng; report M9 bật repositioning tĩnh, còn "ngoài phạm vi" trong đề bài là repositioning **theo cầu**. | Tình |
| 2026-09-30 | T-02 | **Ca làm tuần hoàn.** Tài xế online khi `((t/3600 − shift_start) mod 24) < shift_len`. Lúc t = 0, xe nào đang trong ca theo quy tắc này thì khởi tạo `idle` tại ô xuất phát, `shift_end = shift_start + shift_len − 24` (giờ ngày 0). Warm-up giữ 60 phút (Q2). | Không có ca nào bắt đầu trước 6:00, nên khởi động lạnh làm 00:00–06:00 ngày đầu không có xe. Quy tắc tuần hoàn cho trạng thái dừng ngay từ t = 0 và khớp "mỗi ngày dùng cùng lịch ca" (spec §4.8). | Tình |
| 2026-09-30 | T-03 | **Kỳ ngân sách neo theo cửa sổ đánh giá**, dài `min(1440, window_min)` phút, kỳ d = `[window_start + d·P, window_start + (d+1)·P)`. Mỗi kỳ có sổ riêng; mỗi reservation thuộc kỳ của `open_time` session và giữ nguyên kỳ đó qua cool-down. Warm-up là kỳ −1 với ngân sách `B × warmup_min / P`, không tính vào đánh giá. Bất biến `spent + committed + reserved ≤ B` giữ theo từng kỳ. Pilot tính B: `fraction × chi tiêu trung bình mỗi kỳ` trong cửa sổ. κ auto: chi tiêu trung bình mỗi kỳ ≤ B (Q3). | Reset lúc 00:00 lệch cửa sổ 01:00–01:00: warm-up tiêu ngân sách ngày 0 và giờ cuối cửa sổ nhận thêm B mới. Neo theo cửa sổ làm chi tiêu của một cửa sổ 1 ngày đúng bằng ≤ B. Warm-up vẫn phát voucher để trạng thái đầu cửa sổ phản ánh chính sách. | Tình |
| 2026-09-30 | T-04 | **Sửa test M1:** `ETA_in(I)` không tăng theo I; giảm ngặt trong miền còn trên sàn; không nhỏ hơn `eta_floor_min`; với I = 1 nhỏ hơn T tới ô kề (Q4). | Với tham số mặc định ETA chạm sàn từ I ≥ 5 (đêm) hoặc I ≥ 13 (cao điểm), nên "giảm ngặt" toàn miền không thể pass. Giữ sàn vì ETA 0 phút không thực tế. | Tình |
| 2026-09-30 | T-05 | Thêm `time.window_min: null`. null = `days_per_run × 1440`; nếu đặt thì là độ dài cửa sổ đánh giá (phút), phải là bội của `slot_min`, và `days_per_run` bị bỏ qua. `tiny.yaml` đặt 120 (Q5). | tests.md yêu cầu fixture 2 giờ; cửa sổ ngắn còn dùng để chạy nhanh khi debug. | Tình |
| 2026-09-30 | T-06 | `session_id = ((day·ticks_per_day + tick_of_day)·N + cell)·1000 + k` với `ticks_per_day = 86400 // tick_s` (Q6). | Hằng 1440 chỉ đúng khi `tick_s = 60`. Với cấu hình mặc định giá trị không đổi. | Tình |
| 2026-09-30 | T-07 | **Rút sẵn `u_score`** ở cuối danh sách số ngẫu nhiên của mỗi session, sau `e_cancel`. `SessionBatch` mang `u_target`, `u_explore`, `u_explore_arm`, `u_score`; chính sách **không** được gọi `rng_for(SESSION, …)`. `scores.random` trả về `u_score` (Q7). | Nếu chỉ rút khi cần, thứ tự rút trong luồng SESSION phụ thuộc chính sách, phá CRN. | Tình |
| 2026-09-30 | T-08 | **`throughput_curve`:** `supply.shift_mode = always_on` (mọi xe online suốt lượt, xuất phát tại ô gốc); `hour_profile` và `speed_factor_by_hour` lấy hằng số tại `throughput.reference_hour` (mặc định 18); quét `throughput.demand_scale_grid` (16 mức 0,25…4,0) × `throughput.n_seeds` (3). Đo trên toàn cửa sổ sau warm-up: `completed_per_h = N_completed / giờ cửa sổ` (Q8). | A1 cần "fleet cố định, trạng thái ổn định"; lịch ca làm số xe đổi theo giờ. Giờ 18 là đỉnh cầu (1,85) và tốc độ thấp nhất (0,75). | Tình |
| 2026-09-30 | T-09 | `utilization = (E + O) / (I + E + O)`; xe `repositioning` và `offline` không tính (Q9). | Giữ công thức spec. Công thức report `(L − I)/L` gộp xe repositioning vào "bận", làm chỉ số phụ thuộc M9. | Tình |
| 2026-09-30 | T-10 | `slack = I / E` (xe rảnh / xe đang đi đón), như spec và report. Câu chữ "(xe − đang chở) / đang đón" trong `BaoCao_MaNguon.pdf` Bảng 7 là lỗi diễn đạt, không dùng (Q10). | Ngưỡng WGC 0,25–0,45 của Castillo và `theta_grid` chỉ có nghĩa với I/E. D4 vẫn đổi được qua `policy.threshold.indicator`. | Tình |
| 2026-09-30 | T-11 | **`schema.md` là danh sách cột ẩn chuẩn.** Mọi số rút sẵn của session (`u_book, u_target, u_explore, u_explore_arm, u_score, trip_noise, e_cancel`) đều là cột ẩn và được ghi vào `hidden/sessions_hidden` để tái lập. CLAUDE.md quy tắc 3 trỏ về schema (Q11). | Hai danh sách khác tên (`beta` vs `beta_price`) gây lọt lưới; ghi đủ số rút sẵn cho phép tái lập từng session. | Tình |
| 2026-09-30 | T-12 | A2(b): π1 = `all_on` **có ngân sách** (FixedPolicy qua lớp voucher, phát đến khi hết B mỗi kỳ), π2 = threshold θ = 0,3 có ngân sách. Chỉ lượt GTE mới chạy all_on không ngân sách (Q12). | Hai chính sách phải cùng B thì phương sai hiệu mới có nghĩa. | Tình |
| 2026-09-30 | T-13 | Code phân tích tuần 5 đặt trong `analysis/`; `sim/` không import từ đó. Thư viện khai báo ở extras `[analysis]`: scikit-learn, lightgbm, scikit-uplift, matplotlib. DR-learner tự viết theo Kennedy (2023) trên sklearn/LightGBM; Qini kiểm chéo bằng scikit-uplift; **không** dùng causalml. Đồ thị gate (throughput, N(π_θ)) cũng vẽ bằng script trong `analysis/` (Q13). | Đề bài: LightGBM/sklearn là đủ. causalml nặng và hay lỗi cài trên Windows; DR-learner chỉ vài chục dòng. | Tình |
| 2026-09-30 | T-14 | **P7 (NYC) làm sau P8, nếu còn thời gian.** Khi làm: pipeline dữ liệu (ngoài `sim/`, được dùng `h3`) sinh thêm `nyc/neighbors.parquet` (`cell_id, neighbor_id`) và `nyc/clusters.parquet` (`cell_id, cluster_id`); `demand_rate` gộp theo giờ (trung bình các ngày trong tuần), simulator không có chiều `dow` (Q14). | Tiêu chí nghiệm thu (đề bài §8) không cần NYC; report chạy thí nghiệm chính trên bản tổng hợp. Hợp đồng §10 thiếu lân cận và cụm. | Tình |
| 2026-09-30 | T-15 | **Định nghĩa bộ đếm và chỉ số:** (a) bộ đếm trong `slot_snapshots` tính theo **thời điểm sự kiện** và **ô đón**: `n_sessions, n_offers, n_requests` theo `open_time`; `n_matched`, `mean_pickup_eta_min` theo `matched_time`; `n_abandoned, n_cancelled` theo thời điểm hủy; `n_completed, voucher_spent_usd` theo `dropoff_time`. (b) `mean_slack` của `throughput_curve` = tổng (xe rảnh × tick) / tổng (xe đi đón × tick) trên cửa sổ, `inf` nếu mẫu số 0. (c) `abandon_rate = n_abandoned / n_requests`, `cancel_rate = n_cancelled / n_requests`, tính trên order tạo trong cửa sổ. (d) `block = floor(t / (block_min·60))` tính từ **đầu lượt chạy**; `−1` chỉ dành cho lượt không thí nghiệm (Q15). | Cần định nghĩa duy nhất trước khi viết `monitor.py` và `runner.py`. Tính từ đầu lượt tránh block âm trong warm-up trùng mã −1. Warm-up 60 = block 60 nên cửa sổ vẫn bắt đầu đúng biên block. | Tình |
| 2026-09-30 | T-16 | P8 thêm bộ `generate` 28 ngày với `experiment.design = rider_ab` (Q16). | RQ3 và tiêu chí §8.4 cần độ chệch A/B theo rider so với GTE. | Tình |
| 2026-09-30 | T-17 | **Chốt theo đề xuất của đội:** D3 (π_θ hai tầng), D4 (slack là chỉ số mặc định), D5 (`max_pickup_eta_min = 30`), `budget.fraction = 0,3`, `explore_frac = 0,05` giữ như YAML hiện tại. Mentor có thể đổi bằng config, không cần sửa code. | Không thể chờ đến P4 mới bắt đầu; mọi lựa chọn đều là tham số. | Tình, Hoàng |
| 2026-09-30 | T-18 | Khóa YAML mới (kèm `config.py`): `time.window_min`, `supply.shift_mode`, `throughput.{demand_scale_grid, n_seeds, reference_hour}`, `runner.n_procs`. Chi tiết ở `default.yaml`. | Theo T-05, T-08 và runner nhiều tiến trình. Thêm ngay để Sprint 0 không phải sửa `config.py` (file chung) lần nữa. | Tình |
| 2026-09-30 | H-01 | `config.py` kiểm tra `time.warmup_min` là bội của `experiment.block_min`. | Block tính từ đầu lượt chạy (T-15), nên cửa sổ chỉ bắt đầu đúng biên block khi warm-up là số nguyên block. Trước đây điều này chỉ đúng vì cả hai cùng bằng 60; đổi warm-up thành 45 thì block lệch cửa sổ mà không báo lỗi. | Hoàng (chờ Tình review PR) |
| 2026-09-30 | H-02 | `config.py` kiểm tra `time.window_min` ≤ 1440 hoặc là bội của 1440. | Kỳ ngân sách dài `min(1440, window_min)` (T-03). Cửa sổ dài hơn 1 ngày mà không tròn ngày (ví dụ 1500) sẽ có kỳ cuối ngắn nhưng vẫn nhận đủ B, làm méo chi tiêu trung bình mỗi kỳ (pilot tính B, κ auto). | Hoàng (chờ Tình review PR) |
| 2026-09-30 | H-03 | Thêm `eval_window_min(cfg)` và `budget_period_min(cfg)` trong `sim/config.py`. Mọi module lấy độ dài cửa sổ và kỳ ngân sách qua hai hàm này, không tự đọc `window_min` / `days_per_run`. | Quy tắc "`window_min` nếu đặt, ngược lại `days_per_run × 1440`" (T-05) và `P = min(1440, window)` (T-03) được dùng ở engine, budget, runner, experiment của cả hai người; một hàm duy nhất tránh mỗi nơi tính một kiểu. | Hoàng (chờ Tình review PR) |
| 2026-09-30 | T-19 | **Hợp đồng Sprint 0 (B0) đã cài trong code.** (a) Mỗi bước engine có chữ ký `step(ctx: SimContext, t)`; `SimContext` (`state.py`) gom cfg, `Clock`, world, rng, policy, hai buffer, bộ đếm, ledger, lớp voucher, monitor. (b) Cột chuỗi (`assign_mechanism`, `status`, `cancel_reason`) lưu mã int8 trong buffer, logger đổi sang chuỗi theo `Column.codes`; số rút sẵn lưu float64 trong buffer, ghi float32 ra `hidden/`. (c) `SessionBatch` chỉ có cột quan sát + 4 uniform của chính sách; có assert lúc import. (d) `SnapshotStore` công bố theo thứ tự slot; `SnapshotView(k)` ném `LookAheadError` với slot ≥ k, trả NaN khi chưa công bố. (e) `VoucherLayer.decide` trả `VoucherOutcome` (arm, voucher_cents, budget_blocked, budget_period, promo_on_cell, cell_propensity, slack_hat); `budget_blocked` thuộc lớp voucher, không thuộc `OfferDecision`. (f) `engine.run(cfg, world, policy, rng, *, log_level, profile, budget_usd, enforce_budget) -> RunResult`; N, V chỉ tính ở engine. (g) `tests/test_schema_contract.py` đối chiếu tên cột trong code với `docs/schema.md`. (h) Thêm cột quan sát `budget_period` (int16) vào `sessions`. | Hai luồng code song song trên cùng giao diện; test đối chiếu schema giữ tài liệu và code luôn khớp. | Tình (chờ Hoàng review PR) |
| 2026-09-30 | T-20 | **Rà lại ba điểm của T-19, giữ nguyên cả ba.** (1) Mỗi bước là `step(ctx: SimContext, t)`: chữ ký không đổi khi một bước cần thêm dữ liệu, nên hai người không phải sửa engine của nhau; rủi ro bước đọc thứ không được phép (quy tắc 5) được chặn bằng `tests/fakes.py::with_forbidden` (cắm `ForbiddenAccess` vào `ctx.monitor`, `ctx.sessions`, `ctx.orders`, dùng cho test M9) và test chữ ký tĩnh trong `test_engine.py`. Thêm `engine.build_context` để unit test gọi từng bước. (2) `budget_blocked` thuộc `VoucherOutcome` của lớp voucher, vì theo L12 ngân sách áp *sau* khi chính sách quyết định; đưa vào `OfferDecision` là bắt lớp voucher sửa đối tượng chính sách trả về. `phan_cong.md` mục 4 sửa theo. (3) Cột `string` lưu mã int8 trong buffer: numpy không giữ chuỗi biến thiên mà không tạo object mỗi dòng (quy tắc 7); so sánh mã vector hóa được; schema chỉ quy định kiểu trên đĩa và logger dùng `state.decode_codes` để ghi chuỗi. Ghi chú thêm vào `schema.md`. | Ba điểm đều là hệ quả của L12 và quy tắc cứng 5, 7; không có phương án thay thế rẻ hơn. | Tình (Hoàng có thể phản đối khi review B0) |
| 2026-10-01 | H-04 | **`SpaceTime` mở rộng so với hợp đồng B0, giữ nguyên các trường và chữ ký đã có.** (a) Thêm trường: `radius`, `rings` (`rings[z][k-1]` = các ô cách z đúng k vành, id tăng dần), `center_dist_km`, `speed_kmh[24]`, `detour_factor`, `nn_const`, `eta_gamma`, `eta_floor_min`, và `max_pickup_eta_min`, `max_ring` chép từ `cfg.matching`. (b) Thêm `SpaceTime.find_pickup(cell, hour, idle_count) -> (ô_nguồn, eta)`, trả `(-1, inf)` khi không đón được; `quote_eta` gọi hàm này và `matching.py` (H2.1) cũng sẽ gọi hàm này. (c) Giới hạn `max_pickup_eta_min` áp cho cả ETA trong ô, không chỉ ETA từ vành. (d) Mọi mảng của `SpaceTime` bị khóa ghi. | Spec §4.1 yêu cầu ETA báo giá dùng cùng quy tắc tìm xe với M5; một hàm duy nhất thì hai nơi không lệch nhau. Giữ giới hạn trong `SpaceTime` để chữ ký `quote_eta(cell, hour, idle_count)` của hợp đồng không phải thêm tham số. Spec §4.5 bước 3 nói "ETA > max_pickup_eta_min thì chờ" mà không phân biệt xe trong ô hay ngoài ô. | Hoàng (chờ Tình review PR) |
| 2026-10-01 | H-05 | **Sinh thế giới và nhu cầu (H1.2).** (a) Luồng WORLD khóa `(WorldPart, chỉ số biến)` với `CELL_WEIGHT = 1`, `RIDERS = 2`, `DRIVERS = 3` (không đổi số); mỗi biến một bộ sinh riêng, nên rider i và tài xế j giữ nguyên thuộc tính khi đổi `n_riders` hoặc `fleet_size` (trừ `zf`, là z-score trên cả quần thể). (b) `World` thêm trường `tables` (bảng cộng dồn để lấy mẫu rider và ô đích); mọi mảng của `World` bị khóa ghi. (c) Mỗi session lấy 3 số đều trước các số rút sẵn: đồng xu ô nhà, chọn rider, chọn ô đích; khớp hai mục `rider`, `dest` của `SESSION_DRAW_ORDER`. (d) `demand.spawn` cộng `slot_counters.n_sessions` theo ô đón (T-15); `pricing.quote` không cộng lại. (e) Giữ một bộ sinh số cho mỗi session, không dùng SESSION_BATCH. (f) `tests/test_engine.py` chạy khung với `demand_scale = 0` cho đến tích hợp 1. | (a) P3 hiệu chỉnh `fleet_size`; đổi số xe không được xáo lại ca của các xe đã có. (e) Đo được 1,56 giây cho 1 ngày mô phỏng (30.397 session), khoảng 5% của mục tiêu 30 giây (A5). (f) `pricing.quote` chưa nhận session trước T2.1, còn `spawn` đã sinh session thật. | Hoàng (chờ Tình review PR) |
| 2026-10-01 | T-21 | **Giao diện hàm điểm (`policies/scores.py`, T1.3).** `score_fn(batch, s_hat) -> float[n]`: `s_hat` là ŝ của ô đón **từng session** (float [n], NaN khi chính sách không dự báo); kết quả một số thực mỗi session, cao hơn = ưu tiên phát; `score_batch` kiểm hình dạng, kiểu số và ép float32. `random` trả `u_score` rút sẵn (T-07), `heuristic_low_freq` trả `−x_freq`; chuỗi `"module:function"` nạp bằng `import_callable`, hàm này cũng nạp engine cho `runner` (spec §7, tiến trình con spawn). | Spec §6 viết `score_fn(SessionBatch, ŝ)` mà không nói ŝ theo ô hay theo session; theo session thì B8 (Hoàng) chỉ cần nối cột của batch, không cần biết ô. Một loader cho cả score_fn và engine để hai chỗ không lệch nhau. | Tình |

---

## Câu hỏi đã chốt (giữ lý do chi tiết)

### Q1. Simulator chính là ABM theo spec hay `marketplace_sim.py`?
- `docs/BaoCao_MaNguon.pdf` (29/09) kết luận: simulator chính là `marketplace_sim.py`; ABM 13 module chỉ là "bản rút gọn, tùy chọn". `docs/problem_statement.md` cũng dựa trên `marketplace_sim.py`.
- CLAUDE.md, spec và plan (30/09) coi ABM là sản phẩm chính, và `marketplace_sim.py` không có trong repo.
- **Quyết định (T-01):** ABM theo spec là simulator chính, vì `marketplace_sim.py` không tồn tại và không được cung cấp. M9 giữ bật với quy tắc tĩnh.

### Q2. Đội xe khởi động lạnh lúc t = 0
- t = 0 là 00:00. Ca sớm nhất bắt đầu lúc 6:00, nên từ 00:00 đến 6:00 ngày đầu không có xe nào online. Ở trạng thái dừng, Monte Carlo trên `shift_start_mixture` cho tỷ lệ đội xe online: 00:00 ≈ 40%, 03:00 ≈ 18%, 05:00 ≈ 8%.
- **Quyết định (T-02):** ca làm tuần hoàn theo ngày; lúc t = 0 xe nào đang trong ca thì `idle` tại ô xuất phát. Không có ca nào chồng lên ca kế tiếp của cùng tài xế vì `shift_len ≤ 11 < 24`.

### Q3. Cửa sổ đánh giá lệch ngày lịch, ảnh hưởng ngân sách "theo ngày"
- Cửa sổ là [01:00 ngày 0, 01:00 ngày 1), nhưng spec reset ngân sách lúc 00:00: warm-up tiêu ngân sách ngày 0, và giờ cuối cửa sổ nhận thêm một B mới.
- **Quyết định (T-03):** kỳ ngân sách neo theo cửa sổ; mỗi reservation thuộc kỳ của session; warm-up có ngân sách pro-rata riêng. Cách này cũng cho cửa sổ ngắn hơn 1 ngày (T-05) một kỳ duy nhất.

### Q4. Test M1 "`ETA_in(I)` giảm ngặt theo I" mâu thuẫn với sàn `eta_floor_min`
- **Quyết định (T-04):** sửa `tests.md`: không tăng theo I, giảm ngặt khi còn trên sàn.

### Q5. `tiny.yaml` cần "2 giờ mô phỏng" nhưng chưa có khóa để biểu diễn
- **Quyết định (T-05):** thêm `time.window_min`. Cửa sổ < 1 ngày thì `slack_lag_day` luôn NaN và kỳ ngân sách bằng cả cửa sổ.

### Q6. Hằng 1440 trong công thức `session_id`
- **Quyết định (T-06):** dùng `ticks_per_day`. Với N = 37, 28 ngày, ID lớn nhất ≈ 1,5·10⁹, còn rất xa giới hạn int64.

### Q7. Số ngẫu nhiên cho `score_fn = random`
- **Quyết định (T-07):** luôn rút sẵn `u_score`. Danh sách rút sẵn cố định: `rider, dest, u_book, u_target, u_explore, u_explore_arm, trip_noise, e_cancel, u_score`. Đây là một phần của hợp đồng CRN: đổi thứ tự sẽ đổi mọi số ngẫu nhiên.

### Q8. A1: đội xe trong `throughput_curve`
- Report đo "giữ cầu, giảm xe"; tests.md A1 giữ xe, quét cầu. Cả hai hợp lệ; spec thắng.
- **Quyết định (T-08):** mọi xe online suốt lượt; hằng số theo `reference_hour`; đo trên toàn cửa sổ sau warm-up. Test có thể rút ngắn cửa sổ bằng `window_min` để chạy nhanh, nhưng số liệu A1 báo cáo phải chạy cửa sổ đủ 1 ngày.

### Q9. Định nghĩa utilization
- **Quyết định (T-09):** giữ công thức spec; xe repositioning không tính.

### Q10. Định nghĩa slack không thống nhất giữa các tài liệu
- **Quyết định (T-10):** `slack = I/E`. Báo cáo mã nguồn là PDF, không sửa được; ghi nhận ở đây.

### Q11. Danh sách cột ẩn: CLAUDE.md và schema.md khác nhau
- **Quyết định (T-11):** schema.md là chuẩn; mọi số rút sẵn của session là cột ẩn. `score` (đầu ra của chính sách) vẫn là cột quan sát, kể cả khi `score_fn = random` cho `score = u_score`: test rò rỉ kiểm theo tên cột, không theo giá trị.

### Q12. A2(b): `all_on` có áp ngân sách không?
- **Quyết định (T-12):** có. Chỉ lượt GTE mới không ngân sách (D10).

### Q13. Thư viện và chỗ đặt code phân tích tuần 5
- **Quyết định (T-13):** `analysis/` + extras `[analysis]`; không dùng causalml. Dữ liệu `hidden/` chỉ dùng để đánh giá, không nối vào dữ liệu huấn luyện.

### Q14. Bản NYC (P7) thiếu dữ liệu và công cụ
- **Quyết định (T-14):** làm sau P8 nếu còn thời gian; bổ sung hợp đồng khi làm.

### Q15. Định nghĩa bộ đếm theo slot và chỉ số tổng hợp
- **Quyết định (T-15):** xem dòng T-15. Bộ đếm theo thời điểm sự kiện vì `slot_snapshots` mô tả trạng thái thị trường theo thời gian thực; hiệu ứng theo slot đặt xe thì tính lại từ `sessions` và `orders`.

### Q16. P8 thiếu bộ dữ liệu `rider_ab`
- **Quyết định (T-16):** thêm.

---

## Câu hỏi mở

Câu hỏi mới ghi vào đây theo mẫu: tiêu đề, bối cảnh, đề xuất, mốc bị chặn.

### Q17. Mode `evaluate` dùng `n_seeds` nào?
- Bối cảnh: spec §7 ghi `evaluate` = "1 chính sách × `n_seeds`", nhưng YAML chỉ có `sweep.n_seeds`, `gte.n_seeds`, `throughput.n_seeds`. Thêm khóa mới cần PR chung (`config.py`).
- Đề xuất (Tình): `evaluate` dùng `sweep.n_seeds`, vì bảng N(π)/V(π) tuần 5 so các chính sách dưới cùng B và cần cùng số seed với `sweep_theta`.
- Mốc bị chặn: T2.4 (`runner.evaluate`). Không chặn T1.4 (`throughput_curve` có `throughput.n_seeds` riêng).

---

## Ghi chú kỹ thuật (đã kiểm, không cần quyết định)

- Kiểm bằng script: với R = 1..4, torus cho mỗi ô đúng 6 ô kề phân biệt và khoảng cách tối đa bằng R; bất đẳng thức tam giác đúng (đã kiểm với R ≤ 3). Với R = 3, cụm cấp 7 có kích thước [3, 3, 4, 6, 7, 7, 7] và mỗi ô cách tâm cụm ≤ 1. Đều khớp spec.
- Với R = 3 và tốc độ thấp nhất (0,75 × 18 km/h), T xa nhất (3 vành) ≈ 22,5 phút, nhỏ hơn `max_pickup_eta_min = 30`. Ở cấu hình mặc định, nhánh "ETA > max_pickup_eta" không bao giờ xảy ra: mọi order được ghép ngay khi còn bất kỳ xe rảnh nào trong lưới. Đúng ý đồ WGC, nhưng test M5 cho giới hạn này phải đặt giới hạn nhỏ hơn trong fixture.
- `T[a, a, h]` đúng bằng `ETA_in(1, h)` vì `nn_const = intra_cell_dist_factor = 0,5`. Không sai, chỉ là trùng hợp đáng biết khi đọc số.
- `docs/survey.md` bị hỏng khi export: mất toàn bộ ký tự `/ \ : | ?`, nên URL, công thức LaTeX và bảng đều vỡ. Cần export lại từ bản gốc.
