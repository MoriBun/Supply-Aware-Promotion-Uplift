# Kế hoạch kiểm thử

Chạy toàn bộ kiểm thử: `pytest -q`. Kiểm thử chậm (đánh dấu `@pytest.mark.slow`): `pytest -q -m slow`.
Mỗi mốc trong `docs/plan.md` chỉ được coi là xong khi các test của mốc đó **pass**.
Test dùng cấu hình nhỏ `tests/fixtures/tiny.yaml` (lớp phủ lên `default.yaml`: bán kính 1, fleet 10, cửa sổ 2 giờ qua `time.window_min: 120`) trừ khi ghi khác.

Ký hiệu: **[U]** unit, **[I]** tích hợp, **[A]** nghiệm thu của [report] (5 kiểm thử bắt buộc), **[CAL]** hiệu chỉnh.

---

## 1. Unit test theo module

### M1 SpaceTime (`tests/test_space.py`)
- [U] Số ô: R = 1, 2, 3 cho 7, 19, 37 ô.
- [U] Torus: mọi ô có **đúng 6** ô kề phân biệt; quan hệ kề đối xứng.
- [U] Khoảng cách torus đối xứng, bằng 0 trên đường chéo, thỏa bất đẳng thức tam giác, tối đa bằng R.
- [U] `T[a,b,h] > 0`, đối xứng theo a, b; `T[a,a,h] < T[a,b,h]` với mọi b ≠ a.
- [U] `ETA_in(I)` không tăng theo I; giảm ngặt trong miền còn trên `eta_floor_min`; không nhỏ hơn `eta_floor_min`; và với I = 1 nhỏ hơn T tới ô kề (T-04).
- [U] Tắt torus: ô biên có < 6 ô kề (kiểm chế độ không torus vẫn chạy được).

### M2 Demand (`tests/test_demand.py`)
- [U] Trung bình số session mỗi (ô, giờ) qua 2.000 tick khớp λ trong ±5%.
- [U] Cùng `(day, tick, cell)` cho cùng số session, bất kể chính sách.
- [U] Phân phối ô đích: tần suất theo khoảng cách giảm dần.
- [U] `max_wait` có mode ≈ 5 phút (±0,5).

### M3 Pricing / ngân sách (`tests/test_pricing.py`)
- [U] `p_s = a_f + b_f*T`; `v_s = 0,2*p_s`; `net = p − v`.
- [U] **Bất biến ngân sách:** trong mọi tick và với mọi kỳ ngân sách, `spent + committed + reserved ≤ B` (chạy 1 ngày, policy all_on, có ngân sách).
- [U] Rider không đặt thì reserved được nhả; order Abandoned hoặc Cancelled thì committed được nhả.
- [U] Kỳ ngân sách neo theo cửa sổ (T-03): session mở ở kỳ d ghi vào sổ kỳ d, kể cả khi order kết thúc trong kỳ d+1 hoặc cool-down; warm-up có ngân sách `B*warmup_min/P` riêng.

### M4 Choice (`tests/test_choice.py`)
- [U] P tính đúng công thức logit (so với cài đặt tham chiếu trên 1.000 bộ tham số ngẫu nhiên, sai số < 1e-9).
- [U] `u_book` giống nhau giữa hai chính sách cho cùng session.
- [U] `direct_request_effect_fixed_market = p_treat − p_control` và chỉ xuất hiện trong `hidden/`.

### M5 Matching (`tests/test_matching.py`)
- [U] FIFO: order đặt trước được ghép trước khi cùng cạnh tranh một xe.
- [U] Có xe cùng ô thì không lấy xe ô kề.
- [U] Ô trống thì lấy xe ở vành gần nhất; không nhảy sang vành 2 khi vành 1 còn xe.
- [U] Không ghép nếu ETA > `max_pickup_eta_min`; order chờ tick sau.
- [U] Chỉ ghép xe `idle` và còn trong ca.
- [U] Hòa ETA thì chọn xe có `idle_since` nhỏ nhất (tiêu chí phá hòa).
- [U] Vành ngoài hòa T: `most_idle` lấy ô nhiều xe rảnh nhất, hòa tiếp thì id nhỏ; `lowest_id` lấy id nhỏ; báo giá và ghép dùng cùng luật (`test_space.py`, H-37).
- [I] Thế giới đối xứng (`cell_weight_sigma = 0`, 6 giờ): tương quan giữa `cell_id` và số lần ô cho mượn xe ≤ −0,5 với `lowest_id`, |·| < 0,3 với `most_idle` (`test_integration.py`, KN 2.1).

