# Tech spec — Simulator gọi xe (Supply-Aware Promotion Impact Framework)

Phiên bản: 1.0 · Ngày: 30/09/2026 · Nguồn thiết kế: `docs/Simulation_design_fix.pdf` (gọi tắt **[report]**)

Tài liệu này mô tả **chính xác cách code** simulator. Báo cáo thiết kế trả lời *làm gì, vì sao*; spec này trả lời *làm thế nào*.
Khi hai tài liệu mâu thuẫn: **spec thắng về chi tiết cài đặt, report thắng về ý đồ**. Gặp mâu thuẫn thì dừng lại hỏi, ghi vào `docs/decisions.md`, không tự chọn.

Tài liệu liên quan:
- `config/default.yaml`: mọi tham số, không hard-code số trong code.
- `docs/schema.md`: định dạng dữ liệu đầu ra.
- `docs/tests.md`: kiểm thử và tiêu chí đạt.
- `docs/plan.md`: thứ tự triển khai.

---

## 0. Mục tiêu và phạm vi

Simulator agent-based, ride-hailing solo, trên lưới ô lục giác. Nó dùng để:

1. Sinh dữ liệu quan sát (có confounding kiểm soát được) và dữ liệu thí nghiệm switchback.
2. Tính **giá trị thật** của một chính sách: N(π) là số chuyến hoàn thành (chính), V(π) là lợi nhuận (phụ).
3. Quét θ để tìm **θ\* = argmax_θ N(π_θ)** dưới cùng ngân sách B.
4. Tính GTE và độ chệch của các thiết kế thí nghiệm.

**Ngoài phạm vi:**
- đi chung (pooling);
- surge pricing;
- tài xế phản ứng theo thu nhập (có công tắc, mặc định tắt);
- nền tảng chủ động điều xe;
- học mô hình uplift. Simulator chỉ *nhận* hàm điểm τ̂ từ bên ngoài.

---

## 1. Quyết định thiết kế (ADR tóm tắt)

| ID | Quyết định | Trạng thái | Lý do / nguồn |
|---|---|---|---|
| D1 | Chỉ tiêu chính là N(π); V(π) là phụ; mọi chính sách chịu cùng ngân sách B | Accepted | Voucher 20% ≈ phần nền tảng giữ lại, nên V(π) luôn giảm [report §1] |
| D2 | θ\* = argmax_θ N(π_θ), tìm bằng quét θ; không rẽ nhánh từng (ô, slot) | Accepted | [report §1, M13] |
| D3 | π_θ hai tầng: cắt ô theo chỉ số căng cung, phát voucher cho rider theo điểm τ̂ trong ngân sách | Accepted (T-17); đổi được qua config | [report M3] |
| D4 | Chỉ số căng cung mặc định là slack = I/E (xe rảnh / xe đang đi đón) | Accepted (T-10, T-17); đổi qua `policy.threshold.indicator` | Castillo et al. 2025 |
| D5 | `max_pickup_eta` = 30 phút; tìm xe theo vành mở rộng dần | Accepted (T-17); đổi qua `matching.max_pickup_eta_min` | Giới hạn thấp làm mất WGC [report M5] |
| D6 | Lưới mặc định bán kính 3 (37 ô), torus | Accepted | [report Bảng 2]. thời gian đón tối đa (qua 3 vành) ≈ 17 phút giờ thường, ≈ 23 phút giờ cao điểm; 19 ô chỉ ≈ 11–15 phút, có thể không đủ cho WGC |
| D7 | Cung độc lập với chính sách: rời sớm theo thu nhập tắt; repositioning theo quy tắc tĩnh | Accepted | [report M8, M9] |
| D8 | Code dạng struct-of-arrays (numpy); không tạo object Python cho mỗi xe/khách trong vòng lặp nóng | Accepted | Mục tiêu ≤ 30 giây / ngày mô phỏng |
| D9 | CRN: mọi phép ngẫu nhiên lấy từ luồng được khóa theo định danh ổn định (session, order, driver, cell-slot) | Accepted | [report M13] |
| D10 | Thí nghiệm (switchback, A/B) và lượt GTE không áp ngân sách | Accepted | [report M3, M13] |
| D11 | Cụm cho switchback: cụm "7 ô" xây theo quy tắc hoa lục giác; trên torus 37 ô cụm có kích thước 3–7 | Accepted | Không chia đều được vì 37 là số nguyên tố |
| D12 | κ (ngưỡng điểm tầng rider) hiệu chỉnh bằng 1 lượt pilot để chi tiêu kỳ vọng ≈ B; kèm dừng cứng khi chạm B | Accepted | [report M3] |

---

## 2. Quy ước chung

- **Đơn vị:** thời gian nội bộ tính bằng **giây**, kiểu `float64` (thời điểm) hoặc `int64` (chỉ số tick); tiền tính bằng **USD**; quãng đường tính bằng **km**. ETA công bố cho rider đổi sang phút.
- **Chỉ số thời gian:**
  - `tick = t // tick_s`;
  - `slot = t // (slot_min*60)`, tính từ đầu lượt chạy;
  - `day = t // 86400`;
  - `hour = (t % 86400) // 3600`;
  - `slot_of_day = (t % 86400) // (slot_min*60)`, từ 0 đến 95.
