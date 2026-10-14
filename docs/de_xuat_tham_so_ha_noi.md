# Đề xuất tham số theo thị trường Hà Nội (bản cuối)

Ngày: 14/10/2026 · Người soạn: Hoàng; Tình rà soát và bổ sung chiều 14/10 (mục B2 đội xe, B3 `n_riders`, B4 lợi nhuận, B5 sân vận động, B7, B8, C thứ tự ưu tiên, E thời gian chạy và dự đoán ghi trước) · Trạng thái: **bản cuối, hai người duyệt trong PR B9**. File này là đầu vào để sửa `docs/ke_hoach_sua_v3.md` và `docs/phan_cong_v3.md`.

**Bối cảnh:** mentor nhận xét thành phố và ô hiện tại hơi nhỏ, gợi ý ô cỡ một phường trung tâm. Nhóm chọn ô H3 độ phân giải 7 và quy mô nội thành Hà Nội. Đây là bản cuối của đề tài, nên mọi tham số đổi **một lần**, trước khi hiệu chỉnh (S8) và sinh dữ liệu.

**Nguyên tắc:**
- Dùng số liệu thật ở mọi chỗ tìm được nguồn.
- Chỗ không có số liệu Hà Nội thì suy từ số liệu gián tiếp, hoặc đặt giả định rồi hiệu chỉnh theo trạng thái thị trường và chạy độ nhạy (mục D).
- Báo cáo ghi: *"quy mô, tốc độ và giá cước theo Hà Nội; lưới, cầu theo giờ và độ dài chuyến là giả định đã hiệu chỉnh"*. Không gọi là "mô phỏng Hà Nội", vì không có dữ liệu cầu theo giờ, theo khu vực của Hà Nội (H-20).

**Nhãn nguồn:**
- **[data]** số liệu công bố;
- **[paper]** bài báo;
- **[suy]** tính ra từ số liệu công bố;
- **[assume]** giả định của nhóm;
- **[hiệu chỉnh]** giá trị xuất phát, chỉnh ở S8 theo chỉ tiêu mục C.

---

## A. Quyết định đã chốt

1. **Mô phỏng xe ô tô 4 chỗ (kiểu GrabCar), không phải xe máy.**
   - Số liệu tốc độ (TomTom) là tốc độ ô tô; Grab công bố bảng giá ô tô rõ ràng; mô hình hiện tại vốn là ô tô.
2. **Tiền tính bằng VND.**
   - Đổi tên `_usd` → `_vnd`, `cents` → đồng nguyên, trên toàn repo: khoảng 1.150 chỗ trong 79 file (`sim/`, `tests/`, `analysis/`, `dashboard/`, `notebooks/`, `config/`, `docs/`). Làm một lần, theo kiểu tìm–thay hàng loạt, trong PR hợp đồng.
   - Sổ ngân sách đang tính bằng cent nguyên, nên đổi sang đồng nguyên không vướng gì.
   - Tỷ giá dùng khi đối chiếu số cũ: **25.700 đ/USD** (Vietcombank, mua chuyển khoản 25.690 đ ngày 10/10/2026).
3. **Ô H3 độ phân giải 7, thành phố bán kính 4: 61 ô, 315 km².**
4. **Sự kiện chia hai loại địa điểm:** sân vận động và phố đi bộ. `shocks.events` đổi sang danh sách loại địa điểm.
5. **Mưa lấy xác suất trung bình cả năm**, với khung giờ cố định chiều tối.

---

## B. Giá trị tham số

### B1. Không gian và tốc độ

| Khóa YAML | Cũ | **Mới** | Nguồn |
|---|---|---|---|
| `space.edge_km` | 0,75 | **1,41** | [data] H3 độ phân giải 7: diện tích TB 5,161 km²; cạnh để đúng diện tích = √(5,161/2,598) |
| `space.grid_radius` | 3 (37 ô, 54 km²) | **4 (61 ô, 315 km²)** | [assume] cỡ 12 quận nội thành cũ của Hà Nội (cộng nhẩm ~300 km²) |
| `space.base_speed_kmh` | 18,0 | **18,0** | [data] TomTom 2025, Hà Nội: 10 km mất 33 phút 20 giây |
| `space.speed_factor_by_hour` (0…23h) | đêm 1,20–1,25; cao điểm 0,75–0,80 | **[1.45, 1.45, 1.45, 1.45, 1.40, 1.25, 1.00, 0.85, 0.85, 0.95, 1.00, 1.00, 1.00, 1.00, 1.00, 0.95, 0.85, 0.76, 0.76, 0.85, 1.00, 1.10, 1.25, 1.35]** | [data] TomTom: cao điểm sáng 15,3 km/h (×0,85), cao điểm tối 13,6 km/h (×0,76). [suy] ban đêm ≈ 27 km/h (×1,45), từ độ tắc trung bình 49,2%. Các giờ giữa nội suy [assume] |
| `space.detour_factor` | 1,3 | **1,3** | [assume] giữ |
| `matching.max_pickup_eta_min` | 30 | **30** | giữ; quy tắc cứng 6 cấm giảm. Với tới 2–3 vành ô |