### M6 / M7 Trip và hủy (`tests/test_trips_cancel.py`)
- [U] Thời điểm đón = ghép + ETA; thời điểm trả = đón + trip_time.
- [U] Tiền (H-42): `driver_pay = 0,75 × (gross − phí nền tảng)`; `profit = net − driver_pay` = phí + 0,25 × (gross − phí) − voucher.
- [U] Giá GrabCar Hà Nội: chuyến 6 km, 20 phút ≈ 83.638đ; trong 2 km đầu chỉ giá mở cửa + phí; giá trị B9 cho lại giá cũ; voucher 25% chạm trần 20.000đ (`test_pricing.py`).
- [U] Order Waiting quá `max_wait` thì Abandoned.
- [U] Hủy khi đi đón: xe rảnh ở ô xuất phát nếu hủy trước nửa ETA, ở ô khách nếu sau; `idle_since = t`; không ghép lại trong cùng tick.
- [U] Hazard hủy tăng theo ETA: với 10.000 order giả lập, tỷ lệ hủy ở ETA 10 phút > ở ETA 3 phút; với `exact_time` tỷ lệ khớp hazard chính xác `1 − exp(−h·ETA)`, không có thì khớp `1 − exp(−h·(ETA − 1))` (H-38).
- [U] `exact_time`: `t_cancel` rơi giữa tick cuối và lúc đón thì bước 1 hủy thay vì đón, xe rảnh ở ô khách, `idle_since = t_cancel`, voucher nhả, đếm `n_cancelled`; không có `exact_time` thì đón.

### Biến động W1 (`tests/test_shocks.py`, H7.5)
- [I] Bật biến động nhưng mọi hiệu ứng trung tính thì từng số trùng với tắt biến động; tắt thì không dựng lịch, `T` giữ 24 giờ.
- [I] Mọi chính sách của một seed gặp cùng lịch biến động và cùng session; lịch đổi theo `run_seed`, ô địa điểm chỉ theo `world_seed`.
- [U] Không module chính sách nào import `sim.shocks`; `SessionBatch` không có trường biến động.
- [U] Tần suất và độ lớn theo tham số trên 28 ngày: tỷ lệ ngày mưa, giờ bắt đầu và độ dài trong khoảng, trung bình và độ lệch log của hệ số ngày, tỷ lệ đi làm và nghỉ khi mưa, độ lệch chuẩn giờ vào ca, tần suất sự kiện theo loại, ô địa điểm phân biệt.
- [U] Hệ số cầu kết hợp ngày × mưa × sự kiện; mưa làm mọi thời gian đi chia `speed_mult`; `travel_hour` trả `h + 24` khi mưa.
- [U] Tài xế nghỉ bỏ ngày đó, ca bắt đầu ngày đi làm đầu tiên cộng độ lệch; tài xế được đánh dấu dừng khi mưa và quay lại đúng ô sau mưa.
- [I] `test_driver_state_consistency` chạy thêm trên W1 (ca theo lịch, có mưa và sự kiện trong cửa sổ).
- [I] Lượt chạy log đầy đủ ghi `meta/shocks` khớp lịch đã rút (W1) và bảng rỗng đúng cột (W0) (H7.7).

### M8 / M9 Cung (`tests/test_supply.py`)
- [U] `early_exit_enabled = false` thì không xe nào rời trước `shift_end`.
- [U] Xe hết ca khi đang bận chỉ rời sau khi trả khách.
- [U] Repositioning không đọc snapshot hay cầu hiện tại: mock M11 ném lỗi nếu bị gọi từ `reposition.py`.