- **ID ô:** số nguyên 0..N-1, sắp theo `(q, r)` tăng dần. Bảng `cell_q`, `cell_r` lưu tọa độ trục.
- **ID ổn định cho CRN:**
  - `session_id` là số nguyên 64-bit tạo từ `(day, tick_of_day, cell, k)`, với `k` là thứ tự session trong (ô, tick). Công thức: `((day*ticks_per_day + tick_of_day)*N + cell)*1000 + k`, với `ticks_per_day = 86400 // tick_s` (T-06), trong đó `k < 1000`; nếu vượt thì raise lỗi.
  - `order_id = session_id`, vì mỗi session có tối đa 1 order.
  - `driver_id` là 0..fleet_size-1.
- **Chỉ đọc quá khứ:** quyết định trong slot k chỉ dùng snapshot đã công bố của các slot < k.

---

## 3. Cấu trúc code

```
sim/
  config.py        # load YAML -> dataclass lồng nhau; --set override; config_hash
  rng.py           # luồng ngẫu nhiên có khóa (§5)
  space.py         # M1: lưới, torus, khoảng cách, T[a,b,h], ETA
  population.py    # sinh rider, trọng số ô, đội xe (theo world_seed)
  state.py         # SoA: DriverState, OrderBuffer, SessionBuffer, bộ đếm, Clock, SimContext
  budget.py        # BudgetLedger (re-export từ state.py, L11)
  demand.py        # M2
  pricing.py       # M3: giá + điều phối chế độ voucher
  policies/
    base.py        # giao diện Policy (§6)
    legacy.py
    experiment.py  # đọc assignment từ M10
    threshold.py   # π_θ
    fixed.py       # all_on / all_off
    scores.py      # hàm điểm: random, heuristic_low_freq, loader "module:function"
  choice.py        # M4
  matching.py      # M5
  trips.py         # M6
  cancel.py        # M7
  supply.py        # M8
  reposition.py    # M9
  experiment.py    # M10: gán (cụm, block)
  monitor.py       # M11
  logger.py        # M12: ghi Parquet theo docs/schema.md
  engine.py        # vòng lặp tick (§4.0)
  runner.py        # M13: các chế độ chạy (§7)
  cli.py           # python -m sim ...
tests/             # theo docs/tests.md
```

---

## 4. Đặc tả từng module

### 4.0 Engine: vòng lặp một tick

Thứ tự bắt buộc, khớp Hình 2 của [report]:

```
for tick in range(n_ticks_total):          # gồm warm-up + cửa sổ + cool-down
    t = tick * tick_s
    1. trips.advance(t)          # M6: xe đến điểm đón / trả; M9: xe điều chuyển tới nơi
    2. supply.update(t)          # M8: vào ca, hết ca (chỉ rời khi rảnh)
    3. cancel.expire_waiting(t)  # M7: đơn chưa ghép quá max_wait -> Abandoned
    4. demand.spawn(t)           # M2: tạo session mới (dừng sau cửa sổ đánh giá)
    5. pricing.quote(t)          # M10 + M3: nhánh, giá, voucher (giữ ngân sách), ETA báo
    6. choice.decide(t)          # M4: đặt xe -> tạo Order Waiting; không đặt -> nhả ngân sách
    7. matching.match(t)         # M5 + M6: ghép theo FIFO, lập lịch đón
    8. cancel.en_route(t)        # M7: hủy trong lúc đi đón (§4.7)
    9. reposition.step(t)        # M9
    10. monitor.accumulate(t)    # M11; nếu hết slot -> publish snapshot; M12 ghi log
```

- **Cửa sổ đánh giá** là `[warmup_min, warmup_min + window_min)` phút, với `window_min = time.window_min` nếu đặt, ngược lại `days_per_run*1440` (T-05). Session chỉ được sinh đến hết cửa sổ.
- **Cool-down:** sau cửa sổ, tiếp tục vòng lặp (bỏ qua bước 4) đến khi mọi order được tạo trong cửa sổ đã kết thúc, hoặc chạm `cooldown_max_min`. Order chưa kết thúc khi chạm giới hạn được ghi `status = Truncated`.
- **Đánh giá:** N(π) và V(π) chỉ tính các order có `request_time` nằm trong cửa sổ đánh giá [report §3.2].

### 4.1 M1 SpaceTime (`space.py`)

**Lưới lục giác bán kính R**
- Tập ô: `{(q, r): max(|q|, |r|, |q+r|) ≤ R}`, gồm N = 3R²+3R+1 ô.
- 6 hướng lân cận: `(1,0) (1,-1) (0,-1) (-1,0) (-1,1) (0,1)`.