Hệ quả, tính ra từ các dòng trên:
- tâm hai ô kề cách 2,44 km, tức ~3,2 km đường thực;
- đi giữa hai ô kề mất **~11 phút** giờ bình thường, **~14 phút** giờ cao điểm, **~7 phút** ban đêm;
- chuyến trong cùng ô dài ~1,5 km.

### B2. Cung (tài xế)

| Khóa YAML | Cũ | **Mới** | Nguồn |
|---|---|---|---|
| `supply.shift_len_mean_h` | 8,0 | **11,2** | [data] khảo sát: tài xế ô tô công nghệ làm 11,2 giờ/ngày (xe máy 9,2) |
| `supply.shift_len_sd_h` | 1,5 | **2,0** | [assume] |
| `supply.shift_len_clip_h` | [4, 11] | **[4, 14]** | [assume] |
| `supply.fleet_size` | 240 | **1.300** | [hiệu chỉnh]. Giữ số giờ-xe trên mỗi km² của mô hình cũ cho 1.000: 240 × 8 giờ × 315/54 ÷ 11,2 giờ ≈ 1.000. Nhưng 1.000 **vi phạm ngay** chỉ tiêu chuyến/tài xế/ngày (mục C): mô hình cũ hoàn thành ~3.944 chuyến/ngày với 240 xe ca 8 giờ (16,4 chuyến/xe); cầu mới ×5,8 cho ~23.000 chuyến/ngày, chia 1.000 xe là 23 chuyến/xe, trên dải [8; 18]. Xuất phát 1.300 cho ~17,7 chuyến/xe, nằm trong dải; S8 chỉnh tiếp cùng độ căng. Tham chiếu: năm 2018 cả Hà Nội có ~15.000 ô tô công nghệ được cấp phép [data], nội thành 315 km² chiếm cỡ 1/3 đến 1/2 số đó, nên 1.300–1.500 xe hoạt động đồng thời là cùng bậc |
| `supply.shift_start_mixture` | | giữ, rồi hiệu chỉnh | [hiệu chỉnh] theo tỷ lệ xe bận lúc 6–8h (mục C) |

### B3. Cầu và khách

| Khóa YAML | Cũ | **Mới** | Nguồn |
|---|---|---|---|
| `demand.base_sessions_per_cell_h` | 35 | **124** | [hiệu chỉnh] giữ mật độ khách: 35 × 5,161/1,461 |
| `demand.demand_scale` | 0,85 | **0,85** | [hiệu chỉnh] |
| `demand.n_riders` | 20.000 | **120.000** | [suy] Giữ tỷ lệ session trên mỗi khách của mô hình cũ: hiện 25.650 session/ngày ÷ 20.000 khách = 1,28/khách/ngày; cầu mới 149.800 session/ngày ÷ 1,28 ≈ 117.000. Nếu giữ 20.000 thì mỗi khách mở 7,5 session/ngày, không còn nghĩa "khách". Kiểm tra: 120.000 ÷ 61 ô ≈ 2.000 khách/ô ≈ 380 khách/km², tức 1–2% dân nội thành (20.000–40.000 người/km²) là người dùng ô tô công nghệ thường xuyên; với P(đặt) 15%, mỗi khách đặt ~5,8 chuyến/tháng, cùng bậc với Q&Me (77% dùng ≥ 3 lần/tháng) [data] |
| `demand.hour_profile` | đỉnh 8h (1,70), 18h (1,85) | **giữ** | [assume]. Đỉnh trùng giờ cao điểm Hà Nội theo quy định (6–9h, 16–19h30) [data] và giờ tắc nhất của TomTom (17h) [data]; Grab nêu nhu cầu buổi trưa 10–13h [data]. Độ nhạy: hình theo giờ của NYC TLC (mục D) |
| `demand.dest_decay_rings` | 3,0 | **1,2** | [hiệu chỉnh] cho quãng đường TB ≈ 6,0 km trên lưới mới (mục C: 5–8 km). Đã tính: 1,0 → 5,3 km; 1,2 → 6,0 km; 1,5 → 6,7 km |
| `riders.beta_price_per_usd` → **`beta_price_per_kvnd`** | 0,10 / USD | **0,022 / 1.000đ** | [suy] giữ độ nhạy giá tương đối như mô hình cũ: β × giá TB = 0,10 × 19,0 USD ≈ 1,9 = 0,022 × 84 nghìn đồng. Không đổi theo tỷ giá, vì độ nhạy giá đi theo mức giá địa phương. `alpha0` và `delta0` hiệu chỉnh lại theo P(đặt) và mức tăng (mục C) |
| `riders.max_wait_mode_min` | 5,0 | **5,0** | [assume] giữ |

