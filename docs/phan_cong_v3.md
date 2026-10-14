# Phân công theo sprint: bản sửa cuối sau review bản 2

Người làm: **1. Phan Văn Tình**, **2. Nguyễn Huy Hoàng**. Người hướng dẫn: Nguyễn Bảo Long.

Phạm vi: Giai đoạn 1–5 của `docs/ke_hoach_sua_v3.md`. Giai đoạn 0 (sửa báo cáo không phụ thuộc số liệu) đã xong. Đây là lần sửa cuối, cho ra sản phẩm cuối cùng.

Giá trị và nguồn của mọi tham số: **`docs/de_xuat_tham_so_ha_noi.md` (ĐX)**. Task nào đặt giá trị tham số thì lấy đúng số trong ĐX; muốn đổi thì sửa ĐX trước (cả hai duyệt).

Quyết định đã chốt:
- **Quy mô Hà Nội:** ô H3 độ phân giải 7 (5,16 km²), thành phố bán kính 4 (61 ô, 315 km²), tốc độ theo TomTom Hà Nội (ĐX mục B1).
- **Tiền VND, giá cước theo GrabCar Hà Nội**, voucher 25% tối đa 20.000đ (ĐX mục B4). Chỉ mô phỏng ô tô 4 chỗ.
- **Animation do Tình làm**, tách riêng khỏi dashboard, theo đủ `huong-dan-animation-chinh-sach.md`.
- Việc 1.4 làm **đủ 5 loại biến động**, với giá trị ở ĐX mục B5.
- Việc 4.9 và 5.6 **chỉ làm nếu mentor yêu cầu** (mục 6).
- Không giới hạn thời gian: làm đủ mọi việc, không cắt.

Quy ước ký hiệu:
- `T7.1` là task của Tình, `H7.1` là task của Hoàng (số đầu = sprint). Sprint đánh số tiếp theo bản cũ (**S7–S11**), để mã task không trùng với T1.x–T6.x, H1.x–H6.x trong `docs/log.md`.
- `B9`–`B15` là các điểm bàn giao (nối tiếp B0–B8); `G7`–`G11` là kiểm tra cuối sprint.
- `W0` là thế giới không biến động; `W1` là thế giới có biến động (overlay `config/world_w1.yaml`).
- `Q..` là câu hỏi của mentor ở Phần I của `Report_version2_review.md`; `KN` là `khuyen-nghi-code-simulator.md`. Hai file này và `huong-dan-animation-chinh-sach.md` do mentor gửi riêng, không lưu trong repo.