**Torus** (khi `torus: true`)
- Vector tịnh tiến: `a = (2R+1, -R)`, `b = (R, R+1)`. Đã kiểm với R = 2, 3, 4: mọi ô có đúng 6 ô kề phân biệt.
- `wrap(c)`: thử `c - i*a - j*b` với i, j ∈ {-1, 0, 1} và trả về ảnh nằm trong tập ô.
- Khoảng cách torus: `dist(x, y) = min_{i,j∈{-1,0,1}} hexdist(x, y + i*a + j*b)`, với `hexdist = (|dq| + |dr| + |dq+dr|)/2`.
- Tính trước ma trận `D[N,N]` kiểu int.

**Hình học**
- Diện tích ô: `A = (3√3/2) * edge_km²`.
- Khoảng cách tâm hai ô kề: `s = √3 * edge_km`.

**Ma trận thời gian `T[a, b, h]`** (phút), với `v_h = base_speed_kmh * speed_factor_by_hour[h]`:
- a ≠ b: `T = detour_factor * D[a,b] * s / v_h * 60`.
- a = b (chuyến trong ô): `T = detour_factor * intra_cell_dist_factor * sqrt(A) / v_h * 60`.
- Kiểu `float32[N, N, 24]`, tính trước một lần.

**ETA đón khi trong ô khách có I ≥ 1 xe rảnh** (phút) [report (4)]:
```
ETA_in(I, h) = max(eta_floor_min, detour_factor * nn_const * (A / I)**eta_gamma / v_h * 60)
```
Khi `eta_gamma = 0.5`, đây là khoảng cách kỳ vọng tới xe gần nhất trong trường điểm Poisson.

**ETA khi xe ở ô khác:** `T[ô_xe, ô_khách, h]`.

**Hàm ETA báo giá** `quote_eta(cell, h, idle_count)`: dùng cùng quy tắc tìm xe như M5 (§4.5), nhưng không giữ xe. Nếu không có xe trong giới hạn thì trả `max_pickup_eta_min` và gắn cờ `no_supply = True`.

### 4.2 M2 DemandGenerator (`demand.py`)

**Trọng số ô:** `w_z ~ LogNormal(0, cell_weight_sigma)`, chuẩn hóa để trung bình bằng 1. Sinh theo `world_seed`, cố định cho mọi lượt chạy.

**Số session mỗi (ô, tick):**
```
λ_z(t) = base_sessions_per_cell_h * demand_scale * w_z * hour_profile[hour(t)] * tick_s/3600
n_z(t) ~ Poisson(λ_z(t))        # luồng DEMAND khóa (day, tick_of_day, cell)
```

**Với mỗi session** (luồng SESSION khóa `session_id`):
- **Chọn rider:** với xác suất `home_cell_share`, chọn trong các rider có `home_cell = z`; ngược lại chọn trong toàn bộ rider. Trong nhóm được chọn, xác suất tỷ lệ với `x_freq`. Nếu ô không có rider nào thì chọn trong toàn bộ.
- **Chọn ô đích:** `P(d | o) ∝ w_d * exp(-D[o,d] / dest_decay_rings)`.
- **Rút sẵn các số ngẫu nhiên**, lưu vào SessionBuffer:
  - `u_book`: Uniform, dùng cho quyết định đặt xe (M4);
  - `u_target`, `u_explore`, `u_explore_arm`: Uniform, dùng cho chính sách cũ (M3);
  - `trip_noise`: LogNormal(0, trip_time_noise_sigma);
  - `e_cancel`: Exponential(1), ngưỡng hazard tích lũy cho hủy (M7);
  - `u_score`: Uniform, dùng cho `score_fn = random` (T-07).

  Thứ tự rút là cố định (rider, đích, `u_book`, `u_target`, `u_explore`, `u_explore_arm`, `trip_noise`, `e_cancel`, `u_score`) và **luôn rút đủ**, bất kể chính sách. Chính sách không được tự rút từ luồng SESSION; các số này đi vào `SessionBatch` (§6) và được ghi ở `hidden/` (T-11).

**Sinh rider** (`population.py`, theo `world_seed`):
- `home_cell`: rút theo phân phối `w_z / Σw`.
- `x_freq ~ Gamma(shape, 1)`.
- `x_tenure ~ Uniform(0, max)`.
- `x_segment ~ Categorical(x_segment_probs)`.
- `u_latent ~ N(0, 1)`.
- Hệ số hành vi, với `zf` là x_freq chuẩn hóa z-score:
  ```
  alpha_i      = alpha0 + alpha_freq*zf + alpha_u*u_latent + N(0, alpha_noise_sd)
  beta_price_i = -beta_price_per_usd * beta_price_seg_mult[seg] * exp(N(0, beta_price_noise_sd))
  beta_eta_i   = -beta_eta_per_min * exp(N(0, beta_eta_noise_sd))
  delta_i      = delta0 + delta_u*u_latent + delta_seg[seg] + N(0, delta_noise_sd)
  max_wait_i   ~ LogNormal(mu, max_wait_sigma), mu = ln(max_wait_mode_min) + max_wait_sigma²   # mode = 5 phút
  ```

### 4.3 M3 PricingAndPromotion (`pricing.py`, `policies/`)

**Giá gốc:** `p_s = base_fare_usd + per_min_usd * T[pu, do, h]`.

**Voucher nếu được phát:** `v_s = pct_of_fare * p_s`, chặn trên bởi `max_usd` nếu có. Giá thực trả `net = p_s - v_s`.

