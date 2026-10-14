# Phân công theo sprint: bản sửa cuối sau review bản 2 (mỗi sprint một người)

Người làm: **1. Phan Văn Tình**, **2. Nguyễn Huy Hoàng**. Người hướng dẫn: Nguyễn Bảo Long.

Phạm vi: Giai đoạn 1–5 của `docs/ke_hoach_sua_v3.md`. Giai đoạn 0 (sửa báo cáo không phụ thuộc số liệu) đã xong. Đây là lần sửa cuối, cho ra sản phẩm cuối cùng.

Giá trị và nguồn của mọi tham số: **`docs/de_xuat_tham_so_ha_noi.md` (ĐX)**. Task nào đặt giá trị tham số thì lấy đúng số trong ĐX; muốn đổi thì sửa ĐX trước (cả hai duyệt).

**Cách chia việc (đổi so với bản 14/10 sáng):** mỗi sprint do **một người làm trọn**, người kia **chỉ review** và nhận bàn giao để làm sprint kế tiếp. Không chia task trong cùng một sprint cho hai người, để không trùng đầu việc và không phải chờ nhau giữa sprint.

| Sprint | Giai đoạn | Người làm | Người review | Ước tính |
|---|---|---|---|---|
| S7 | 1. Sửa simulator, quy mô Hà Nội, VND | **Hoàng** | Tình | 5–6 ngày |
| S8 | 2. Hiệu chỉnh và sinh dữ liệu W0, W1 | **Tình** | Hoàng | 3 ngày (máy ~1 giờ, 8 lõi) |
| S9 | 3. Phương pháp (uplift, độ căng, ngưỡng, thác nước, burn-in) | **Hoàng** | Tình | 2–3 ngày |
| S10 | 4. Thí nghiệm đánh giá + code animation | **Tình** | Hoàng | 3 ngày + một đêm máy (~8,5 giờ) |
| S11 | 5. Báo cáo, animation bản cuối, trả lời mentor | **Tình** | Hoàng (review chéo toàn bộ) | 3 ngày |

Khối lượng: Hoàng S7 + S9 ≈ 7–9 ngày; Tình S8 + S10 + S11 ≈ 9 ngày. Người đang chờ review làm việc chuẩn bị ở mục 5, không ngồi không.

Quyết định đã chốt (giữ nguyên):
- **Quy mô Hà Nội:** ô H3 độ phân giải 7 (5,16 km²), thành phố bán kính 4 (61 ô, 315 km²), tốc độ theo TomTom Hà Nội (ĐX mục B1).
- **Tiền VND, giá cước theo GrabCar Hà Nội**, voucher 25% tối đa 20.000đ (ĐX mục B4). Chỉ mô phỏng ô tô 4 chỗ.
- **Animation do Tình làm**, tách riêng khỏi dashboard, theo đủ `huong-dan-animation-chinh-sach.md` (nằm trong S10, S11 của Tình).
- Việc 1.4 làm **đủ 5 loại biến động**, với giá trị ở ĐX mục B5.
- Việc 4.9 và 5.6 **chỉ làm nếu mentor yêu cầu** (mục 6).
- Không giới hạn thời gian: làm đủ mọi việc, không cắt.
- **Nhóm tự quyết, không hỏi lại mentor** (chiều 14/10, sau rà soát ĐX):
  - **A5-HN:** tiêu chí thời gian chạy trên cấu hình Hà Nội là ≤ 60 giây/ngày mô phỏng/một tiến trình (ĐX mục E), thay 30 giây của thành phố 54 km²; mọi lệnh chạy dùng `runner.n_procs = số lõi`. Ghi `decisions.md` và sửa quy tắc 7 của `CLAUDE.md` trong PR B9.
  - Điểm xuất phát `fleet_size = 1.300`, `n_riders = 120.000` (ĐX B2, B3), sân vận động `[2, 0,05, …]` (ĐX B5), lợi nhuận V(π) có phí nền tảng (ĐX B4), điều xe giữ `max_idle_min = 10` và báo tỷ lệ (ĐX B7).
  - **Ba dự đoán P1–P3** (ĐX mục E) ghi vào `decisions.md` cùng H1, H2 **trước khi** sinh dữ liệu; đúng hay sai đều báo ở Chương 4.
  - Thứ tự ưu tiên chỉ tiêu hiệu chỉnh khi không thỏa hết (ĐX mục C); S8 ước 3 ngày.

Quy ước ký hiệu:
- `H7.x` là task của Hoàng trong S7, `T8.x` là task của Tình trong S8… (chữ đầu = người làm, số đầu = sprint). Số sprint tiếp theo bản cũ (**S7–S11**) để không trùng T1.x–T6.x, H1.x–H6.x trong `docs/log.md`. Task đổi người so với bản sáng 14/10 ghi mã cũ trong ngoặc.
- `B9`–`B14` là các điểm bàn giao; `G7`–`G11` là kiểm tra cuối sprint.
- `W0` là thế giới không biến động; `W1` là thế giới có biến động (overlay `config/world_w1.yaml`).
- `Q..` là câu hỏi của mentor ở Phần I của `Report_version2_review.md`; `KN` là `khuyen-nghi-code-simulator.md`. Hai file này và `huong-dan-animation-chinh-sach.md` do mentor gửi riêng, không lưu trong repo.