### B4. Giá cước, voucher, hoa hồng (VND)

Công thức giá mới, giống cách Grab tính:

```
giá = 28.473 + 9.818 × max(0, km − 2) + 442 × (phút sau 2 km) + 10.000
phút sau 2 km = thời gian chuyến × max(0, km − 2) / km
```

| Khóa YAML | Cũ | **Mới** | Nguồn |
|---|---|---|---|
| `pricing.base_fare_usd` → **`open_fare_vnd`** | 3,0 USD | **28.473** | [data] GrabCar 4 chỗ Hà Nội, giá tối thiểu 2 km đầu (Grab, cập nhật 08/07/2026; đã gồm VAT 8%) |
| **`pricing.open_km`** (mới) | | **2,0** | [data] như trên |
| **`pricing.per_km_vnd`** (mới) | | **9.818** | [data] mỗi km sau 2 km |
| `pricing.per_min_usd` → **`per_min_vnd`** | 1,70 USD | **442** | [data] mỗi phút sau 2 km |
| **`pricing.platform_fee_vnd`** (mới) | | **10.000** | [data] 5.000–19.000đ tùy điểm đón và quãng đường; lấy mức giữa [assume]. Toàn bộ thuộc nền tảng |
| `pricing.target_mean_fare_usd` | 19,1 | **bỏ** | giá đã do bảng giá quyết định |
| `pricing.commission_rate` | 0,24 | **0,25** | [data] phí ứng dụng Grab 25%; tổng khấu trừ kể cả thuế 27,27% (phần thuế không thuộc nền tảng) |
| `voucher.pct_of_fare` | 0,20 | **0,25** | [data] mã giảm giá GrabCar khung 6–9h, Hà Nội và TP.HCM |
| `voucher.max_usd` → **`max_vnd`** | null | **20.000** | [data] như trên: tối đa 20.000đ |
| `budget.fraction` | 0,30 | **0,30** | giữ |

Kiểm tra:
- chuyến 6 km, 20 phút: 28.473 + 39.272 + 5.893 + 10.000 ≈ **83.638đ** (≈ 84.000đ), voucher 20.000đ (chạm trần);
- chuyến 5 km ≈ 65.000–80.000đ, khớp mức Grab công bố (50.000–80.000đ) [data];
- người dùng ở Hà Nội và TP.HCM chi trung bình 252.000đ/tháng, 77% dùng ≥3 lần/tháng [data, Q&Me], tức mỗi chuyến cỡ ≤84.000đ. Cùng bậc với chuyến 6 km.

**Lợi nhuận nền tảng V(π)** (thay spec §4.6, cài ở H7.8): với mỗi chuyến hoàn thành

```
cước_dịch_vụ  = giá − platform_fee_vnd
driver_pay    = (1 − commission_rate) × cước_dịch_vụ
platform_profit = platform_fee_vnd + commission_rate × cước_dịch_vụ − voucher
```

Phí nền tảng thuộc nền tảng toàn bộ [data]; hoa hồng chỉ tính trên phần cước dịch vụ. Chuyến 6 km: 10.000 + 0,25 × 73.638 = 28.410đ trước voucher, 8.410đ sau voucher 20.000đ. Thuế VAT và thuế thu nhập tài xế không mô phỏng.

**Hệ quả của trần voucher, ghi trước khi chạy:** 25% giá chạm trần 20.000đ khi giá ≥ 80.000đ, tức chuyến dài hơn ~5,6 km, cỡ **một nửa** số chuyến với quãng đường TB 6 km. Voucher mỗi session chỉ còn dao động từ ~9.600đ (chuyến 2 km) tới 20.000đ, khoảng 2 lần, so với dải rộng hơn của mô hình cũ (20% giá, không trần). Vì vậy **lợi ích của xếp hạng theo mỗi đồng** (phát hiện +303 chuyến của bản 2) nhiều khả năng **co lại**; đây là đặc điểm thật của thị trường, báo cáo nói trước và đo, không chỉnh trần để giữ kết quả cũ (dự đoán P2, mục E).