**Sổ ngân sách `BudgetLedger`** (khi `budget.enforce` bật):
- `reserved`: giữ khi phát voucher ở bước 5; nhả ở bước 6 nếu rider không đặt.
- `committed`: chuyển từ reserved khi rider đặt; nhả khi order Abandoned hoặc Cancelled.
- `spent`: chuyển từ committed khi order Completed.
- Chỉ phát voucher khi `spent + committed + reserved + v_s ≤ B`. Nếu không đủ thì session ghi `budget_blocked = True`.
- Bất biến: `spent + committed + reserved ≤ B` tại mọi thời điểm.
- **Kỳ ngân sách** (T-03): dài `P = min(1440, window_min)` phút, neo theo cửa sổ đánh giá: kỳ d là `[window_start + d*P, window_start + (d+1)*P)`. Mỗi kỳ có bộ đếm `spent/committed/reserved` riêng và cùng mức B. Một reservation thuộc kỳ của `open_time` session và giữ nguyên kỳ đó khi order kết thúc trong cool-down; bất biến giữ theo từng kỳ. Warm-up là kỳ −1 với ngân sách `B * warmup_min / P`, để trạng thái đầu cửa sổ phản ánh chính sách; chi tiêu warm-up không tính vào đánh giá.
- Ledger khóa theo `session_id`, tiền tính bằng **cent nguyên** để bất biến chính xác.

**Tính B khi `mode = fraction_of_all_on`:**
1. Chạy pilot `all_on` với seed `pilot_seed_offset`, không áp ngân sách.
2. `B = fraction * chi tiêu voucher trung bình mỗi kỳ ngân sách` của lượt pilot, tính trên các kỳ trong cửa sổ (bỏ warm-up).

B được tính một lần cho mỗi cấu hình thế giới và dùng chung cho mọi chính sách, θ và seed.

**Mỗi session ghi:** `assign_mechanism` ∈ {legacy_rule, legacy_eps, explore, experiment, threshold, fixed}, `propensity` (quan sát được, nếu biết), `cell_propensity`, `promo_on_cell`, `arm` (0/1), `score` (nếu có).

**Các chế độ voucher** gồm chính sách, thí nghiệm và cố định; giao diện chung ở §6.

### 4.4 M4 RiderChoice (`choice.py`) [report (5)]

```
eta_q = ETA báo (phút)
logit = alpha_i + beta_price_i * (p_s - v_s) + beta_eta_i * eta_q + delta_i * 1[v_s > 0]
P     = 1 / (1 + exp(-logit))
book  = u_book < P
```

- **Ground truth** (chỉ ghi vào bảng ẩn): tính cùng bối cảnh
  - `p_request_treat` với `v = pct*p_s`;
  - `p_request_control` với `v = 0`;
  - `direct_request_effect_fixed_market = treat - control`.
- Nếu `no_supply = True`, rider vẫn quyết định theo `eta_q = max_pickup_eta_min`.

### 4.5 M5 Matching (`matching.py`) [report M5]

Duyệt các order `Waiting` theo `request_time` tăng dần (FIFO). Với mỗi order ở ô khách z, giờ h:

1. **Nếu `idle[z] ≥ 1`:**
   - ETA = `ETA_in(idle[z], h)`, tính **trước** khi trừ xe.
   - Chọn xe trong ô z có `idle_since` nhỏ nhất. Mọi xe trong ô có cùng ETA; tiêu chí này chỉ để phá hòa.
2. **Nếu ô trống:** xét lần lượt vành k = 1, 2, … theo `D[z, ·] = k`, đến khi `min T[·, z, h] > max_pickup_eta_min` hoặc vượt `max_ring`.
   - Ở vành gần nhất còn xe rảnh, chọn ô c có `T[c, z, h]` nhỏ nhất; nếu hòa thì lấy `cell_id` nhỏ hơn.
   - Trong ô c, chọn xe có `idle_since` nhỏ nhất.
   - ETA = `T[c, z, h]`.
3. **Nếu `ETA > max_pickup_eta_min`** hoặc không có xe: order tiếp tục chờ đến tick sau.
4. **Khi ghép:** xe chuyển sang `en_route`, `idle[c] -= 1`; order chuyển sang `Matched`, ghi `matched_time`, `pickup_eta_min`, `driver_id`, `driver_origin_cell = c`.

Chỉ xe `idle` **và** còn trong ca mới được ghép.

**Hiệu năng:** duy trì mảng `idle_count[N]` và, cho mỗi ô, danh sách xe rảnh sắp theo `idle_since` (deque hoặc heap). Không quét toàn bộ đội xe cho mỗi order.

### 4.6 M6 TripExecution (`trips.py`)

- **Khi ghép:**
  - `pickup_at = t + pickup_eta*60`;
  - `trip_dur = T[z, do, h_pickup] * trip_noise` (phút);
  - `dropoff_at = pickup_at + trip_dur*60`.