### M10 Thí nghiệm (`tests/test_experiment.py`)
- [U] Cụm cấp 7 phủ mọi ô, không chồng lấn; với R = 3 kích thước là [3, 3, 4, 6, 7, 7, 7].
- [U] Tỷ lệ block bật ≈ `p_on` (±3% trên 2.000 block).
- [U] Cờ `in_burnin` đúng cho `burnin_min` phút đầu mỗi block.
- [U] `rider_ab`: arm cố định theo rider trong suốt lượt chạy.

### M11 Monitor (`tests/test_monitor.py`)
- [U] Slack = I/E; `inf` khi E = 0.
- [U] **Không nhìn trước:** chính sách ở slot k chỉ nhận snapshot có `published_at_s ≤ đầu slot k`; `SnapshotView` ném lỗi nếu truy cập slot ≥ k.
- [U] `slack_lag_day` bằng NaN trong ngày đầu, đúng giá trị slot k−96 từ ngày thứ hai.

### M12 Logger (`tests/test_logger.py`)
- [U] Mọi bảng khớp đúng tên cột và kiểu trong `docs/schema.md`.
- [U] `test_no_hidden_leak`: không cột ẩn nào có trong `observed/` hoặc `market/`.

### Chính sách (`tests/test_policies.py`)
- [U] `SessionBatch` truyền cho π_θ không chứa cột ẩn.
- [U] π_θ: θ = 0 thì không ô nào bị tắt; θ rất lớn thì mọi ô tắt.
- [U] π_θ: ŝ không bao giờ là inf: với `scope = cell`, `forecast = persistence`, ô có xe rảnh mà không xe đi đón cho ŝ = `monitor.slack_cap`; `score_fn` chỉ nhận giá trị hữu hạn; chưa công bố thì NaN (T-39).
- [U] Hysteresis: với chuỗi ŝ dao động quanh θ, số lần đổi trạng thái khi h > 0 ít hơn khi h = 0.
- [U] Thí nghiệm và luật cũ ghi `s_hat` = slack đã công bố của slot k−1, chặn ở `slack_cap`, không đổi quyết định; `lag_same_block` sai ở slot đầu khối và slot 0, đúng trong khối và với A/B theo khách; cột session khớp (H7.6, H-40).
- [U] Chính sách cũ: `cell_propensity = (1−ε)·rule + ε·0,5`; `propensity` NaN với session nhắm theo rider, bằng `explore_p` với session explore.
- [U] κ auto: chi tiêu thực tế của lượt đánh giá nằm trong [0,85B; 1,0B].

- [U] `scope = city`: mọi ô cùng ŝ = (Σ idle)/(Σ enroute) toàn thành phố, cùng một quyết định; quy tắc H-14 và chặn ở `slack_cap` áp ở cấp thành phố; không cần bảng ô kề (T-40).
- [U] Oracle: điểm = (p1 − p0)/(v·p1) khớp `choice.request_probability` với voucher từ `pricing.voucher_dong`; v = 0 → NaN → không phát; `load_score_fn("oracle")` raise; `OracleHiddenView` chỉ được tạo khi `policy.name = threshold`; `hidden_view` bằng `legacy` với chính sách cũ, `oracle` với threshold+oracle, `none` với các lượt khác (T-40, T-41).
- [U] Runner (`tests/test_runner.py`): `run_metadata` có `budget_pilot_seed = pilot_seed(cfg)` và `budget_pilot_spent_vnd > 0` khi áp ngân sách, −1 và NaN khi không; `policy_results` có `world_seed` (T-40).

### Cấu hình (`tests/test_config.py`)
- [U] Khóa lạ trong YAML thì raise lỗi.
- [U] `--set` ghi đè đúng kiểu.
- [U] Cùng config cho cùng `config_hash`.
- [U] Hợp đồng B9 (H-29…H-33): mọi khóa mới có mặt với giá trị cũ; giá trị mới hợp lệ được nhận, giá trị sai kiểu hoặc ngoài khoảng bị từ chối (`shocks.*`, `events.venues`, chỉ tiêu CAL mới); khóa chưa cài mà đặt giá trị mới thì `engine.build_context` báo `NotImplementedError` (`tests/test_engine.py`); mã luồng `SHOCK = 8`, `ShockKind`, `WorldPart.VENUES = 4` không đổi (`test_rng.py`, `test_demand.py`).