### B5. Biến động tự nhiên (thế giới W1)

`shocks.enabled = false` ở W0 và `true` ở W1 (overlay `config/world_w1.yaml`).

| Khóa YAML | **Giá trị** | Nguồn |
|---|---|---|
| `shocks.day_demand.sigma` | **0,12** | [data] NYC TLC 03/2024, đo trên `runs/tlc`: hệ số biến thiên số chuyến theo ngày 12,8% (chỉ ngày thường: 10%). Không có số liệu Hà Nội |
| `shocks.rain.p_per_day` | **0,31** | [data] Hà Nội ~114 ngày mưa/năm: 114/365. Một ngày mô phỏng là "một ngày bất kỳ trong năm" |
| `shocks.rain.start_hour_range` | **[14,0; 19,0]** | [data] mưa tập trung vào giông chiều tối |
| `shocks.rain.duration_h_range` | **[1,0; 3,0]** | [assume] |
| `shocks.rain.demand_mult` | **1,25** | [paper] Brodeur & Nield (2018): giờ có mưa, số chuyến Uber mỗi giờ ở NYC cao hơn 25% |
| `shocks.rain.speed_mult` | **0,85** | [paper] mưa lớn giảm tốc độ 7–18% |
| `shocks.rain.driver_off_share` | **0,10** | [assume]; báo chí ghi nhiều tài xế nghỉ khi mưa lớn, giá có lúc tăng 200–300% |
| `shocks.events.venues` — sân vận động | **[2, 0,05, 21,5, 23,0, 60, 20,0, 3,0]** | [data] hai sân lớn trong nội thành: Mỹ Đình ~40.000 chỗ, Hàng Đẫy ~22.000 chỗ (V-League cách tuần, concert, sự kiện). [suy] mỗi sân ~1,5 sự kiện/tháng ≈ 0,05/ngày; hai sân cho ≈ 2,8 sự kiện trong 28 ngày dữ liệu, đủ để switchback W1 chứa vài sự kiện (với [1, 0,03] chỉ còn 0,8 sự kiện/28 ngày, gần như không có trong dữ liệu). [suy] 5% khán giả gọi ô tô trong 60 phút ≈ 2.000 lượt, trong khi cầu thường của một ô lúc 22h khoảng 90–100 lượt/giờ, nên ×20 là mức thận trọng. Lượt chạy cho animation cần khung có sự kiện thì ép bằng `--set shocks.events.venues=...` với xác suất 1 cho đúng ngày, ghi lệnh trong `datasets.md` |
| `shocks.events.venues` — phố đi bộ | **[1, 0,43, 21,0, 24,0, 60, 2,0, 1,3]** | [data] phố đi bộ Hồ Gươm mở 19h thứ Sáu–24h Chủ nhật (3/7 ngày ≈ 0,43), hàng chục nghìn lượt khách mỗi cuối tuần. Hệ số [assume] |
| vị trí địa điểm | rút một lần theo `world_seed` | [assume] |
| `shocks.attendance.p_work` | **0,90** | [assume]; tài xế ít ngày nghỉ |
| `shocks.shift_jitter.sd_min` | **20** | [assume] |

Cột của `events.venues`: [số địa điểm, xác suất mỗi ngày, giờ tan từ, giờ tan đến, số phút cầu tăng, nhân cầu ô, nhân cầu vành kề].

### B6. Hủy chuyến

| Khóa YAML | Giá trị | Nguồn |
|---|---|---|
| `cancel.base_per_min` | **0,005** | [assume] giữ |
| `cancel.slope_per_min2` | **0,004** | [assume] giữ |
| `cancel.eta_free_min` | **3,0** | [assume] giữ |

Tỷ lệ hủy là **kết quả** của mô hình, không phải tham số. Kiểm ở mục C và chạy độ nhạy ở mục D.

**Hệ quả của ô lớn, ghi trước khi chạy:** xe từ ô kề mất ~11 phút giờ thường (B1), nên hazard trung bình trên đường đi là 0,005 + 0,004 × (11 − 3) ≈ 0,037/phút và P(hủy) ≈ 1 − e^(−0,037 × 11) ≈ **33%** cho xe đón từ vành 1; từ vành 2 (~22 phút) gần chắc chắn hủy. Kênh hủy sẽ **chi phối** tác hại của voucher, và việc "ô căng mượn xe ô kề" (cơ chế mentor dùng để giải thích tác hại cấp hệ ở bản 2) sẽ yếu đi, tức độ căng trở nên **cục bộ hơn**. Kết quả RQ1 và việc chọn chỉ số độ căng (ring1 / system / hour) có thể đảo so với bản 2. Vì vậy độ nhạy hazard ×0,5 / ×2 ở mục D3 là **bắt buộc**, và H1, H2 được viết với ý thức này (dự đoán P1, mục E).

