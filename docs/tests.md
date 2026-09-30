# Kế hoạch kiểm thử

Chạy toàn bộ kiểm thử: `pytest -q`. Kiểm thử chậm (đánh dấu `@pytest.mark.slow`): `pytest -q -m slow`.
Mỗi mốc trong `docs/plan.md` chỉ được coi là xong khi các test của mốc đó **pass**.
Test dùng cấu hình nhỏ `tests/fixtures/tiny.yaml` (bán kính 1, fleet 10, 2 giờ mô phỏng) trừ khi ghi khác.

Ký hiệu: **[U]** unit, **[I]** tích hợp, **[A]** nghiệm thu của [report] (5 kiểm thử bắt buộc), **[CAL]** hiệu chỉnh.

---

## 1. Unit test theo module

### M1 SpaceTime (`tests/test_space.py`)
- [U] Số ô: R = 1, 2, 3 cho 7, 19, 37 ô.
- [U] Torus: mọi ô có **đúng 6** ô kề phân biệt; quan hệ kề đối xứng.
- [U] Khoảng cách torus đối xứng, bằng 0 trên đường chéo, thỏa bất đẳng thức tam giác, tối đa bằng R.
- [U] `T[a,b,h] > 0`, đối xứng theo a, b; `T[a,a,h] < T[a,b,h]` với mọi b ≠ a.
- [U] `ETA_in(I)` giảm ngặt theo I, không nhỏ hơn `eta_floor_min`, và với I = 1 nhỏ hơn T tới ô kề.
- [U] Tắt torus: ô biên có < 6 ô kề (kiểm chế độ không torus vẫn chạy được).

### M2 Demand (`tests/test_demand.py`)
- [U] Trung bình số session mỗi (ô, giờ) qua 2.000 tick khớp λ trong ±5%.
- [U] Cùng `(day, tick, cell)` cho cùng số session, bất kể chính sách.
- [U] Phân phối ô đích: tần suất theo khoảng cách giảm dần.
- [U] `max_wait` có mode ≈ 5 phút (±0,5).

### M3 Pricing / ngân sách (`tests/test_pricing.py`)
- [U] `p_s = a_f + b_f*T`; `v_s = 0,2*p_s`; `net = p − v`.
- [U] **Bất biến ngân sách:** trong mọi tick, `spent + committed + reserved ≤ B` (chạy 1 ngày, policy all_on, có ngân sách).
- [U] Rider không đặt thì reserved được nhả; order Abandoned hoặc Cancelled thì committed được nhả.
- [U] Ngân sách reset lúc 00:00 mỗi ngày.

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

### M6 / M7 Trip và hủy (`tests/test_trips_cancel.py`)
- [U] Thời điểm đón = ghép + ETA; thời điểm trả = đón + trip_time.
- [U] Tiền: `driver_pay = 0,76*gross`; `profit = net − driver_pay`.
- [U] Order Waiting quá `max_wait` thì Abandoned.
- [U] Hủy khi đi đón: xe rảnh ở ô xuất phát nếu hủy trước nửa ETA, ở ô khách nếu sau; `idle_since = t`; không ghép lại trong cùng tick.
- [U] Hazard hủy tăng theo ETA: với 10.000 order giả lập, tỷ lệ hủy ở ETA 10 phút > ở ETA 3 phút.

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
- [U] Hysteresis: với chuỗi ŝ dao động quanh θ, số lần đổi trạng thái khi h > 0 ít hơn khi h = 0.
- [U] Chính sách cũ: `cell_propensity = (1−ε)·rule + ε·0,5`; `propensity` NaN với session nhắm theo rider, bằng `explore_p` với session explore.
- [U] κ auto: chi tiêu thực tế của lượt đánh giá nằm trong [0,85B; 1,0B].

### Cấu hình (`tests/test_config.py`)
- [U] Khóa lạ trong YAML thì raise lỗi.
- [U] `--set` ghi đè đúng kiểu.
- [U] Cùng config cho cùng `config_hash`.

---

## 2. Tích hợp