**Trạng thái ngày 14/10:**
- Đã gộp vào `develop`: PR #23 (Tình: T7.1 chặn ŝ, bộ kiểm hồi quy G7, T-39); PR #24 (Tình: `scope = city`, oracle qua `OracleHiddenView`, cột `lag_slot_same_block`, `budget_pilot_*`, `world_seed`, T-40); PR #25 (Hoàng: kế hoạch v3 Hà Nội, ĐX).
- Trên `develop1`, chưa commit: đính chính T-41 (`uses_hidden` → `hidden_view`, bỏ cột `slack_lag_cell`, `slack_hat` nhận nghĩa mới). Tình commit và PR trước khi Hoàng bắt đầu S7, để B9 không phải sửa lại.
- Bản nháp code của B9 (khóa mô hình, luồng `SHOCK`, cột schema, chỉ tiêu xe bận) nằm trên `develop2`, chưa commit. Còn thiếu: phần VND, khóa giá cước, danh sách địa điểm sự kiện.

---

## 1. Nguyên tắc và Git

1. **Một người một sprint.** Người làm sprint sửa mọi file sprint đó cần, kể cả file trước đây thuộc người kia. Người kia review toàn bộ PR của sprint. Bảng sở hữu cũ (mục 2 của `docs/phan_cong.md`) chỉ còn dùng để biết ai hiểu file nào khi review.
2. **Hợp đồng trước (B9, đầu S7, Hoàng làm, Tình duyệt):** chốt mọi tên khóa config, tên cột, luồng ngẫu nhiên, và đổi tên tiền sang VND. Sau B9 không đổi tên nữa.
3. **Mặc định trong B9 bằng hành vi cũ.**
   - Khóa nào làm đổi mô hình thì trong B9 có mặc định cho ra đúng kết quả cũ. Khóa nào chưa cài mà bị đặt giá trị mới thì code báo `NotImplementedError`, không chạy lặng lẽ mô hình cũ.
   - Task cài khóa nào thì đổi mặc định của khóa đó sang giá trị mới. Giá trị Hà Nội vào ở H7.1, H7.4, H7.8.
4. **Sprint xong mới bàn giao.** Người làm chạy mục "Kiểm tra cuối sprint"; đạt thì ghi log gate, mở PR, người kia review và chạy đúng phần "Người nhận kiểm tra" rồi ghi log "nhận B-x". Không đạt thì báo số liệu, ghi log, không nới tiêu chí.
5. Mọi thay đổi đụng `sim/`, `config.py`, `rng.py`, `schema.md` cần mục `docs/decisions.md` (ID `H-`/`T-`), mục log, và PR được người kia duyệt (theo `CLAUDE.md`).
6. **Review không phải là chờ.** Người review trả lời trong một ngày làm việc. Trong lúc đó người kia đọc trước tài liệu của sprint mình sắp làm, không code lên nhánh của sprint đang mở.

**Git:**
- Hoàng code trên `develop2`, Tình trên `develop1`. Trước mỗi task: kéo `develop` về nhánh mình.
- Mỗi task một commit, kèm mục log trong `docs/log.md` (mục của người làm). Mô tả PR chép từ các mục log của sprint. Không gắn tag tác giả vào commit.
- Xong sprint: một PR từ nhánh mình vào `develop`, người kia review, gộp bằng merge commit (không squash). Bàn giao người kia đang chờ (B9) thì PR sớm.
- Cuối S11: gộp `develop → main` và gắn tag bản cuối.

---

## 2. Người làm và người review theo phần việc

| Phần việc | Làm | Review |
|---|---|---|
| `sim/` (mọi module), `config/`, `rng.py`, `schema.md`, `tests/` của S7 | Hoàng (S7) | Tình |
| Hiệu chỉnh `default.yaml`, `world_w1.yaml`, sinh dữ liệu, `datasets.md`, `check_dataset`, `validation.py` | Tình (S8) | Hoàng |
| `analysis/uplift.py`, `tension.py`, `theta.py`, `estimate.py`, `confounding.py`, `interference.py` (thác nước, burn-in), hàm điểm mới | Hoàng (S9) | Tình |
| `policy_table.py`, `qini_vs_value.py`, `metrics.py`, `figures.py`, notebook 01–05, `analysis/animation.py`, độ nhạy, độ vững | Tình (S10) | Hoàng |
| Báo cáo LaTeX toàn bộ, `notebooks/06_animation.ipynb`, file trả lời Q1–Q27, slide | Tình (S11) | Hoàng (review chéo từng chương) |

**Chung (PR cả hai duyệt):** `docs/de_xuat_tham_so_ha_noi.md`; `tests/fixtures/regression_s7*` (chỉ sinh lại một lần ở B9); `CLAUDE.md`; file này.

---

## 3. Các sprint

### Sprint 7 (Hoàng): Sửa simulator, quy mô Hà Nội, VND (Giai đoạn 1)