### B7. Điều xe

| Khóa YAML | Giá trị | Nguồn |
|---|---|---|
| `reposition.mode` | `static_weights` | giữ (quy tắc cứng 5) |
| `reposition.max_idle_min` | **10,0** | [assume] giữ. Với ô 1,41 km, xe đi điều chuyển mất ~11 phút (B1) thay cho ~5 phút trước; trong lúc đó xe không tính vào slack hay utilization (H-11). S8 **báo** tỷ lệ thời gian xe ở trạng thái điều chuyển; nếu vượt 15% tổng giờ-xe thì ghi hạn chế và chạy thêm một điểm độ nhạy `max_idle_min = 20` ở T10.8, không chỉnh ở S8 |

### B8. Quy mô dữ liệu và bộ nhớ

| Đại lượng | Cũ | Mới (ước) |
|---|---|---|
| Session/ngày | 25.650 | ~150.000 |
| Request/ngày (P(đặt) 15%) | ~3.900 | ~22.500 |
| Dòng `observed/sessions` cho 28 ngày | 0,72 triệu | ~4,2 triệu (~0,5 GB parquet mỗi bộ, chấp nhận) |
| Dòng `slot_snapshots` cho 28 ngày | 99.000 | 164.000 |

---

## C. Chỉ tiêu hiệu chỉnh (S8, H8.1)

Chỉ chỉnh các núm: `fleet_size`, `demand_scale`, `shift_start_mixture`, `dest_decay_rings`, `alpha0`, `delta0`.

| Khóa `calibration_targets` | Dải | Nguồn |
|---|---|---|
| `p_request_no_voucher` | [0,13; 0,17] | giữ [data đề bài: 15%] |
| `request_uplift_surplus` | [0,35; 0,70] | giữ [data đề bài: +50%] |
| `share_cellslots_slack_below_0_35` | [0,10; 0,35] | giữ, thiết kế kịch bản (H-23) |
| `share_cellslots_slack_above_1` | [0,30; 0,80] | giữ, thiết kế kịch bản (H-23) |
| `busy_rel_h6` / `h7` / `h8` | [0,31; 0,61] / [0,55; 0,85] / [0,63; 0,93] | [data] NYC TLC (H-31); không có số liệu Hà Nội |
| `mean_gross_fare_usd` | | **bỏ** (giá do bảng giá quyết định) |
| **`mean_trip_km`** (mới) | **[5,0; 8,0]** | [suy] chi tiêu Q&Me + bảng giá Grab |
| **`trips_per_driver_day`** (mới) | **[8; 18]** | [suy] doanh thu GrabCar 20–35 triệu/tháng [data] ÷ 26–30 ngày ÷ 70.000–90.000đ/chuyến |

**Thứ tự ưu tiên khi không thỏa hết** (6 núm, 9 chỉ tiêu, có cặp kéo ngược nhau: thêm xe làm giảm chuyến/tài xế nhưng cũng giảm phần (ô, slot) căng):
1. `p_request_no_voucher` và `request_uplift_surplus` (núm `alpha0`, `delta0`): quyết định ý nghĩa của voucher, phải đạt.
2. `share_cellslots_slack_below_0_35` và `share_cellslots_slack_above_1` (núm `fleet_size`, `demand_scale`): quyết định có hiện tượng cần đo, phải đạt.
3. `busy_rel_h6/h7/h8` (núm `shift_start_mixture`): sửa lỗi lịch ca của bản 2 (Q20), phải đạt ít nhất h7.
4. `mean_trip_km` (núm `dest_decay_rings`): gần độc lập với các núm khác, chỉnh sau cùng.
5. `trips_per_driver_day`: nếu sau 1–4 vẫn lệch thì **ghi hạn chế**, không phá 1–3 để đạt nó; dải [8; 18] là suy từ doanh thu nên kém chắc nhất.

Mỗi vòng hiệu chỉnh ghi vào bảng ở `decisions.md`: giá trị 6 núm, 9 chỉ tiêu, đạt/không. Dự kiến 3 ngày công cho S8 (T8.1–T8.3), không phải 1–2.