- **Ở bước 1 mỗi tick:**
  - xe có `pickup_at ≤ t` chuyển `en_route → on_trip`, order chuyển `OnTrip`;
  - xe có `dropoff_at ≤ t` chuyển `on_trip → idle` tại ô trả, `idle_since = dropoff_at`; order chuyển `Completed`; ngân sách chuyển committed → spent.
- **Thanh toán lúc Completed:**
  - `gross_fare = p_s`;
  - `voucher_value = v_s`;
  - `net_fare = p_s - v_s`;
  - `driver_pay = (1 - commission_rate) * gross_fare`;
  - `platform_profit = net_fare - driver_pay`.

### 4.7 M7 Cancellation (`cancel.py`)

- **Bỏ chờ (bước 3):** order `Waiting` có `t - request_time ≥ max_wait_i*60` chuyển sang `Abandoned`; nhả ngân sách.
- **Hủy trong lúc đi đón (bước 8)**, dùng hazard tích lũy để giữ CRN:
  ```
  h_per_min = base_per_min + slope_per_min2 * max(0, pickup_eta_min - eta_free_min)
  H(t)      = h_per_min * (t - matched_time)/60
  cancel khi H(t) ≥ e_cancel  (và xe chưa tới điểm đón)
  ```
  Khi hủy:
  - order chuyển `Cancelled`, `cancel_reason = "rider_en_route"`; nhả ngân sách;
  - xe chuyển `idle` **tại chỗ đang đứng**: nếu `(t - matched_time) < pickup_eta/2` thì ở `driver_origin_cell`, ngược lại ở ô khách;
  - `idle_since = t`; xe không được ghép lại trong cùng tick.
- `e_cancel` rút sẵn theo session, nên cùng một session có cùng ngưỡng hủy ở mọi chính sách.

### 4.8 M8 SupplyModel (`supply.py`)

Mỗi tài xế sinh một lần theo `world_seed`:
- **Ca làm:** chọn thành phần hỗn hợp theo trọng số, rồi `shift_start ~ Uniform(from, to)` (giờ).
- **Độ dài ca:** `len ~ N(mean, sd)`, cắt trong `clip`.
- **Ô xuất phát:** rút theo `w_z`.
- **Ca làm tuần hoàn** (T-02): tài xế trong ca khi `((t/3600 − shift_start) mod 24) < shift_len`; mỗi ngày dùng cùng lịch ca (ghi rõ trong log metadata). Lúc t = 0, xe nào đang trong ca theo quy tắc này thì khởi tạo `idle` tại ô xuất phát với `shift_end = shift_start + shift_len − 24` (giờ), để không có khởi động lạnh.
- **`shift_mode`** (T-08): `schedule` là mặc định; `always_on` cho mọi xe online suốt lượt chạy tại ô xuất phát, chỉ dùng cho `throughput_curve`.
- **Vào ca:** chuyển `offline → idle` tại ô xuất phát.
- **Hết ca:** chỉ rời khi đang `idle`; nếu đang bận thì rời ngay sau khi trả khách.
- **`early_exit_enabled = false`:** bỏ qua `reservation_wage` hoàn toàn. Nếu bật: xe rảnh ở thời điểm ≥ 2 giờ vào ca mà `earnings_today / giờ_đã_làm < reservation_wage` thì rời. Chỉ dùng cho phân tích độ nhạy.

### 4.9 M9 Repositioning (`reposition.py`)

- **`mode = stay`:** không làm gì.
- **`mode = static_weights`:** xe `idle` có `t - idle_since ≥ max_idle_min` sẽ chuyển sang một ô kề.
  - Ô kề được rút theo trọng số **tĩnh** `w_z`. **Không dùng** cầu hay chỉ số của slot hiện tại.
  - Luồng ngẫu nhiên khóa `(driver_id, reposition_count)`.
  - Trạng thái chuyển `repositioning`, tới nơi sau `T[c, c', h]`; khi tới thì `idle`, `idle_since = t_tới`.
  - Xe đang repositioning không nhận đơn.

### 4.10 M10 ExperimentDesigner (`experiment.py`)

**Cụm ô** (`cluster_level`):
- `1`: mỗi ô là một cụm.
- `all`: một cụm duy nhất, tức switchback toàn hệ.
- `7`:
  - tâm cụm là các ô có `(q + 5r) mod 7 == 0`. Trên lưới vô hạn, mỗi ô cách đúng một tâm ≤ 1; đã kiểm.
  - mỗi ô gán vào tâm gần nhất theo khoảng cách torus; hòa thì lấy `cell_id` nhỏ.
  - kích thước cụm với R = 3 là [3, 3, 4, 6, 7, 7, 7].

**Block:** `block = floor(t / (block_min*60))`, tính từ **đầu lượt chạy** (T-15), nên warm-up cũng có block không âm và `-1` chỉ dành cho lượt không thí nghiệm. Với `warmup_min` là bội của `block_min`, cửa sổ bắt đầu đúng biên block.

**Gán trạng thái:**
- `cluster_switchback`: `on(cluster, block) = Uniform < p_on`, luồng CELLSLOT khóa `(cluster_level, cluster_id, block)`.
- `global_switchback`: như trên với `cluster_level = all`.
- `rider_ab`: `arm(rider) = Uniform < p_on`, khóa `rider_id`, cố định cả lượt chạy. Mọi ô bật; rider arm = 1 nhận voucher.