---

## 2. Tích hợp

- [I] `test_smoke_day`: chạy 1 ngày với `default.yaml`, mọi chính sách, không lỗi; số order Completed > 0.
- [I] `test_conservation`: sessions = requested + not-requested; requested = Completed + Abandoned + Cancelled + Truncated.
- [I] `test_cooldown`: N(π) đếm order có `request_time` trong cửa sổ, kể cả order hoàn thành sau cửa sổ; order tạo sau cửa sổ không tồn tại.
- [I] `test_driver_state_consistency`: mỗi tick, số xe theo trạng thái cộng lại bằng số xe online; không xe nào vừa idle vừa có order.

---

## 2b. Hồi quy Sprint 7 (`tests/test_regression_s7.py`, G7) — `@slow`

- [I] Với `config/default.yaml` + `tests/fixtures/regression_s7_pinned.yaml` (default.yaml ghim tại 1c2eb85, cộng giá trị cũ của mọi khóa mới S7), 1 ngày của `generate` legacy, `generate` experiment, `evaluate` threshold (κ auto) và `evaluate` all_on phải trùng từng số với `tests/fixtures/regression_s7.json` (sinh tại 1c2eb85): số dòng và băm từng cột của mọi bảng `observed/`, `market/`, `hidden/`, `results/`, `meta/`, trừ cột biến động và trừ `slack_hat` được chặn ở `slack_cap` trước khi băm (T-39). Lệch thì test in tên bảng và cột lệch. Không sinh lại mốc trong S7.
- [U] `tests/fixtures/regression_s7.json` đủ 4 lượt và đủ các bảng chính (chạy trong `pytest -q`).

## 3. Nghiệm thu bắt buộc (5 kiểm thử của [report])

### A1. Đường throughput (quan trọng nhất) — `@slow`
- **Cách chạy:** `mode throughput_curve`, policy all_off, fleet cố định (`fleet_size`, `supply.shift_mode = always_on`), quét `throughput.demand_scale_grid` (16 mức 0,25…4,0), `throughput.n_seeds = 3`, **một giờ cao điểm ổn định** (`hour_profile` và `speed_factor_by_hour` hằng số tại `throughput.reference_hour`). `mean_slack` = tổng (xe rảnh × tick) / tổng (xe đi đón × tick) trên cửa sổ (T-08, T-15). Số liệu báo cáo chạy cửa sổ đủ 1 ngày; khi debug có thể rút ngắn bằng `time.window_min`.
- **Đạt khi:**
  1. `completed_per_h` tăng rồi đạt đỉnh ở mức cầu nào đó.
  2. Tại mức cầu lớn nhất, `completed_per_h ≤ 0,95 × đỉnh`, tức **có đoạn giảm**.
  3. Ở vùng giảm, `mean_slack < 0,45`, khớp ngưỡng WGC của Castillo.
  4. `mean_pickup_eta_min` tăng đơn điệu theo cầu, không có bước nhảy > 3 phút giữa hai mức liền kề.
- **Nếu không đạt:** tăng `grid_radius`, giảm `base_speed_kmh` giờ cao điểm, hoặc tăng `max_wait`. Ghi lại vào `docs/decisions.md`. **Không** giảm `max_pickup_eta_min`.

### A2. Số ngẫu nhiên chung (CRN)
- (a) Cùng chính sách, cùng seed chạy hai lần cho N, V **giống hệt** (so sánh bằng `==`).
- (b) Với 20 seed, `Var(N(π1) − N(π2))` khi dùng CRN ≤ **0,5 ×** khi dùng seed độc lập, với π1 = all_on **có ngân sách** (phát đến khi hết B mỗi kỳ) và π2 = threshold θ = 0,3 có ngân sách; cả hai cùng B (T-12).
- (c) Hai chính sách khác nhau cho cùng tập `session_id`, cùng `rider_id`, `do_cell`, `u_book` cho mỗi session.