Chỉ tiêu kiểm tra (không hiệu chỉnh theo, chỉ báo cáo; lệch xa thì ghi hạn chế):

| Đại lượng | Khoảng hợp lý | Nguồn |
|---|---|---|
| Thời gian chờ đón trung bình | 3–8 phút | [data] NYC TLC 2,8–4,8 phút theo giờ (`runs/tlc/hourly_comparison.csv`); Hà Nội tắc hơn nên cho phép cao hơn |
| Thời gian chuyến trung bình | 15–25 phút | [suy] TomTom: 15 phút đi được 4,5 km |
| Tỷ lệ hủy, tỷ lệ bỏ chờ | báo cáo | không có số liệu |
| Tỷ lệ giờ-xe ở trạng thái điều chuyển | báo cáo, ngưỡng chú ý 15% | xem B7 |

---

## D. Đại lượng không có số liệu Hà Nội: cách xử lý

### D1. Nguyên tắc

Chia tham số thành ba loại:
1. **Có số liệu Hà Nội:** dùng trực tiếp (mục B).
2. **Có số liệu gián tiếp:** suy ra, rồi dùng làm chỉ tiêu hiệu chỉnh hoặc kiểm tra (mục C).
3. **Không có gì:** đặt giả định, hiệu chỉnh theo **trạng thái thị trường** (độ căng) thay vì mức tuyệt đối, chạy **độ nhạy**, và ghi vào hạn chế.

Vì sao làm vậy được: kết luận của đề tài là **tương đối**, gồm θ\*, phần trăm chênh lệch giữa các chính sách, xếp hạng chính sách, số chuyến thêm trên mỗi 100.000đ. Các kết luận này phụ thuộc chủ yếu vào **độ căng cung–cầu**, không vào số xe hay số khách tuyệt đối. Độ căng thì điều khiển trực tiếp được bằng chỉ tiêu hiệu chỉnh (H-23).

### D2. Từng đại lượng

| Đại lượng | Đầu vào / đầu ra | Cách làm | Giá trị |
|---|---|---|---|
| Số tài xế | đầu vào | Xuất phát từ mật độ giờ-xe cũ, hiệu chỉnh theo độ căng và số chuyến/tài xế/ngày | xuất phát 1.000; mục tiêu 8–18 chuyến/tài xế/ngày |
| Số khách, số lượt đặt | đầu vào | Xuất phát từ mật độ khách cũ, hiệu chỉnh cùng số xe; P(đặt) 15%, mức tăng +50% | xuất phát 124 lượt/ô/giờ |
| Quãng đường, thời gian chuyến | đầu vào (quãng đường) / đầu ra (thời gian) | Chỉnh `dest_decay_rings`; thời gian tự ra từ tốc độ TomTom | xuất phát 1,2 (≈ 6,0 km); mục tiêu 5–8 km; kiểm 15–25 phút |
| Hình dạng cầu theo giờ | đầu vào | Giữ hình cũ (đỉnh khớp giờ cao điểm Hà Nội); độ nhạy với hình NYC TLC | xem B3 |
| Tỷ lệ xe bận theo giờ | đầu vào (qua lịch ca) | Hiệu chỉnh lịch ca theo NYC lúc 6–8h; độ dài ca theo số liệu Hà Nội | xem C |
| Thời gian chờ đón | **đầu ra** | Không đặt trực tiếp; kiểm sau hiệu chỉnh | 3–8 phút |
| Tỷ lệ hủy | **đầu ra** | Giữ tham số hazard cũ; độ nhạy ×0,5 và ×2 | báo cáo |

### D3. Độ nhạy (S10, cùng T10.5)

Chạy chính sách khuyến nghị và các chính sách so sánh dưới:
- hình cầu theo giờ: cũ và NYC TLC;
- hazard hủy: ×0,5, ×1, ×2;
- quãng đường trung bình: ~5 km và ~8 km (`dest_decay_rings` 1,0 và 2,0).

Báo θ\* và chênh lệch giữa các chính sách có đổi không. Nếu không đổi, các giả định trên không quyết định kết luận.

---

## E. Ảnh hưởng tới code và kế hoạch

**Hợp đồng B9 phải sửa trước khi commit:**
- đổi tên tiền sang VND trên toàn repo (`_usd` → `_vnd`, `cents` → đồng);
- khóa giá mới: `pricing.open_fare_vnd`, `open_km`, `per_km_vnd`, `per_min_vnd`, `platform_fee_vnd`, `voucher.max_vnd`; bỏ `pricing.target_mean_fare_usd`;
- `riders.beta_price_per_usd` → `beta_price_per_kvnd`;
- `shocks.events` đổi sang `venues` (danh sách loại địa điểm);
- `calibration_targets`: bỏ `mean_gross_fare_usd`, thêm `mean_trip_km`, `trips_per_driver_day`.