**Trong ô "on" khi thí nghiệm:** mọi session được phát voucher. Không áp ngân sách (`budget_enforce: false`). Propensity cấp ô bằng `p_on`.

**Burn-in:** snapshot và session ghi `in_burnin = True` nếu nằm trong `burnin_min` phút đầu block. Simulator vẫn chạy bình thường; cờ này để bước phân tích loại bỏ.

### 4.11 M11 MarketMonitor (`monitor.py`)

Trong mỗi slot, sau bước 9 của **mỗi tick**, cộng dồn cho từng ô z:
- `I_z`: số xe `idle` trong ô z.
- `E_z`: số xe `en_route` có **ô khách** = z.
- `O_z`: số xe `on_trip` có ô đón = z.
- `W_z`: số order `Waiting` ở ô z.

Cuối slot, lấy trung bình theo số tick để có `I, E, O, W`, rồi tính:
- `slack = I / E`; nếu E = 0 thì `+inf` [Castillo et al. 2025].
- `utilization = (E + O) / (I + E + O)`; nếu mẫu số = 0 thì NaN. Xe `repositioning` và `offline` không tính (T-09).
- Đếm trong slot theo **thời điểm sự kiện** và **ô đón** (T-15): `n_sessions`, `n_offers`, `n_requests` theo `open_time`; `n_matched` và `mean_pickup_eta_min` theo `matched_time`; `n_abandoned`, `n_cancelled` theo thời điểm hủy; `n_completed`, `voucher_spent_usd` theo `dropoff_time`.
- Giá trị trễ để làm feature: `slack_lag_slot` (slot k-1) và `slack_lag_day` (slot k-96; NaN nếu chưa có).

Snapshot của slot k được **công bố** sau khi slot k kết thúc. Chính sách ở slot k+1 chỉ thấy các snapshot ≤ k. Cài đặt như một hàng đợi, và có assert kiểm tra thứ tự này.

### 4.12 M12 Logger (`logger.py`)

- Ghi theo đúng `docs/schema.md`.
- Tách thư mục `observed/`, `hidden/`, `market/`, `results/`, `meta/`.
- Buffer trong RAM, flush theo lô.
- Kết thúc lượt chạy: ghi `run_metadata`, gồm config đầy đủ, `config_hash`, `git_sha` và thời gian chạy.

### 4.13 M13 Runner (`runner.py`): xem §7

---

## 5. Ngẫu nhiên và CRN (`rng.py`)

Mọi phép rút ngẫu nhiên đi qua hàm:

```python
def rng_for(stream: Stream, *key: int) -> np.random.Generator:
    return np.random.Generator(np.random.Philox(key=_hash64(run_seed, stream.value, *key)))
```

| Stream | Khóa | Dùng cho |
|---|---|---|
| WORLD | `(world_seed, …)` | trọng số ô, rider, tài xế. **Không** phụ thuộc `run_seed` |
| DEMAND | `(day, tick_of_day, cell)` | số session Poisson |
| SESSION | `(session_id)` | rider, ô đích, `u_book`, `u_target`, `u_explore`, `u_explore_arm`, `trip_noise`, `e_cancel`, `u_score` (thứ tự cố định, §4.2) |
| CELLSLOT | `(kind, cell_or_cluster, slot_or_block)` | ε của chính sách cũ, switchback |
| RIDER | `(rider_id)` | arm của A/B theo rider |
| DRIVER | `(driver_id, counter)` | repositioning |

**Yêu cầu:**
- Không dùng `np.random.*` toàn cục và không dùng `random` của Python.
- Thay đổi chính sách không được làm đổi bất kỳ số ngẫu nhiên nào của một session. Kiểm bởi test T2 trong `docs/tests.md`.
- Nếu tạo Generator cho từng session quá chậm, được phép rút theo lô bằng `rng_for(SESSION_BATCH, day, tick_of_day, cell)` rồi phân phát theo `k`. Kết quả phải giống nhau giữa các chính sách.

---

## 6. Giao diện chính sách (`policies/base.py`)

```python
class Policy(Protocol):
    def cell_state(self, slot: int, snapshots: SnapshotView) -> CellDecision:
        """Gọi đầu mỗi slot. Trả về promo_on[N] (bool), cell_propensity[N] (float|NaN), mechanism[N]."""
    def offer(self, sessions: SessionBatch, cell_dec: CellDecision, ledger: BudgetLedger) -> OfferDecision:
        """Gọi ở bước 5. Trả về offer[n] (bool), propensity[n] (float|NaN), mechanism[n], score[n]."""
```

`SnapshotView` chỉ trả về snapshot đã công bố. `SessionBatch` chỉ chứa **cột quan sát được**: `session_id`, `rider_id`, `x_freq`, `x_tenure`, `x_segment`, ô, giờ, giá, ETA báo, cùng các số rút sẵn dành cho chính sách `u_target`, `u_explore`, `u_explore_arm`, `u_score` (T-07). **Không** có `u_latent`, alpha, beta, delta, hay max_wait. Chính sách không được gọi `rng_for(SESSION, …)`.