### A3. Dao động của π_θ
- Chạy π_θ với θ = 0,35, h = 0, 5 seed; đo `n_switches_per_cell_day`.
- **Báo cáo** giá trị. Nếu trung vị > 12 lần/ô/ngày thì chạy lại với h = 0,1 và ghi kết quả so sánh. Đây là kiểm thử thông tin, không chặn mốc.

### A4. Tính đơn điệu
- Từ dữ liệu `generate` với `experiment.design = cluster_switchback`, ước lượng hiệu ứng khác biệt N theo nhóm `slack_lag_slot` (bin theo tứ phân vị). Ghi số lần đổi dấu.
- Đây là kiểm thử thông tin: kết quả đưa vào báo cáo phân tích, không chặn mốc.

### A5. Thời gian chạy
- `mode evaluate`, `default.yaml`, 1 ngày, log tối thiểu, 1 lõi: **trung vị 3 lần ≤ 30 giây**.
- **A5-HN** (H-34, từ H7.1, cấu hình quy mô Hà Nội): `evaluate` `all_on` 1 ngày, 1 tiến trình, trung vị 3 lần **≤ 60 giây** (`performance.max_seconds_per_sim_day`). Vượt thì profile và tối ưu đúng bước nặng nhất, tối đa 1 ngày công; vẫn vượt thì ghi số thật, không nới thêm.

---

## 4. Hiệu chỉnh [CAL] (mốc P3)

Chạy all_off, 5 seed, `default.yaml` (`tests/test_acceptance_core.py`, đánh dấu `slow`). Một session ở "ô dư cung" khi slack của **slot trước**, cùng ô (`slack_lag_slot`) lớn hơn 1 (H-15); không dùng slack của chính slot đó, vì nó là kết quả của các lượt đặt trong slot. Kiểm từng chỉ tiêu trong `calibration_targets`:

| Chỉ tiêu | Cách đo | Khoảng mục tiêu |
|---|---|---|
| P(đặt) không voucher | requested / sessions, all_off, session ở ô dư cung | 0,13–0,17 |
| Tăng request khi dư cung | `mean(p_request_treat) / mean(p_request_control) − 1` trên session ở ô dư cung (cột ẩn, cùng bối cảnh; H-16) | +35% … +70% |
| Tỷ lệ (ô, slot) căng | share slack < 0,35 (all_off; slack của chính (ô, slot), I = 0 thì slack = 0, H-14) | 10–35% |
| Tỷ lệ (ô, slot) dư | share slack > 1 (all_off) | 30–80% |
| Tỷ lệ xe bận lúc 6/7/8h (H-31) | giờ-xe chở khách của chuyến hoàn thành đặt trong giờ h / giờ cao nhất (như `analysis/tlc_hourly.py`) | 0,31–0,61 / 0,55–0,85 / 0,63–0,93 |
| Quãng đường TB (H-31) | mean `trip_km` của order hoàn thành trong cửa sổ | 5–8 km |
| Chuyến / tài xế / ngày (H-31) | order hoàn thành trong cửa sổ / (`fleet_size` × số ngày cửa sổ), W0 | 8–18 |

Hai dải tỷ lệ (ô, slot) căng và dư là **thiết kế kịch bản** ("có vùng căng thật"), không phải số đo từ dữ liệu thực tế; số tuyệt đối về tiền và số xe là quy ước (H-23). Bỏ chỉ tiêu giá gốc trung bình ở B9 vì giá do bảng giá quyết định (H-31). Từ B9 tới khi hiệu chỉnh xong (S8), test CAL chậm không đạt vì các chỉ tiêu mới chưa hiệu chỉnh: ghi log, không nới dải. Không dùng N(π_θ), θ\*, GTE làm mục tiêu hiệu chỉnh.

Núm chỉnh (S8, thứ tự ưu tiên ở `docs/de_xuat_tham_so_ha_noi.md` mục C): `alpha0`, `delta0` (P(đặt), uplift); `fleet_size`, `demand_scale` (phân bố slack); `shift_start_mixture` (xe bận theo giờ); `dest_decay_rings` (quãng đường). Ghi giá trị cuối vào `default.yaml` và lý do vào `docs/decisions.md`.