**Việc thêm ngoài kế hoạch S7:**
- `pricing.py` (Tình): công thức giá theo km + phút + phí nền tảng, trần voucher;
- `space`/`demand`/`supply` (Hoàng): giá trị mới ở mục B;
- dashboard và notebook: đổi nhãn tiền;
- báo cáo: Bảng 4.1 và Phụ lục A ghi nguồn từng tham số theo file này.

**Thời gian chạy và tiêu chí A5 (nhóm tự quyết, ghi `decisions.md` ở B9, sửa quy tắc 7 của `CLAUDE.md` cùng PR):**
- Session/ngày ×5,8, xe ×5,4, ô ×1,65. Hiện 7 giây/ngày mô phỏng (A5 bản 2). Ước **40–60 giây/ngày/tiến trình**. H7.1 đo thật ngay sau khi đổi giá trị, trước mọi task khác.
- **A5-HN:** ≤ **60 giây/ngày mô phỏng trên một tiến trình**, đo bằng `evaluate` `all_on` 1 ngày, 3 lần lấy trung vị (cách đo cũ). Lý do đổi từ 30: tiêu chí cũ đặt cho thành phố 54 km²; quy mô mới gấp 5,8 lần số session mà chỉ cho gấp 2 thời gian, tức đã đòi code nhanh hơn 2,9 lần trên mỗi session. Nếu đo vượt 60 giây: Hoàng `--profile`, tối ưu **đúng bước nặng nhất**, tối đa 1 ngày công, được dùng `numba` kèm fallback (quy tắc 7). Vẫn vượt thì ghi số thật và không nới thêm.
- Mọi lệnh sinh dữ liệu và quét dùng `runner.n_procs = số lõi` (máy hiện có 8 lõi); thời gian chạy thật ghi vào `datasets.md`.

Ngân sách tính toán (giả định 50 giây/ngày/tiến trình, 8 lõi, tức ~6 giây/ngày hiệu dụng; cập nhật sau H7.1):

| Việc | Ngày mô phỏng | Giờ máy |
|---|---|---|
| S8 dữ liệu W0 + W1 (luật cũ 28 + 4 mức u × 28 + 3 switchback × 28 + A/B 28 + GTE 20 + GTE đội xe lớn 20 + bật/tắt 10, mỗi thế giới ~302) | ~615 | ~1,1 |
| S10 bảng chính sách (12 chính sách × 30 seed × 2 thế giới + pilot κ) | ~800 | ~1,4 |
| S10 quét θ (16 × 30 × 2 + pilot κ mỗi θ) | ~1.300 | ~2,3 |
| S10 độ vững (9 tổ hợp × 30 seed × 2 chính sách + 3 `world_seed` × 12 × 30) | ~1.600 | ~2,8 |
| S10 độ nhạy (7 cấu hình × 5 chính sách × 10 seed + quét θ rút gọn) | ~560 | ~1,0 |
| **Tổng** | **~4.900** | **~8,5 giờ**, tức một đêm máy cho S10 |

**Dự đoán ghi trước khi chạy** (cùng H1, H2 vào `decisions.md` ở B9; đúng hay sai đều báo ở Chương 4):
- **P1 (từ B6):** trên lưới mới, tác hại của voucher đi chủ yếu qua kênh **hủy** khi xe đón từ ô kề; phần tác hại cấp hệ do "mượn xe ô kề" nhỏ hơn bản 2, nên chỉ số cục bộ (`cell`, `ring1`) không thua `system` rõ như Hình PL.3 cũ.
- **P2 (từ B4):** vì trần 20.000đ làm voucher gần bằng nhau giữa các session, chênh lệch giữa xếp theo mỗi đồng và xếp theo lượt phát **nhỏ hơn** +237 chuyến (303 − 66) của bản 2, tính theo phần trăm N.
- **P3 (từ B5):** trên W1, phần (ô, slot) căng ngoài 5–8h tăng rõ so với W0, và đó là nơi chính sách theo độ căng hơn luật tắt theo giờ (H2 chỉ được coi là xác nhận nếu chênh lệch có khoảng tin cậy 95% không chứa 0 **và** tập trung vào các slot có biến động theo `meta/shocks`).

---

## Nguồn