Ngân sách được áp ở lớp voucher trong `pricing.py` (L12): lớp này gọi `cell_state` khi đổi slot, gọi `offer`, rồi giữ ngân sách theo thứ tự `session_id` cho mọi chính sách; `offer` vẫn nhận `ledger` chỉ để đọc số dư. Riêng `LegacyPolicy` được dùng `u_latent` để tạo confounding, qua một view riêng `LegacyHiddenView`, và kết quả propensity thật chỉ ghi vào bảng ẩn.

**LegacyPolicy** [report M3]:
- **Cấp ô:** `rule_on = slack_lag_slot ≥ slack_on`. Với xác suất ε (luồng CELLSLOT), thay bằng coin(`epsilon_p_on`).
  - `cell_propensity = (1-ε)*rule_on + ε*epsilon_p_on`.
  - `mechanism` = legacy_rule hoặc legacy_eps.
- **Cấp rider, trong ô on:** `p_target = σ(g0 + g_freq*zf + g_u*u_latent)`; offer nếu `u_target < p_target`.
  - `propensity` quan sát = NaN (không biết);
  - `propensity_true = p_target`, chỉ ghi bảng ẩn.
- **Explore:** nếu `u_explore < explore_frac` thì session thuộc lát explore, bất kể trạng thái ô. Offer nếu `u_explore_arm < explore_p`; `propensity = explore_p`; `mechanism = explore`.
- Mọi offer chịu ngân sách. Nếu bị chặn, ghi `budget_blocked`; propensity khi đó không còn hợp lệ.

**ThresholdPolicy π_θ** [report M3]:
- **Tầng ô:**
  - dự báo ŝ: `persistence` dùng `slack_lag_slot`; `ar` dùng `ar_weights · [slack_lag_slot, slack_lag_day]`, trong đó inf được thay bằng `slack_cap`.
  - `promo_on = not (ŝ < θ)`.
  - Nếu `hysteresis_h > 0`: ô đang off chỉ bật lại khi `ŝ > θ + h`.
  - θ = 0 nghĩa là không cắt ô nào.
- **Tầng rider:**
  - `score = score_fn(SessionBatch, ŝ)`;
  - offer nếu `promo_on[cell]` **và** `score ≥ κ` **và** ngân sách còn đủ.
- **Hàm điểm có sẵn:**
  - `random`: trả về `u_score` đã rút sẵn (T-07);
  - `heuristic_low_freq`: `-x_freq`;
  - chuỗi `"module:function"`: import động, chữ ký `f(batch, s_hat) -> np.ndarray[float]`.
- **κ = auto:**
  1. Chạy pilot với κ = -∞, **không áp ngân sách** nhưng vẫn cắt ô theo θ.
  2. Ghi `(score, voucher_spent_session)` cho mọi session được offer.
  3. Sắp giảm theo score; κ là score nhỏ nhất sao cho tổng chi tiêu ≤ B.
  4. Pilot dùng seed `pilot_seed_offset + θ_index`. Ghi κ vào `run_metadata`.

**ExperimentPolicy:** đọc assignment từ M10. **FixedPolicy:** `all_on` hoặc `all_off`, không áp ngân sách khi dùng cho GTE.

**Các chính sách so sánh dưới cùng B** [report M3]:
- `random` (score = random);
- τ̂(x) (score_fn không dùng ŝ);
- τ̂(x, s);
- π_θ, tức τ̂(x, s) cộng tầng ô.

---

## 7. Chế độ chạy (`runner.py`, `cli.py`)

```
python -m sim run --mode <mode> --config config/default.yaml [--set a.b=c ...] [--out runs/<name>]
```

| Mode | Làm gì | Ghi |
|---|---|---|
| `generate` | chạy `generate.days` ngày liên tục với `policy.name` (legacy hoặc experiment) | observed, hidden, market, meta |
| `evaluate` | 1 chính sách × `n_seeds` | results, meta (chỉ tóm tắt) |
| `sweep_theta` | mỗi θ trong `theta_grid` × `n_seeds`, cùng B | results; bảng `theta_sweep` |
| `gte` | all_on và all_off × `n_seeds`, không ngân sách | results |
| `calibrate_budget` | pilot all_on để tính B | meta |
| `throughput_curve` | quét `throughput.demand_scale_grid` × `throughput.n_seeds`, all_off, `supply.shift_mode = always_on` (mọi xe online suốt lượt); `hour_profile` và `speed_factor_by_hour` đặt hằng số bằng giá trị tại `throughput.reference_hour`. Đo trên toàn cửa sổ sau warm-up: `completed_per_h = N_completed / giờ cửa sổ`; `mean_slack` = tổng (xe rảnh × tick) / tổng (xe đi đón × tick); `abandon_rate`, `cancel_rate` chia cho `n_requests` (T-08, T-15) | results (bảng A1) |