- [I] `test_smoke_day`: chạy 1 ngày với `default.yaml`, mọi chính sách, không lỗi; số order Completed > 0.
- [I] `test_conservation`: sessions = requested + not-requested; requested = Completed + Abandoned + Cancelled + Truncated.
- [I] `test_cooldown`: N(π) đếm order có `request_time` trong cửa sổ, kể cả order hoàn thành sau cửa sổ; order tạo sau cửa sổ không tồn tại.
- [I] `test_driver_state_consistency`: mỗi tick, số xe theo trạng thái cộng lại bằng số xe online; không xe nào vừa idle vừa có order.

---

## 3. Nghiệm thu bắt buộc (5 kiểm thử của [report])

### A1. Đường throughput (quan trọng nhất) — `@slow`
- **Cách chạy:** `mode throughput_curve`, policy all_off, fleet cố định (`fleet_size`), quét `demand_scale ∈ {0,25; 0,5; …; 4,0}` (16 mức), 3 seed, **một giờ cao điểm ổn định** (dùng `hour_profile` hằng số).
- **Đạt khi:**
  1. `completed_per_h` tăng rồi đạt đỉnh ở mức cầu nào đó.
  2. Tại mức cầu lớn nhất, `completed_per_h ≤ 0,95 × đỉnh`, tức **có đoạn giảm**.
  3. Ở vùng giảm, `mean_slack < 0,45`, khớp ngưỡng WGC của Castillo.
  4. `mean_pickup_eta_min` tăng đơn điệu theo cầu, không có bước nhảy > 3 phút giữa hai mức liền kề.
- **Nếu không đạt:** tăng `grid_radius`, giảm `base_speed_kmh` giờ cao điểm, hoặc tăng `max_wait`. Ghi lại vào `docs/decisions.md`. **Không** giảm `max_pickup_eta_min`.

### A2. Số ngẫu nhiên chung (CRN)
- (a) Cùng chính sách, cùng seed chạy hai lần cho N, V **giống hệt** (so sánh bằng `==`).
- (b) Với 20 seed, `Var(N(π1) − N(π2))` khi dùng CRN ≤ **0,5 ×** khi dùng seed độc lập, với π1 = all_on và π2 = threshold θ = 0,3 (có ngân sách).
- (c) Hai chính sách khác nhau cho cùng tập `session_id`, cùng `rider_id`, `do_cell`, `u_book` cho mỗi session.

### A3. Dao động của π_θ
- Chạy π_θ với θ = 0,35, h = 0, 5 seed; đo `n_switches_per_cell_day`.
- **Báo cáo** giá trị. Nếu trung vị > 12 lần/ô/ngày thì chạy lại với h = 0,1 và ghi kết quả so sánh. Đây là kiểm thử thông tin, không chặn mốc.

### A4. Tính đơn điệu
- Từ dữ liệu `generate` với `experiment.design = cluster_switchback`, ước lượng hiệu ứng khác biệt N theo nhóm `slack_lag_slot` (bin theo tứ phân vị). Ghi số lần đổi dấu.
- Đây là kiểm thử thông tin: kết quả đưa vào báo cáo phân tích, không chặn mốc.

### A5. Thời gian chạy
- `mode evaluate`, `default.yaml`, 1 ngày, log tối thiểu, 1 lõi: **trung vị 3 lần ≤ 30 giây**.

---

## 4. Hiệu chỉnh [CAL] (mốc P3)

Chạy all_off và all_on, 5 seed, `default.yaml`. Kiểm từng chỉ tiêu trong `calibration_targets`:

| Chỉ tiêu | Cách đo | Khoảng mục tiêu |
|---|---|---|
| P(đặt) không voucher | requested / sessions, all_off, các slot có slack > 1 | 0,13–0,17 |
| Tăng request khi dư cung | (P_on − P_off)/P_off, slot có slack > 1 | +35% … +70% |
| Giá gốc trung bình | mean gross_fare | 17,2–21,0 USD |
| Tỷ lệ (ô, slot) căng | share slack < 0,35 (all_off) | 10–35% |
| Tỷ lệ (ô, slot) dư | share slack > 1 (all_off) | 30–80% |

Núm chỉnh theo thứ tự: `alpha0` (cho P(đặt)), `beta_price_per_usd` và `delta0` (cho uplift), `per_min_usd` (cho giá), `fleet_size` và `demand_scale` (cho phân bố slack). Ghi giá trị cuối vào `default.yaml` và lý do vào `docs/decisions.md`.