**Trạng thái ngày 14/10:**
- Đã gộp vào `develop` (PR #23, Tình): T7.1 và bộ kiểm hồi quy G7 (`tests/test_regression_s7.py`, T-39).
- Bản nháp code của B9 (phần khóa mô hình, luồng `SHOCK`, cột schema, chỉ tiêu tỷ lệ xe bận) nằm trên `develop2`, chưa commit. Còn thiếu: phần VND, khóa giá cước, danh sách địa điểm sự kiện.

---

## 1. Nguyên tắc và Git

1. **Hợp đồng trước:** đầu S7, PR chung B9 chốt mọi tên khóa config, tên cột, luồng ngẫu nhiên, và đổi tên tiền sang VND. Sau B9, mỗi người code phía mình mà không phải đổi tên nữa.
2. **Mặc định trong B9 bằng hành vi cũ.**
   - Khóa nào làm đổi mô hình thì trong B9 có mặc định cho ra đúng kết quả cũ. Khóa nào chưa cài mà bị đặt giá trị mới thì code báo `NotImplementedError`, không chạy lặng lẽ mô hình cũ.
   - Task cài khóa nào thì đổi mặc định của khóa đó sang giá trị mới. Giá trị Hà Nội vào ở H7.1, T7.6, H7.4.
3. **Mỗi file một chủ** (mục 2). File chung chỉ sửa qua PR có cả hai duyệt. Cần sửa file của người kia thì mở PR nhỏ để chủ file review.
4. **Sprint xong mới sang sprint sau:** xong hết task thì chạy mục "Kiểm tra cuối sprint"; đạt thì ghi log gate rồi mới sang sprint tiếp. Không đạt thì báo số liệu, ghi log, không nới tiêu chí.
5. Mọi thay đổi đụng `sim/`, `config.py`, `rng.py`, `schema.md` cần mục `docs/decisions.md` (ID `H-`/`T-`), mục log, và PR có chủ file duyệt (theo `CLAUDE.md`).

**Git:**
- Trước mỗi task: kéo `develop` về `develop1` (Tình) / `develop2` (Hoàng).
- Mỗi task một commit, kèm mục log trong `docs/log.md` (mục của người làm). Mô tả PR chép từ mục log của task.
- Xong các task của sprint: mở một PR từ nhánh của mình vào `develop`, người kia review, gộp bằng merge commit (không squash). Bàn giao người kia đang chờ thì PR sớm, không đợi hết sprint.
- Cuối S11: gộp `develop → main` và gắn tag bản cuối.

---

## 2. Sở hữu file

Giữ nguyên bảng sở hữu ở mục 2 của `docs/phan_cong.md`. Thêm:

| | 1. Tình | 2. Hoàng |
|---|---|---|
| Mã mới | `analysis/animation.py`, `notebooks/06_animation.ipynb` | `sim/shocks.py`, `config/world_w1.yaml` |
| Giá trị trong `default.yaml` | `pricing`, `voucher`, `budget`, `policy`, `experiment`, `monitor`, `sweep`, `generate`, `gte` | `space`, `time`, `demand`, `riders`, `matching`, `cancel`, `supply`, `reposition`, `shocks` |
| `analysis/` | `policy_table.py`, `qini_vs_value.py`, `interference.py`, `metrics.py`, `validation.py`, `figures.py`, `score_ties.py`, `check_dataset.py`, `io.py`; notebook 01–03; `dashboard/` | `uplift.py`, `theta.py`, `estimate.py`, `tension.py`, `confounding.py`, `scores.py`, `notebook.py`, `tlc_hourly.py`; notebook 04–05 |
| Báo cáo LaTeX | Chương 4 phần chính sách, quét θ, Qini, thiết kế thí nghiệm, thác nước, burn-in, độ vững; Phụ lục D phần liên quan | Chương 3; Chương 4 phần RQ1, chỉ số độ căng, ngưỡng, gây nhiễu, độ nhạy giả định; Phụ lục A |

**Chung (PR cả hai duyệt):**
- khóa mới trong `config.py`/`default.yaml`; `rng.py`; `schema.md`; `tests.md`; `calibration_targets`;
- `tests/fixtures/regression_s7*`;
- `docs/de_xuat_tham_so_ha_noi.md`;
- Tóm tắt, mở đầu và Chương 5 viết chung.

---

## 3. Các sprint

### Sprint 7: Sửa simulator (Giai đoạn 1)

**Đầu S7: PR hợp đồng B9** (Hoàng soạn tiếp từ bản nháp trên `develop2`, Tình duyệt).

1. **Khóa mô hình**, mặc định bằng hành vi cũ:
   - `matching.ring_tiebreak: lowest_id | most_idle` (B9: `lowest_id`);
   - `cancel.exact_time: bool` (B9: `false`);
   - `policy.threshold.scope` thêm `city`;
   - tên hàm điểm `oracle` (giữ chỗ);
   - mục `shocks:` gồm:
     - `enabled` (B9: `false`);
     - `day_demand.sigma`;
     - `events.venues` (danh sách loại địa điểm, ĐX mục B5);
     - `rain.*`, `attendance.p_work`, `shift_jitter.sd_min`.
2. **Tiền VND** (việc 1.0b):
   - đổi tên `_usd` → `_vnd`, `cents` → đồng nguyên trên toàn repo bằng một script tìm–thay (~1.150 chỗ, 79 file);
   - khóa giá mới: `pricing.open_fare_vnd`, `open_km`, `per_km_vnd`, `per_min_vnd`, `platform_fee_vnd`; `voucher.max_vnd`; `riders.beta_price_per_kvnd`;
   - bỏ `pricing.target_mean_fare_usd`;
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

     Các khóa khác giữ giá trị hiện tại.

   - công thức theo km và phí nền tảng chưa cài: đặt `open_km`, `per_km_vnd` hoặc `platform_fee_vnd` khác 0 thì báo `NotImplementedError` cho tới T7.6.
3. **`calibration_targets`:**
   - thêm `busy_rel_h6/h7/h8`, `mean_trip_km` [5; 8], `trips_per_driver_day` [8; 18];
   - bỏ `mean_gross_fare_usd`;
   - cách tính viết luôn trong `tests/test_acceptance_core.py` (Hoàng) và `analysis/validation.py` (Tình);
   - từ B9 tới H8.1, test CAL chậm sẽ không đạt vì có chỉ tiêu mới chưa hiệu chỉnh. Ghi log, không nới dải.
4. **`rng.py`:** luồng `SHOCK = 8`, mã `ShockKind`; `WorldPart.VENUES = 4`. Không đánh số lại mã cũ.
5. **`schema.md`:**
   - cột tiền đổi `_vnd`;
   - session: `lag_slot_same_block`; nghĩa mới của `slack_hat` (mọi chính sách);
   - `run_metadata`: `budget_pilot_seed`, `budget_pilot_spent_vnd`, `hidden_view`;
   - `policy_results`: `world_seed`;
   - bảng mới `meta/shocks`.
6. **Kiểm tương đương đơn vị:**
   - chạy 4 lượt của bộ kiểm hồi quy G7 bằng code trước và sau B9;
   - số chuyến, số request, số hủy phải trùng; cột tiền khớp ×100 trong sai số 1e-6;
   - đạt thì viết lại `regression_s7_pinned.yaml` theo khóa mới và **sinh lại `regression_s7.json` một lần** (đính chính T-39 b).
7. **`decisions.md`** (đánh số tiếp từ H-28):
   - khóa mô hình;
   - biến động và luồng `SHOCK`;
   - chỉ tiêu hiệu chỉnh (đính chính một phần H-20);
   - cột schema;
   - quy mô Hà Nội và tiền VND (trỏ tới ĐX);
   - đính chính T-39 b;
   - hai giả thuyết ghi trước khi chạy: (H1) W0: chính sách theo độ căng ngang luật tắt theo giờ; (H2) W1: chính sách theo độ căng thắng.

**Task S7:**

| Tình | Hoàng |
|---|---|
| **T7.1** ✅ Chặn độ căng dự báo ở `slack_cap` cho mọi nhánh (`threshold.py`) + test; bộ kiểm hồi quy G7 (việc 1.3; PR #23) | **H7.1** Quy mô Hà Nội (việc 1.0, ĐX B1–B3). Giá trị: `edge_km = 1.41`, `grid_radius = 4`, `speed_factor_by_hour` theo TomTom, ca 11,2 giờ (sd 2,0, chặn [4, 14]), `fleet_size = 1000`, `base_sessions_per_cell_h = 124`, `dest_decay_rings = 1.2`. Sửa test kiểm cứng 37 ô (`test_engine.py`) và kích thước cụm 7 ô (`test_space.py`). **Đo A5 ngay** trên cấu hình mới, báo nếu vượt 30 giây/ngày |
| **T7.2** Phạm vi `city` cho tầng vùng (`threshold.py`, ma trận vành toàn 1) + test: mọi ô cùng một quyết định (việc 1.5) | **H7.2** Luật chọn xe vành ngoài: khi hòa lấy ô nhiều xe rảnh nhất (`space.find_pickup`); ETA báo giá và lúc ghép dùng chung luật. Test thế giới đối xứng: tương quan `cell_id`–số lần làm ô nguồn ≈ 0. Đổi mặc định `ring_tiebreak` sang `most_idle` (việc 1.1) |
| **T7.3** Chính sách oracle: `OracleHiddenView` (theo mẫu `LegacyHiddenView`), hàm điểm oracle trong `sim/policies/scores.py` (điểm = chuyến thêm trên mỗi 1.000đ), chặn dùng ngoài chính sách ngưỡng, `hidden_view = oracle`. Test: `SessionBatch` vẫn không có cột ẩn (việc 1.5, KN 3.1) | **H7.3** Hủy đúng thời điểm: tính `t_cancel = t_ghép + 60·e/h`; ở bước 1, nếu `t_cancel < t_đón` thì hủy thay vì đón, xe rảnh theo luật nửa ETA (`trips.py`, `cancel.py`); không rút thêm số. Test so với hazard chính xác, nhả ngân sách đúng. Đổi mặc định `exact_time` sang `true` (việc 1.2) |
| **T7.4** Ghi độ căng trễ (`slack_hat`) cho chính sách thí nghiệm và luật cũ, cờ `lag_slot_same_block` (`policies/experiment.py`, `legacy.py`, `logger.py`); test không nhìn trước (việc 1.5, KN 3.3) | **H7.4** Biến động tự nhiên (việc 1.4, ĐX B5). Code: `sim/shocks.py` mới; `demand.py`, `supply.py`; tốc độ khi mưa trong `space.py`/`matching.py`/`trips.py`. Gồm: cầu theo ngày (σ 0,12); hai loại địa điểm sự kiện; mưa (p 0,31, 14–19h, cầu ×1,25, tốc độ ×0,85, 10% tài xế nghỉ); tài xế đi làm 90%; giờ vào ca lệch 20 phút. Lịch rút trước theo ngày qua luồng `SHOCK`; chính sách không đọc được |
| **T7.5** `runner.py`: điền `budget_pilot_spent_vnd`; `logger.py`: ghi bảng `meta/shocks` (việc 1.5, Q23) | **H7.5** Test cho H7.4: tắt biến động thì trùng từng số với mốc G7; cùng ngày cùng biến động dưới mọi chính sách; độ lớn biến động đúng tham số (tần suất mưa, sự kiện; hệ số cầu, tốc độ) |
| **T7.6** Giá cước Hà Nội (việc 1.0b, ĐX B4). Code (`pricing.py`): giá = 28.473đ (2 km đầu) + 9.818đ/km + 442đ/phút sau 2 km + phí nền tảng 10.000đ (thuộc nền tảng, cộng vào lợi nhuận); voucher 25% tối đa 20.000đ. Giá trị `commission_rate = 0.25`. Đề xuất `riders.beta_price_per_kvnd = 0.022` trong cùng PR (Hoàng duyệt khóa `riders`). Test: chuyến 6 km 20 phút ≈ 83.638đ; voucher chạm trần; bất biến sổ ngân sách bằng đồng nguyên. Đổi nhãn tiền trên dashboard | |

**Kiểm tra cuối S7 (G7, việc 1.6):**
- `pytest -q` toàn bộ pass.
- **Hồi quy:** với `regression_s7_pinned.yaml` (giá trị cũ theo đơn vị mới), đầu ra 1 ngày trùng từng số với mốc sinh lại ở B9.
- Không rò biến ẩn (`test_no_hidden_leak`), không nhìn trước, bất biến ngân sách, số ngẫu nhiên chung giữa các chính sách khi bật biến động.
- **A5:** ≤ 30 giây/ngày trên cấu hình Hà Nội (61 ô, ~1.000 xe).
- **Kiểm giá:** giá trung bình một chuyến và voucher trung bình trên `all_on` 1 ngày nằm cùng bậc với ĐX (chuyến ~6 km ≈ 84.000đ, voucher ≈ 20.000đ).
- Giao **B10** (Hoàng → Tình) và **B11** (Tình → Hoàng); PR S7 vào `develop`.

### Sprint 8: Hiệu chỉnh và sinh dữ liệu (việc 1.7, Giai đoạn 2)

Trong S8 **chỉ Hoàng sửa giá trị** `default.yaml` (như S3 cũ).

| Tình | Hoàng |
|---|---|
| **T8.1** Sau B12: `calibrate_budget` cho W0 và W1, rồi sinh dữ liệu cho **mỗi** thế giới (việc 2.1; máy chạy ước 3–4 giờ cho cả hai):<br>• luật cũ 28 ngày;<br>• luật cũ 4 mức nhắm theo `u` (độ nhạy);<br>• switchback 1 ô, 7 ô, toàn thành phố, 28 ngày;<br>• A/B theo khách 28 ngày;<br>• GTE 10 seed;<br>• **GTE với đội xe rất lớn**;<br>• bật/tắt toàn bộ 5 seed, ghi đầy đủ | **H8.1** Hiệu chỉnh trên W0 (việc 1.7, ĐX mục C).<br>• Núm: `fleet_size`, `demand_scale`, `shift_start_mixture`, `dest_decay_rings`, `alpha0`, `delta0`.<br>• Chỉ tiêu: P(đặt) 13–17%; mức tăng +35–70%; (ô, slot) căng 10–35%, dư 30–80%; tỷ lệ xe bận 6/7/8h theo NYC; quãng đường TB 5–8 km; 8–18 chuyến/tài xế/ngày.<br>• Báo kèm: thời gian chờ đón TB (3–8 phút), thời gian chuyến TB (15–25 phút), tỷ lệ hủy và bỏ chờ.<br>• Ghi bảng hiệu chỉnh vào `decisions.md`; `config_hash` mới |
| **T8.2** Ghi lệnh vào `docs/datasets.md`; chạy `check_dataset` (schema + không rò biến ẩn) trên mọi bộ → giao **B13** (việc 2.1) | **H8.2** A1 (đường throughput) và A5 trên cấu hình đã hiệu chỉnh; cập nhật test CAL và `tests.md` cho các chỉ tiêu mới (việc 1.7) |
| **T8.3** A2 (số ngẫu nhiên chung) trên code mới; kiểm `analysis/validation.py` cho ra các chỉ tiêu CAL mới khớp test chậm | **H8.3** `config/world_w1.yaml`: bật biến động với giá trị ĐX B5; `fleet_size` của W1 = W0 / 0,90 để số xe trung bình bằng W0. Báo các chỉ tiêu thị trường của W1 (không hiệu chỉnh lại W1) → giao **B12** (cấu hình W0 + overlay W1) |

**Kiểm tra cuối S8 (G8):**
- A1, A2, A5 và mọi chỉ tiêu CAL đạt trên W0; chỉ tiêu của W1 được ghi lại.
- Thời gian chờ đón và thời gian chuyến trung bình nằm trong khoảng kiểm ở ĐX mục C. Lệch thì ghi hạn chế, không chỉnh theo.
- Mọi bộ dữ liệu qua `check_dataset`; `config_hash` khớp `datasets.md`.
- **Biến động có tác dụng:** trên W1, tỷ lệ (ô, slot) căng **ngoài 5–8h** tăng rõ so với W0.

### Sprint 9: Phương pháp (Giai đoạn 3) và chuẩn bị đánh giá

| Tình | Hoàng |
|---|---|
| **T9.1** Hàm điểm "tắt cố định ở các giờ voucher có hại": trả NaN ở các giờ có τ̂(h) < 0 (lấy từ H9.3), θ = 0. Đây cũng là tầng vùng `hour` của Q6 (việc 4.1) | **H9.1** Học lại DR-learner trên luật cũ của W0 và W1 (`uplift.py`); xuất hàm điểm theo mỗi 1.000đ (việc 3.1) |
| **T9.2** Code bảng thác nước ba nguồn sai số (`interference.py`), các phần cộng lại phải khớp (việc 4.4):<br>• gây nhiễu: so thô − mốc không gây nhiễu, gọi `confounding.py` của Hoàng;<br>• tranh chấp xe: mức trên mỗi khách so với GTE;<br>• công suất: GTE đội xe mặc định so với GTE đội xe rất lớn | **H9.2** Chọn chỉ số độ căng (`tension.py`) trên W0 và W1: `ring1`, `system`, `hour` và các ứng viên cũ (việc 3.2) |
| **T9.3** Tách burn-in bias khỏi ảnh hưởng kéo dài: từ dữ liệu bật/tắt toàn bộ, tính tác dụng trên phút 15–60 mỗi giờ, so với GTE, có khoảng tin cậy (việc 4.5) | **H9.3** Ngưỡng theo độ căng (`theta.py`, `estimate.py`; việc 3.3):<br>• chia khối switchback toàn thành phố theo **độ căng trước khối**;<br>• đường tác dụng theo độ căng, đủ các nhóm, có khoảng tin cậy;<br>• ngưỡng mới; giữ ngưỡng theo giờ (A) và (B) để so;<br>• **so phân bố độ căng khi không voucher và khi chính sách chạy** |
| **T9.4** Code animation `analysis/animation.py` theo đúng mục 6 của hướng dẫn mentor (việc 5.5):<br>• lục giác bằng `RegularPolygon`, tọa độ từ `dashboard.geometry.axial_to_xy`;<br>• `completed_by_request_slot`;<br>• ba bản đồ + đường ΔN cộng dồn có dải tin cậy;<br>• thang màu cố định, đối xứng, an toàn cho người mù màu; thanh màu; chú thích theo khung;<br>• test trên dữ liệu nhỏ: ma trận đúng `[n_slot, 61]`, tổng Δ khớp | **H9.4** Giao **B14** cho W0 và W1: hàm điểm mới, chỉ số độ căng đã chọn, ngưỡng mới và cũ, danh sách giờ có hại |

**Kiểm tra cuối S9 (G9):**
- Có hình đường tác dụng theo độ căng với khoảng tin cậy (tiêu chí 1), và ngưỡng có khoảng tin cậy.
- Test của mọi code phân tích mới pass; animation chạy được trên dữ liệu nhỏ.
- B14 đã giao; Tình kiểm tra nạp được trong tiến trình con.

### Sprint 10: Thí nghiệm đánh giá (Giai đoạn 4)

| Tình | Hoàng |
|---|---|
| **T10.1** Bảng chính sách mở rộng trên **W0 và W1** (việc 4.1, Q4–6, Q21). Gồm: các chính sách cũ, ngưỡng theo độ căng, ngưỡng theo giờ, luật tắt cố định theo giờ, tầng vùng `city`, oracle. Báo **tỷ lệ khoảng cách `all_on` → oracle đã lấp** và giới hạn của oracle | **H10.1** Hai kiểm tra nhỏ (việc 4.7, Q16, Q20):<br>• điều chỉnh theo đặc trưng so với so thô **trên đúng mốc**;<br>• tỷ lệ bỏ chờ;<br>• **tác hại 7–8h trước và sau khi sửa lịch ca** |
| **T10.2** Quét θ (16 mức × 30 seed; đặt `sweep.theta_grid` 16 mức, `n_seeds = 30`) trên W0 và W1; chọn ngưỡng tốt nhất trên nửa seed, đo regret trên nửa còn lại; báo "% lợi ích tối đa của tầng vùng lấy lại được" (việc 4.2, Q2, Q18) | **H10.2** Gây nhiễu và độ nhạy theo `u` trên dữ liệu mới (`confounding.py`): tách so thô, ghi rõ mốc của từng ước lượng (kiểu 6,9 hay 7,4 như bản cũ) |
| **T10.3** Số lần bật/tắt ở chính sách khuyến nghị; đề xuất thời gian giữ trạng thái (việc 4.3, Q7) | **H10.3** Chạy lại notebook 04, 05 trên dữ liệu mới; đổi nhãn tiền sang VND; sửa chữ "hiệu ứng thật" trong hình thành "mốc không gây nhiễu"/"ATE" |
| **T10.4** Qini (`qini_vs_value.py`; việc 4.6, Q3, Q11–13):<br>• tương quan trong nhóm hàm theo mỗi 1.000đ;<br>• Qini có tính chi phí;<br>• giải thích vì sao "chuyến thêm / 100.000đ" khớp;<br>• tìm ví dụ Qini và số chuyến lệch nhau **do cung** trên W1 | **H10.4** Độ nhạy theo giả định thiếu số liệu Hà Nội (việc 4.8b, ĐX D3). Chạy chính sách khuyến nghị và các chính sách so sánh dưới:<br>• cầu theo giờ cũ và NYC TLC;<br>• hazard hủy ×0,5 / ×1 / ×2;<br>• quãng đường TB ~5 và ~8 km.<br>Báo θ\* và chênh lệch có đổi không |
| **T10.5** Độ vững trên W1: B ∈ {0,3; 0,6; 1,0} × số xe {100%; 83%; 67%} với chính sách khuyến nghị; bảng chính sách trên 3 `world_seed` (việc 4.8, Q18, Q19) | |
| **T10.6** Chạy lại notebook 01–03 (thêm thác nước, burn-in; đổi nhãn tiền sang VND); giao **B15** (kết quả cho báo cáo và animation) | |

**Kiểm tra cuối S10 (G10):**
- Mọi bảng kết quả nằm trong `runs/` và có lệnh trong `datasets.md`.
- Notebook 01–05 "Restart & Run All" sạch; hình xuất vào `docs/figures/`.
- Bảng thác nước cộng lại khớp; chênh lệch ghép cặp có khoảng tin cậy.
- Kết luận giả thuyết H1/H2 và kết quả độ nhạy H10.4 được ghi vào `decisions.md`.

### Sprint 11: Báo cáo, animation, trả lời mentor (Giai đoạn 5)

| Tình | Hoàng |
|---|---|
| **T11.1** Animation bản cuối (việc 5.5):<br>• cặp `all_on` có ngân sách và chính sách khuyến nghị; cùng seed, cùng B, `--log-level full`, 10 seed;<br>• khung 5h–9h (hoặc khung có sự kiện trên W1, chọn theo `meta/shocks`), khoảng 1 giây/slot, dừng 2 giây ở cuối;<br>• ghi lệnh vào `datasets.md`, chạy `check_dataset`; `notebooks/06_animation.ipynb`;<br>• slide ghi "trong mô phỏng này", cặp chính sách, số seed, B (VND);<br>• kiểm đủ **8 mục** ở mục 8 của hướng dẫn | **H11.1** Báo cáo Chương 3 và Phụ lục A (việc 5.1):<br>• Chương 3: quy mô Hà Nội (H3 độ phân giải 7, 315 km², TomTom), giá cước VND theo GrabCar, biến động, phương pháp ngưỡng theo độ căng;<br>• Phụ lục A: bảng tham số ghi nguồn từng dòng theo ĐX;<br>• Bảng 4.1 dòng "Lưới" và các dòng tiền;<br>• sửa lỗi `\noalign` ở `phuluc.tex`; số trang Castillo 2017 |
| **T11.2** Báo cáo Chương 4 phần của Tình: bảng chính sách W0/W1, quét θ, Qini, thiết kế thí nghiệm, thác nước, burn-in, độ vững; Phụ lục D liên quan (việc 5.1) | **H11.2** Báo cáo Chương 4 phần của Hoàng: RQ1 với đường tác dụng theo độ căng, chọn chỉ số độ căng, ngưỡng, gây nhiễu, tác hại 7–8h trước/sau khi sửa lịch ca, **độ nhạy giả định (H10.4)** (việc 5.1) |
| **T11.3** Trả lời mentor phần của Tình: Q4–6, Q7, Q11–13, Q17–19, Q21 (việc 5.4b) | **H11.3** Trả lời mentor phần của Hoàng: Q8–10, Q14–16, Q20, Q22, Q23–27 (việc 5.4b) |

**Chung (T11.4/H11.4):**
- Trả lời Q1–3 (việc 5.4b).
- Tóm tắt, mở đầu (đóng góp), trả lời RQ, Chương 5 theo nguyên tắc viết số và hạn chế (việc 5.2–5.4).
- Review chéo toàn bộ báo cáo.

**Kiểm tra cuối S11 (G11, hoàn thành toàn bộ):** xem mục 7.

---

## 4. Bàn giao

| ID | Từ → Đến | Nội dung | Khi | Người nhận kiểm tra |
|---|---|---|---|---|
| B9 | Hoàng → Tình (chung) | PR hợp đồng: khóa config, VND, luồng `SHOCK`, cột schema, mốc G7 sinh lại | đầu S7 | `pytest -q`; bảng tương đương đơn vị; G7 pass |
| B10 | Hoàng → Tình | lõi đã sửa (việc 1.0, 1.1, 1.2, 1.4) | cuối S7 | hồi quy G7; số ngẫu nhiên chung khi bật biến động; A5 trên cấu hình Hà Nội |
| B11 | Tình → Hoàng | chính sách và giá cước đã sửa (việc 1.0b, 1.3, 1.5) | cuối S7 | test chính sách, không rò biến ẩn, oracle chỉ chạy với chính sách ngưỡng; test giá 83.638đ |
| B12 | Hoàng → Tình | `default.yaml` đã hiệu chỉnh (W0) + `world_w1.yaml` | giữa S8 | A1, A5, CAL đạt; `config_hash` |
| B13 | Tình → Hoàng | toàn bộ dữ liệu W0, W1 + `datasets.md` | cuối S8 | `check_dataset` pass; `config_hash` khớp |
| B14 | Hoàng → Tình | hàm điểm, chỉ số độ căng, ngưỡng mới/cũ, giờ có hại | cuối S9 | nạp được trong tiến trình con; tất định |
| B15 | Tình → Hoàng | bảng chính sách, quét θ, thác nước, độ vững | cuối S10 | số khớp `runs/`; notebook chạy sạch |

---

## 5. Thứ tự phụ thuộc

```
S7:  B9 → H7.1 (đo A5 sớm) ∥ T7.6 ∥ (T7.2–T7.5 ∥ H7.2–H7.5) → G7, B10, B11
S8:  H8.1 → H8.2, H8.3 → B12 → T8.1 → T8.2 (B13), T8.3 → G8
S9:  H9.1 → H9.2 → H9.3 → H9.4 (B14);  T9.2, T9.3, T9.4 song song;  T9.1 sau H9.3 → G9
S10: T10.1 → T10.2, T10.3, T10.5;  T10.4 ∥ H10.1–H10.4 → T10.6 (B15) → G10
S11: T11.1 ∥ H11.1, H11.2, T11.2 → T11.3, H11.3 → T11.4/H11.4 → G11
```

---

## 6. Việc có điều kiện (chỉ làm khi mentor yêu cầu)

- **4.9** Thêm giá và độ dài chuyến vào mô hình hiệu ứng và chi phí (Hoàng). Nếu không làm, Q22 trả lời rõ lý do.
- **5.6** Trang so sánh chính sách trên dashboard (Tình), tách riêng khỏi animation.

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
| 1.0 | H7.1 | 4.1 | T9.1, T10.1 |
| 1.0b | B9 (đổi tên, khóa), T7.6 (công thức, giá trị) | 4.2 | T10.2 |
| 1.1 | H7.2 | 4.3 | T10.3 |
| 1.2 | H7.3 | 4.4 | T9.2 |
| 1.3 | T7.1 ✅ | 4.5 | T9.3 |
| 1.4 | H7.4, H7.5 | 4.6 | T10.4 |
| 1.5 | T7.2–T7.5 | 4.7 | H10.1 |
| 1.6 | G7 | 4.8 | T10.5 |
| 1.7 | H8.1–H8.3 | 4.8b | H10.4 |
| 2.1 | T8.1, T8.2 | 4.9 | có điều kiện (mục 6) |
| 3.1 | H9.1 | 5.1 | H11.1, T11.2, H11.2 |
| 3.2 | H9.2 | 5.2–5.4 | T11.4/H11.4 |
| 3.3 | H9.3 | 5.4b | T11.3, H11.3, T11.4/H11.4 |
| | | 5.5 | T9.4, T11.1 |
| | | 5.6 | có điều kiện (mục 6) |