**Đầu S7: PR hợp đồng B9** (Hoàng soạn tiếp từ bản nháp trên `develop2`, sau khi kéo `develop` có PR #24 và đính chính T-41; Tình duyệt).

1. **Khóa mô hình**, mặc định bằng hành vi cũ:
   - `matching.ring_tiebreak: lowest_id | most_idle` (B9: `lowest_id`);
   - `cancel.exact_time: bool` (B9: `false`);
   - `policy.threshold.scope` có `city` (đã có, PR #24); tên hàm điểm `oracle` (đã có, PR #24);
   - mục `shocks:` gồm `enabled` (B9: `false`); `day_demand.sigma`; `events.venues` (danh sách loại địa điểm, ĐX mục B5); `rain.*`, `attendance.p_work`, `shift_jitter.sd_min`.
2. **Tiền VND** (việc 1.0b):
   - đổi tên `_usd` → `_vnd`, `cents` → đồng nguyên trên toàn repo bằng một script tìm–thay (~1.150 chỗ, 79 file), gồm `budget_pilot_spent_usd` → `budget_pilot_spent_vnd`;
   - khóa giá mới: `pricing.open_fare_vnd`, `open_km`, `per_km_vnd`, `per_min_vnd`, `platform_fee_vnd`; `voucher.max_vnd`; `riders.beta_price_per_kvnd`; bỏ `pricing.target_mean_fare_usd`;
   - giá trị trong B9 là **giá trị cũ viết theo đơn vị mới** (1 USD = 100 đơn vị):

     | Khóa | Giá trị trong B9 |
     |---|---|
     | `open_fare_vnd` | 300 |
     | `open_km` | 0 |
     | `per_km_vnd` | 0 |
     | `per_min_vnd` | 170 |
     | `platform_fee_vnd` | 0 |
     | `max_vnd` | null |
     | `beta_price_per_kvnd` | 1,0 |
     | `commission_rate` | 0,24 |
     | `pct_of_fare` | 0,20 |

   - công thức theo km và phí nền tảng chưa cài: đặt `open_km`, `per_km_vnd` hoặc `platform_fee_vnd` khác 0 thì báo `NotImplementedError` cho tới H7.8.
3. **`calibration_targets`:** thêm `busy_rel_h6/h7/h8`, `mean_trip_km` [5; 8], `trips_per_driver_day` [8; 18]; bỏ `mean_gross_fare_usd`; cách tính viết trong `tests/test_acceptance_core.py` và `analysis/validation.py`. Từ B9 tới T8.1, test CAL chậm sẽ không đạt vì có chỉ tiêu mới chưa hiệu chỉnh: ghi log, không nới dải.
4. **`rng.py`:** luồng `SHOCK = 8`, mã `ShockKind`; `WorldPart.VENUES = 4`. Không đánh số lại mã cũ.
5. **`schema.md`:** cột tiền đổi `_vnd`; session giữ `lag_slot_same_block` và nghĩa mới của `slack_hat` (đã có, T-41); `run_metadata` giữ `budget_pilot_seed`, `budget_pilot_spent_vnd`, `hidden_view` (đã có); `policy_results` giữ `world_seed` (đã có); bảng mới `meta/shocks` (luôn ghi, rỗng ở W0).
6. **Kiểm tương đương đơn vị:** chạy 4 lượt của bộ kiểm hồi quy G7 bằng code trước và sau B9; số chuyến, số request, số hủy phải trùng; cột tiền khớp ×100 trong sai số 1e-6. Đạt thì viết lại `regression_s7_pinned.yaml` theo khóa mới và **sinh lại `regression_s7.json` một lần** (đính chính T-39 b).
7. **`decisions.md`** (đánh số tiếp từ H-28): khóa mô hình; biến động và luồng `SHOCK`; chỉ tiêu hiệu chỉnh (đính chính một phần H-20); cột schema; quy mô Hà Nội và tiền VND (trỏ tới ĐX); đính chính T-39 b; A5-HN 60 giây và `n_procs`; hai giả thuyết và ba dự đoán ghi trước khi chạy: (H1) W0: chính sách theo độ căng ngang luật tắt theo giờ; (H2) W1: chính sách theo độ căng thắng, chênh lệch có khoảng tin cậy 95% không chứa 0 và tập trung vào các slot có biến động; (P1) kênh hủy chi phối, độ căng cục bộ hơn bản 2; (P2) lợi ích xếp theo mỗi đồng co lại vì trần voucher; (P3) W1 căng ngoài 5–8h rõ hơn W0 (ĐX mục E). Cùng PR: sửa quy tắc 7 của `CLAUDE.md`.

**Task S7 (Hoàng):**

| Mã | Việc |
|---|---|
| **H7.1** | Quy mô Hà Nội (việc 1.0, ĐX B1–B3). Giá trị: `edge_km = 1.41`, `grid_radius = 4`, `speed_factor_by_hour` theo TomTom, ca 11,2 giờ (sd 2,0, chặn [4, 14]), `fleet_size = 1300`, `n_riders = 120000`, `base_sessions_per_cell_h = 124`, `dest_decay_rings = 1.2`. Sửa test kiểm cứng 37 ô (`test_engine.py`), kích thước cụm 7 ô (`test_space.py`) và `tiny.yaml` nếu cần. **Đo A5-HN ngay** (`evaluate` `all_on` 1 ngày, 3 lần, trung vị): ≤ 60 giây/ngày/tiến trình thì đi tiếp; vượt thì `--profile`, tối ưu đúng bước nặng nhất, tối đa 1 ngày công, được dùng `numba` kèm fallback; vẫn vượt thì ghi số thật, không nới. Cập nhật bảng ngân sách tính toán ở ĐX mục E theo số đo |
| **H7.2** | Luật chọn xe vành ngoài: khi hòa lấy ô nhiều xe rảnh nhất (`space.find_pickup`); ETA báo giá và lúc ghép dùng chung luật. Test thế giới đối xứng: tương quan `cell_id`–số lần làm ô nguồn ≈ 0. Đổi mặc định `ring_tiebreak` sang `most_idle` (việc 1.1) |
| **H7.3** | Hủy đúng thời điểm: `t_cancel = t_ghép + 60·e/h`; ở bước 1, nếu `t_cancel < t_đón` thì hủy thay vì đón, xe rảnh theo luật nửa ETA (`trips.py`, `cancel.py`); không rút thêm số. Test so với hazard chính xác, nhả ngân sách đúng. Đổi mặc định `exact_time` sang `true` (việc 1.2) |
| **H7.4** | Biến động tự nhiên (việc 1.4, ĐX B5): `sim/shocks.py` mới; `demand.py`, `supply.py`; tốc độ khi mưa trong `space.py`/`matching.py`/`trips.py`. Gồm: cầu theo ngày (σ 0,12); hai loại địa điểm sự kiện (sân vận động `[2, 0,05, 21,5, 23,0, 60, 20,0, 3,0]`, phố đi bộ `[1, 0,43, 21,0, 24,0, 60, 2,0, 1,3]`, vị trí rút theo `world_seed`); mưa (p 0,31, 14–19h, cầu ×1,25, tốc độ ×0,85, 10% tài xế nghỉ); tài xế đi làm 90%; giờ vào ca lệch 20 phút. Lịch rút trước theo ngày qua luồng `SHOCK`; chính sách không đọc được |
| **H7.5** | Test cho H7.4: tắt biến động thì trùng từng số với mốc G7; cùng ngày cùng biến động dưới mọi chính sách; độ lớn biến động đúng tham số |
| **H7.6** (cũ T7.4) | Ghi độ căng trễ vào `slack_hat` cho `ExperimentPolicy` và `LegacyPolicy` (`snapshots.lag("slack", 1)` chặn ở `slack_cap`), điền cờ `lag_slot_same_block` (`policies/experiment.py`, `legacy.py`, `pricing.py`); test không nhìn trước (việc 1.5, KN 3.3) |
| **H7.7** (cũ T7.5) | `logger.py`: ghi bảng `meta/shocks` từ lịch của `sim/shocks.py`; `runner.py`: kiểm `budget_pilot_spent_vnd` đúng sau đổi tên (việc 1.5, Q23) |
| **H7.8** (cũ T7.6) | Giá cước Hà Nội (việc 1.0b, ĐX B4), `pricing.py`: giá = 28.473đ (2 km đầu) + 9.818đ/km + 442đ/phút sau 2 km + phí nền tảng 10.000đ; lợi nhuận V(π) mỗi chuyến = phí nền tảng + `commission_rate` × (giá − phí) − voucher, `driver_pay` = (1 − `commission_rate`) × (giá − phí) (ĐX B4, thay spec §4.6); voucher 25% tối đa 20.000đ; `commission_rate = 0.25`; `riders.beta_price_per_kvnd = 0.022`. Điểm oracle đổi đơn vị sang chuyến thêm trên mỗi 1.000đ (`scores.py`). Test: chuyến 6 km 20 phút ≈ 83.638đ, lợi nhuận trước voucher 28.410đ; voucher chạm trần ở giá ≥ 80.000đ; bất biến sổ ngân sách bằng đồng nguyên. Đổi nhãn tiền trên dashboard |

Đã xong trước S7, Hoàng kế thừa: T7.1 (chặn ŝ, mốc G7), T7.2 (`city`), T7.3 (oracle, `hidden_view`), cột `budget_pilot_*`, `world_seed` (PR #23, #24, T-39, T-40, T-41).

**Kiểm tra cuối S7 (G7, việc 1.6), Hoàng chạy, Tình kiểm lại khi nhận B10:**
- `pytest -q` toàn bộ pass.
- **Hồi quy:** với `regression_s7_pinned.yaml` (giá trị cũ theo đơn vị mới), đầu ra 1 ngày trùng từng số với mốc sinh lại ở B9.
- Không rò biến ẩn (`test_no_hidden_leak`), không nhìn trước, bất biến ngân sách, số ngẫu nhiên chung giữa các chính sách khi bật biến động, oracle chỉ chạy với chính sách ngưỡng.
- **A5-HN:** ≤ 60 giây/ngày mô phỏng/một tiến trình trên cấu hình Hà Nội (61 ô, ~1.300 xe, ~150.000 session/ngày); ghi số đo thật.
- Tỷ lệ giờ-xe ở trạng thái điều chuyển và tỷ lệ hủy trên `all_on` 1 ngày được ghi log (chỉ báo, ĐX B7, B6).
- **Kiểm giá:** giá trung bình một chuyến và voucher trung bình trên `all_on` 1 ngày nằm cùng bậc với ĐX (chuyến ~6 km ≈ 84.000đ, voucher ≈ 20.000đ).
- Giao **B10** (Hoàng → Tình): PR S7 vào `develop`.

### Sprint 8 (Tình): Hiệu chỉnh và sinh dữ liệu (việc 1.7, Giai đoạn 2)

Trong S8 **chỉ Tình sửa giá trị** `default.yaml` và `world_w1.yaml`; Hoàng review bảng hiệu chỉnh. Ước 3 ngày: 6 núm, 9 chỉ tiêu, có cặp kéo ngược nhau; làm theo **thứ tự ưu tiên ở ĐX mục C**, mỗi vòng ghi một dòng vào bảng hiệu chỉnh trong `decisions.md`.

| Mã | Việc |
|---|---|
| **T8.1** (cũ H8.1) | Hiệu chỉnh trên W0 (ĐX mục C). Núm: `fleet_size`, `demand_scale`, `shift_start_mixture`, `dest_decay_rings`, `alpha0`, `delta0`. Chỉ tiêu: P(đặt) 13–17%; mức tăng +35–70%; (ô, slot) căng 10–35%, dư 30–80%; tỷ lệ xe bận 6/7/8h theo NYC; quãng đường TB 5–8 km; 8–18 chuyến/tài xế/ngày. Báo kèm: thời gian chờ đón TB (3–8 phút), thời gian chuyến TB (15–25 phút), tỷ lệ hủy và bỏ chờ, tỷ lệ giờ-xe điều chuyển (chú ý nếu > 15%, ĐX B7). Không thỏa hết thì theo thứ tự ưu tiên ĐX mục C, `trips_per_driver_day` được ghi hạn chế thay vì phá các chỉ tiêu trên. Ghi bảng hiệu chỉnh vào `decisions.md`; `config_hash` mới |
| **T8.2** (cũ H8.2) | A1 (đường throughput) và A5 trên cấu hình đã hiệu chỉnh; cập nhật test CAL và `tests.md` cho các chỉ tiêu mới |
| **T8.3** (cũ H8.3) | `config/world_w1.yaml`: bật biến động với giá trị ĐX B5; `fleet_size` của W1 = W0 / 0,90 để số xe trung bình bằng W0. Báo các chỉ tiêu thị trường của W1 (không hiệu chỉnh lại W1) |
| **T8.4** (cũ T8.1) | `calibrate_budget` cho W0 và W1, rồi sinh dữ liệu cho **mỗi** thế giới (việc 2.1; ~615 ngày mô phỏng, ~1,1 giờ máy với `runner.n_procs = 8`, ĐX mục E; ghi thời gian thật vào `datasets.md`): luật cũ 28 ngày; luật cũ 4 mức nhắm theo `u`; switchback 1 ô, 7 ô, toàn thành phố, 28 ngày; A/B theo khách 28 ngày; GTE 10 seed; **GTE với đội xe rất lớn**; bật/tắt toàn bộ 5 seed, ghi đầy đủ |
| **T8.5** (cũ T8.2) | Ghi lệnh vào `docs/datasets.md`; chạy `check_dataset` (schema + không rò biến ẩn) trên mọi bộ |
| **T8.6** (cũ T8.3) | A2 (số ngẫu nhiên chung) trên code mới; kiểm `analysis/validation.py` cho ra các chỉ tiêu CAL mới khớp test chậm |

**Kiểm tra cuối S8 (G8):**
- A1, A2, A5 và mọi chỉ tiêu CAL đạt trên W0; chỉ tiêu của W1 được ghi lại.
- Thời gian chờ đón và thời gian chuyến trung bình nằm trong khoảng kiểm ở ĐX mục C. Lệch thì ghi hạn chế, không chỉnh theo.
- Mọi bộ dữ liệu qua `check_dataset`; `config_hash` khớp `datasets.md`.
- **Biến động có tác dụng:** trên W1, tỷ lệ (ô, slot) căng **ngoài 5–8h** tăng rõ so với W0.
- Giao **B11** (Tình → Hoàng): cấu hình W0 đã hiệu chỉnh, overlay W1, toàn bộ dữ liệu, `datasets.md`.

### Sprint 9 (Hoàng): Phương pháp (Giai đoạn 3)

| Mã | Việc |
|---|---|
| **H9.1** | Học lại DR-learner trên luật cũ của W0 và W1 (`uplift.py`); xuất hàm điểm theo mỗi 1.000đ (việc 3.1) |
| **H9.2** | Chọn chỉ số độ căng (`tension.py`) trên W0 và W1: `ring1`, `system` (= `scope: city`), `hour` và các ứng viên cũ (việc 3.2) |
| **H9.3** | Ngưỡng theo độ căng (`theta.py`, `estimate.py`; việc 3.3): chia khối switchback toàn thành phố theo **độ căng trước khối**; đường tác dụng theo độ căng, đủ các nhóm, có khoảng tin cậy; ngưỡng mới; giữ ngưỡng theo giờ (A) và (B) để so; **so phân bố độ căng khi không voucher và khi chính sách chạy** |
| **H9.4** (cũ T9.1) | Hàm điểm "tắt cố định ở các giờ voucher có hại": trả NaN ở các giờ có τ̂(h) < 0 (từ H9.3), θ = 0; cũng là tầng vùng `hour` của Q6 (việc 4.1) |
| **H9.5** (cũ T9.2) | Bảng thác nước ba nguồn sai số (`interference.py`), các phần cộng lại phải khớp (việc 4.4): gây nhiễu (so thô − mốc không gây nhiễu, `confounding.py`); tranh chấp xe (mức trên mỗi khách so với GTE); công suất (GTE đội xe mặc định so với GTE đội xe rất lớn) |
| **H9.6** (cũ T9.3) | Tách burn-in bias khỏi ảnh hưởng kéo dài: từ dữ liệu bật/tắt toàn bộ, tác dụng trên phút 15–60 mỗi giờ so với GTE, có khoảng tin cậy (việc 4.5) |
| **H9.7** | Gói **B12** cho W0 và W1: hàm điểm mới (DR-learner theo 1.000đ, tắt theo giờ), chỉ số độ căng đã chọn, ngưỡng mới và cũ, danh sách giờ có hại, bảng thác nước, bảng burn-in; mọi thứ nạp được trong tiến trình con, tất định |

**Kiểm tra cuối S9 (G9):**
- Có hình đường tác dụng theo độ căng với khoảng tin cậy (tiêu chí 1), và ngưỡng có khoảng tin cậy.
- Bảng thác nước cộng lại khớp; bảng burn-in có khoảng tin cậy.
- Test của mọi code phân tích mới pass.
- Giao **B12** (Hoàng → Tình); Tình kiểm: nạp được trong tiến trình con, chạy hai lần cho cùng số.

### Sprint 10 (Tình): Thí nghiệm đánh giá và code animation (Giai đoạn 4)

Ngân sách máy ~8,5 giờ với 8 lõi (ĐX mục E): chạy T10.1, T10.2, T10.5, T10.8 qua đêm theo thứ tự đó, mọi lệnh có `--set runner.n_procs=8`, thời gian thật ghi vào `datasets.md`. Code animation (T10.10) làm trong lúc máy chạy.

| Mã | Việc |
|---|---|
| **T10.1** | Bảng chính sách mở rộng trên **W0 và W1** (việc 4.1, Q4–6, Q21): các chính sách cũ, ngưỡng theo độ căng, ngưỡng theo giờ, luật tắt cố định theo giờ, tầng vùng `city`, oracle. Báo **tỷ lệ khoảng cách `all_on` → oracle đã lấp** và giới hạn của oracle |
| **T10.2** | Quét θ (16 mức × 30 seed; đặt `sweep.theta_grid` 16 mức, `n_seeds = 30`) trên W0 và W1; chọn ngưỡng tốt nhất trên nửa seed, đo regret trên nửa còn lại; báo "% lợi ích tối đa của tầng vùng lấy lại được" (việc 4.2, Q2, Q18) |
| **T10.3** | Số lần bật/tắt ở chính sách khuyến nghị; đề xuất thời gian giữ trạng thái (việc 4.3, Q7) |
| **T10.4** | Qini (`qini_vs_value.py`; việc 4.6, Q3, Q11–13): tương quan trong nhóm hàm theo mỗi 1.000đ; Qini có tính chi phí; giải thích vì sao "chuyến thêm / 100.000đ" khớp; tìm ví dụ Qini và số chuyến lệch nhau **do cung** trên W1 |
| **T10.5** | Độ vững trên W1: B ∈ {0,3; 0,6; 1,0} × số xe {100%; 83%; 67%} với chính sách khuyến nghị; bảng chính sách trên 3 `world_seed` (việc 4.8, Q18, Q19) |
| **T10.6** (cũ H10.1) | Hai kiểm tra nhỏ (việc 4.7, Q16, Q20): điều chỉnh theo đặc trưng so với so thô **trên đúng mốc**; tỷ lệ bỏ chờ; **tác hại 7–8h trước và sau khi sửa lịch ca** |
| **T10.7** (cũ H10.2) | Gây nhiễu và độ nhạy theo `u` trên dữ liệu mới (`confounding.py`): tách so thô, ghi rõ mốc của từng ước lượng |
| **T10.8** (cũ H10.4) | Độ nhạy theo giả định thiếu số liệu Hà Nội (việc 4.8b, ĐX D3), **bắt buộc**, không phải phụ: chính sách khuyến nghị và các chính sách so sánh dưới cầu theo giờ cũ và NYC TLC; hazard hủy ×0,5 / ×1 / ×2 (kiểm P1); quãng đường TB ~5 và ~8 km; thêm `max_idle_min = 20` nếu S8 báo điều chuyển > 15% giờ-xe. Báo θ\* và chênh lệch có đổi không |
| **T10.9** (cũ H10.3 + T10.6) | Chạy lại notebook 01–05 trên dữ liệu mới: thêm thác nước, burn-in; đổi nhãn tiền sang VND; sửa chữ "hiệu ứng thật" thành "mốc không gây nhiễu"/"ATE" |
| **T10.10** (cũ T9.4) | Code animation `analysis/animation.py` theo mục 6 của hướng dẫn mentor (việc 5.5): lục giác bằng `RegularPolygon`, tọa độ từ `dashboard.geometry.axial_to_xy`; `completed_by_request_slot`; ba bản đồ + đường ΔN cộng dồn có dải tin cậy; thang màu cố định, đối xứng, an toàn cho người mù màu; thanh màu; chú thích theo khung. Test trên dữ liệu nhỏ: ma trận đúng `[n_slot, 61]`, tổng Δ khớp |

**Kiểm tra cuối S10 (G10):**
- Mọi bảng kết quả nằm trong `runs/` và có lệnh trong `datasets.md`.
- Notebook 01–05 "Restart & Run All" sạch; hình xuất vào `docs/figures/`.
- Chênh lệch ghép cặp có khoảng tin cậy; animation chạy được trên dữ liệu nhỏ.
- Kết luận giả thuyết H1/H2 và ba dự đoán P1–P3 (đúng/sai, kèm số và khoảng tin cậy), cùng kết quả độ nhạy T10.8, được ghi vào `decisions.md`.
- Hoàng review PR S10 (**B13**: bảng kết quả cho báo cáo); S11 cùng người làm nên không có bàn giao.

### Sprint 11 (Tình): Báo cáo, animation bản cuối, trả lời mentor (Giai đoạn 5)

| Mã | Việc |
|---|---|
| **T11.1** | Animation bản cuối (việc 5.5): cặp `all_on` có ngân sách và chính sách khuyến nghị; cùng seed, cùng B, `--log-level full`, 10 seed; khung 5h–9h, và một bản khung có sự kiện trên W1 (chọn ngày theo `meta/shocks`; không có trong 10 seed thì ép sự kiện bằng `--set shocks.events.venues=...` xác suất 1, ghi rõ trong `datasets.md` và chú thích slide), khoảng 1 giây/slot, dừng 2 giây ở cuối; ghi lệnh vào `datasets.md`, chạy `check_dataset`; `notebooks/06_animation.ipynb`; slide ghi "trong mô phỏng này", cặp chính sách, số seed, B (VND); kiểm đủ **8 mục** ở mục 8 của hướng dẫn |
| **T11.2** (cũ H11.1) | Chương 3 và Phụ lục A (việc 5.1): quy mô Hà Nội (H3 độ phân giải 7, 315 km², TomTom), giá cước VND theo GrabCar, biến động, phương pháp ngưỡng theo độ căng; Phụ lục A ghi nguồn từng tham số theo ĐX; Bảng 4.1 dòng "Lưới" và các dòng tiền; sửa lỗi `\noalign` ở `phuluc.tex`; số trang Castillo 2017 |
| **T11.3** (cũ T11.2 + H11.2) | Chương 4 toàn bộ: RQ1 với đường tác dụng theo độ căng, chọn chỉ số độ căng, ngưỡng, gây nhiễu, tác hại 7–8h trước/sau khi sửa lịch ca, độ nhạy giả định; bảng chính sách W0/W1, quét θ, Qini, thiết kế thí nghiệm, thác nước, burn-in, độ vững; Phụ lục D |
| **T11.4** (cũ T11.3 + H11.3) | File trả lời mentor Q1–Q27 (việc 5.4b): mỗi câu 1–3 câu, có số, trỏ mục báo cáo; câu không làm (Q22 nếu bỏ 4.9) ghi rõ lý do |
| **T11.5** (cũ T11.4/H11.4) | Tóm tắt, mở đầu (đóng góp), trả lời RQ, Chương 5, hạn chế, theo nguyên tắc viết số (việc 5.2–5.4) |

**Hoàng trong S11 (H11.R):** review chéo từng chương ngay khi Tình đẩy lên, kiểm mọi con số truy về `runs/` qua `datasets.md`, kiểm Phụ lục A khớp ĐX, biên dịch LaTeX. Không viết phần mới; sửa nhỏ thì sửa thẳng và ghi trong PR.

**Kiểm tra cuối S11 (G11, hoàn thành toàn bộ):** xem mục 7.

---

## 4. Bàn giao

| ID | Từ → Đến | Nội dung | Khi | Người nhận kiểm tra |
|---|---|---|---|---|
| B9 | Hoàng → Tình (duyệt) | PR hợp đồng: khóa config, VND, luồng `SHOCK`, cột schema, mốc G7 sinh lại | đầu S7 | `pytest -q`; bảng tương đương đơn vị; G7 pass |
| B10 | Hoàng → Tình | simulator đã sửa xong S7 (việc 1.0–1.5), PR S7 | cuối S7 | hồi quy G7; CRN khi bật biến động; A5 Hà Nội; test giá 83.638đ; oracle chỉ với chính sách ngưỡng |
| B11 | Tình → Hoàng | `default.yaml` hiệu chỉnh (W0), `world_w1.yaml`, toàn bộ dữ liệu, `datasets.md` | cuối S8 | A1, A2, A5, CAL đạt; `check_dataset` pass; `config_hash` khớp |
| B12 | Hoàng → Tình | hàm điểm, chỉ số độ căng, ngưỡng mới/cũ, giờ có hại, thác nước, burn-in | cuối S9 | nạp được trong tiến trình con; tất định; thác nước cộng khớp |
| B13 | Tình → Hoàng (review) | bảng chính sách, quét θ, độ vững, độ nhạy, notebook 01–05, animation chạy được | cuối S10 | số khớp `runs/`; notebook chạy sạch |
| B14 | Tình → Hoàng (review) | báo cáo, animation, file trả lời mentor | cuối S11 | mục 7 |

---

## 5. Thứ tự

```
S7  (Hoàng): B9 → H7.1 (đo A5 sớm) → H7.2, H7.3, H7.4 → H7.5 → H7.6, H7.7, H7.8 → G7 → B10
S8  (Tình):  T8.1 → T8.2, T8.3 → T8.4 → T8.5, T8.6 → G8 → B11
S9  (Hoàng): H9.1 → H9.2 → H9.3 → H9.4; H9.5, H9.6 song song → H9.7 → G9 → B12
S10 (Tình):  T10.1 → T10.2, T10.3, T10.5; T10.4, T10.6–T10.8 song song; T10.10 bất kỳ lúc nào → T10.9 → G10 → B13
S11 (Tình):  T11.1 ∥ T11.2 → T11.3 → T11.4 → T11.5 → G11 → B14
```

**Việc chuẩn bị của người đang chờ** (không đụng file của sprint đang mở; commit trên nhánh mình, PR sau khi sprint kia gộp):
- Tình trong S7: script hiệu chỉnh đọc `calibration_targets` và in bảng 9 chỉ tiêu từ một lượt `all_off`/`all_on` (dùng `analysis/validation.py`, cột tiền theo tên mới sau B9); khung `analysis/animation.py` chạy trên dữ liệu giả 61 ô; mở rộng `analysis/policy_table.py` cho `city`, oracle, luật tắt theo giờ; mẫu `datasets.md` cho W0/W1. Review B9 và PR S7 trong một ngày làm việc.
- Hoàng trong S8: đọc lại `uplift.py`, `theta.py`, `estimate.py` với cột tiền mới; viết sẵn test cho đường tác dụng theo độ căng trên dữ liệu giả. Review bảng hiệu chỉnh của T8.1 theo thứ tự ưu tiên ĐX mục C.
- Hoàng trong S10, S11: đọc bản nháp báo cáo bản 2 và danh sách Q1–Q27 để review chéo nhanh; kiểm số trong báo cáo truy về `runs/`.

---

## 6. Việc có điều kiện (chỉ làm khi mentor yêu cầu)

- **4.9** Thêm giá và độ dài chuyến vào mô hình hiệu ứng và chi phí (thuộc S9, Hoàng). Nếu không làm, Q22 trả lời rõ lý do.
- **5.6** Trang so sánh chính sách trên dashboard (thuộc S11, Tình), tách riêng khỏi animation.

---

## 7. Điều kiện hoàn thành toàn bộ (G11)

- Báo cáo biên dịch không lỗi, không tham chiếu hay trích dẫn hỏng.
- Mọi con số trong báo cáo truy được về `runs/` qua `datasets.md`; áp đủ nguyên tắc viết số ở việc 5.2; tiền ghi bằng VND.
- Mọi tham số trong Phụ lục A có nguồn theo ĐX.
- File trả lời mentor có đủ Q1–Q27.
- Animation đạt 8 mục kiểm tra của hướng dẫn.
- `pytest -q` và `pytest -q -m slow` pass.
- PR `develop1`/`develop2` → `develop`; gộp `develop → main`; gắn tag bản cuối.

---

## 8. Đối chiếu với `docs/ke_hoach_sua_v3.md`

| Việc | Task | Việc | Task |
|---|---|---|---|
| 1.0 | H7.1 | 4.1 | H9.4, T10.1 |
| 1.0b | B9 (đổi tên, khóa), H7.8 (công thức, giá trị) | 4.2 | T10.2 |
| 1.1 | H7.2 | 4.3 | T10.3 |
| 1.2 | H7.3 | 4.4 | H9.5 |
| 1.3 | T7.1 ✅ | 4.5 | H9.6 |
| 1.4 | H7.4, H7.5 | 4.6 | T10.4 |
| 1.5 | T7.2 ✅, T7.3 ✅, H7.6, H7.7 | 4.7 | T10.6 |
| 1.6 | G7 | 4.8 | T10.5 |
| 1.7 | T8.1–T8.3 | 4.8b | T10.8 |
| 2.1 | T8.4–T8.6 | 4.9 | có điều kiện (mục 6) |
| 3.1 | H9.1 | 5.1 | T11.2, T11.3 |
| 3.2 | H9.2 | 5.2–5.4 | T11.5 |
| 3.3 | H9.3 | 5.4b | T11.4 |
| | | 5.5 | T10.10, T11.1 |
| | | 5.6 | có điều kiện (mục 6) |