- [Grab – Bảng thông tin các dịch vụ trên ứng dụng Grab (giá GrabCar Hà Nội, cập nhật 08/07/2026)](https://www.grab.com/vn/blog/bang-thong-tin-cac-dich-vu-tren-ung-dung-grab/)
- [Grab – Ưu đãi 25% đặt Grab khung giờ sáng](https://www.grab.com/vn/uu-dai-25-khi-dat-grabbike-grabcar-khung-gio-sang/)
- [Grab – Introducing GrabCar Plus in Vietnam](https://grab.com/vn/en/grabcar-plus)
- [Grab – Chương trình Giờ vàng GrabCar TP.HCM và Hà Nội](https://www.grab.com/vn/blog/driver/grabcar-giovang-hcmhn/)
- [Vietnam Tourism – Does Grab work in Vietnam, guide 2026 (giá tham khảo chuyến 5 km)](https://www.vietnamtourism.com/en/does-grab-work-in-vietnam-complete-guide-2026)
- [VNReview – Tỷ lệ chiết khấu của tài xế xe công nghệ khi giảm thuế VAT](https://vnreview.vn/threads/ty-le-chiet-khau-cua-tai-xe-xe-cong-nghe-thay-doi-the-nao-khi-giam-thue-vat.20750/latest)
- [FPT Shop – Chạy Grab thu nhập bao nhiêu 2025 (doanh thu GrabCar 20–35 triệu/tháng)](https://fptshop.com.vn/tin-tuc/danh-gia/chay-grab-thu-nhap-bao-nhieu-2025-191525)
- [Q&Me – Car ride-hailing service usage habits in Vietnam 2024](https://qandme.net/en/report/car-ride-hailing-service-usage-habits-in-vietnam-2024.html)
- [TomTom Traffic Index – Hà Nội](https://www.tomtom.com/traffic-index/city/ha-noi)
- [SGGP – Hà Nội ùn ứ cuối năm do đường sá quá tải](https://www.sggp.org.vn/ha-noi-un-u-cuoi-nam-do-duong-sa-qua-tai-nhieu-xe-hoi-post725225.html)
- [VinWonders – Khí hậu Hà Nội](https://vinwonders.com/vi/wonderpedia/news/khi-hau-ha-noi/)
- [Vietnam Tourism – Mùa mưa ở Hà Nội](https://www.vietnamtourism.com/vi/mua-mua-o-ha-noi-vao-thang-may-cam-nang-chi-tiet-cho-chuyen-)
- [IZA – Brodeur & Nield, Has Uber made it easier to get a ride in the rain?](https://newsroom.iza.org/en/archive/research/has-uber-made-it-easier-to-get-a-ride-in-the-rain)
- [TRID – Impacts of Weather on Urban Freeway Traffic Flow Characteristics and Facility Capacity](https://trid.trb.org/View/760690)
- [VietnamNet – Xe ôm công nghệ liên tục tăng giá](https://vietnamnet.vn/xe-om-cong-nghe-lien-tuc-tang-gia-xe-co-dau-ngo-duoc-thoi-695479.html)
- [VnBusiness – 200.000 lái xe công nghệ cần được tiếp cận chính sách an sinh xã hội](https://vnbusiness.vn/200000-lai-xe-cong-nghe-can-duoc-tiep-can-chinh-sach-an-sinh-xa-hoi.html)
- [VnBusiness – Hà Nội đề xuất gắn phù hiệu như taxi truyền thống với Uber, Grab](https://vnbusiness.vn/ha-noi-de-xuat-gan-phu-hieu-nhu-taxi-truyen-thong-voi-uber-grab-1023415.html)
- [VnExpress – Concert Big Bang ở Hà Nội cháy vé](https://vnexpress.net/concert-big-bang-chay-ve-5110090.html)
- [FPT Shop – Phố đi bộ Hà Nội](https://fptshop.com.vn/tin-tuc/danh-gia/pho-di-bo-ha-noi-190990)
- [thuviennhadat.vn – Chi tiết bản đồ phường Hoàn Kiếm sau sáp nhập](https://thuviennhadat.vn/bat-dong-san/chi-tiet-ban-do-phuong-hoan-kiem-sau-sap-nhap-21995.html)
- [webgia – Tỷ giá Vietcombank ngày 10/10/2026](https://webgia.com/ty-gia/vietcombank/10-10-2026.html)
- NYC TLC High Volume FHV trip records, 03/2024 (`runs/tlc/fhvhv_tripdata_2024-03.parquet`, xem `docs/datasets.md`)
- H3 – bảng diện tích ô theo độ phân giải (h3geo.org/docs/core-library/restable)