- `evaluate`, `sweep_theta` và `gte` mặc định **không** ghi bảng session hay order, để nhanh. Bật bằng `--log-level full`.
- Chạy song song các seed bằng `multiprocessing`, `runner.n_procs` tiến trình (null = số lõi). Mỗi tiến trình một seed. Windows khởi động tiến trình con bằng spawn, nên engine và hàm điểm được truyền dạng `"module:function"` và phải import được trong tiến trình con.

---

## 8. Hiệu năng

- Mục tiêu: ≤ 30 giây cho 1 ngày mô phỏng với `default.yaml`, chế độ `evaluate`, log tối thiểu, 1 lõi CPU.
- Trạng thái xe lưu trong mảng numpy: `status: int8`, `cell: int16`, `busy_until: float64`, `idle_since: float64`, `order: int64`, `shift_start/end: float64`, `earnings: float64`.
- Order và session lưu trong buffer cấp phát trước, tăng gấp đôi khi đầy.
- Vòng lặp Python chỉ được chạy trên **số order đang chờ trong tick** và **số session của tick**. Không được lặp trên toàn bộ đội xe mỗi tick; dùng chỉ mục theo `busy_until` (heap) cho bước 1.
- Có `--profile` để in thời gian theo bước.
- Nếu vượt 30 giây thì tối ưu theo thứ tự: hàng đợi sự kiện, vector hóa M2/M4, rồi `numba` (tùy chọn, phải có fallback thuần numpy).

---

## 9. Cấu hình

- `config.py` đọc YAML thành dataclass lồng nhau, **kiểm tra khóa lạ** (raise lỗi) và kiểm tra kiểu cùng khoảng giá trị cơ bản.
- `--set policy.threshold.theta=0.4` ghi đè; giá trị parse theo YAML.
- `config_hash = sha1(json.dumps(config, sort_keys=True))[:12]`, ghi vào mọi output.
- Khóa thêm ngày 30/09 (T-18): `time.window_min`, `supply.shift_mode`, `throughput.demand_scale_grid`, `throughput.n_seeds`, `throughput.reference_hour`, `runner.n_procs`. Ý nghĩa ghi trong `default.yaml`.
- Ràng buộc thời gian thêm (H-01, H-02): `warmup_min` là bội của `experiment.block_min`; `window_min` ≤ 1440 hoặc là bội của 1440.
- Độ dài cửa sổ đánh giá và kỳ ngân sách lấy qua `config.eval_window_min(cfg)` và `config.budget_period_min(cfg)` (H-03); không module nào tự đọc `window_min` hay `days_per_run` để tính.

---

## 10. Bản NYC (làm sau P8 nếu còn thời gian, T-14)

Chỉ cần đạt hợp đồng dữ liệu; phần lõi giữ nguyên. Nhóm dữ liệu (Tình) cung cấp các file dưới đây cùng hai file bổ sung: `nyc/neighbors.parquet` (`cell_id, neighbor_id`) và `nyc/clusters.parquet` (`cell_id, cluster_id`, cụm ~7 ô). Pipeline dữ liệu nằm ngoài `sim/` và được dùng `h3`. `demand_rate` gộp theo giờ (trung bình các ngày trong tuần); simulator không có chiều `dow`.

| File | Cột | Ghi chú |
|---|---|---|
| `nyc/cells.parquet` | `cell_id, h3, area_km2, lat, lng, is_buffer` | H3 res 8, có vành đệm |
| `nyc/demand_rate.parquet` | `cell_id, hour, dow, sessions_per_h` | đã chia theo P(đặt) nếu từ request |
| `nyc/speed.parquet` | `hour, speed_kmh` | từ `trip_miles/trip_time` [report §3.1] |
| `nyc/zone_pair_time.parquet` | `pu_zone, do_zone, hour, median_trip_min` | chỉ dùng cho cặp ô xa |
| `nyc/cell_zone.parquet` | `cell_id, zone_id, weight` | trọng số diện tích giao |

**Luật `T[a,b,h]` cho NYC:**
- nếu `D[a,b] ≤ space.nyc_near_rings` (mặc định 2) hoặc a, b cùng zone thì `detour * haversine / speed_h`;
- ngược lại dùng `median_trip_min` của cặp zone.

Ô `is_buffer` vẫn được mô phỏng nhưng bị loại khỏi N(π) và V(π). Lấy mẫu 5–10% cầu và đội xe theo cùng tỷ lệ.

---

## 11. Câu hỏi mở (không tự quyết trong code)

Các câu hỏi Q1–Q16 đã chốt ngày 30/09/2026, xem `docs/decisions.md` (T-01…T-18). Còn lại:

1. D3, D4, D5, mức B (`fraction = 0.3`) và `explore_frac` đã chốt theo YAML (T-17); vẫn đổi được bằng config mà không sửa code.
2. Chính sách cũ **có** áp ngân sách B, để dữ liệu quan sát giống thực tế.
3. Mọi giá trị gắn `[assume]` trong YAML sẽ được hiệu chỉnh ở mốc P3. Kết quả hiệu chỉnh ghi vào `docs/decisions.md`.
4. Câu hỏi mới: ghi vào `docs/decisions.md` mục "Câu hỏi mở" và dừng lại hỏi người.
