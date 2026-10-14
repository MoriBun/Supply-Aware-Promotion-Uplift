# Phân công theo sprint: bản sửa cuối sau review bản 2

Người làm: **1. Phan Văn Tình**, **2. Nguyễn Huy Hoàng**. Người hướng dẫn: Nguyễn Bảo Long.

Phạm vi: Giai đoạn 1–5 của `ke_hoach_sua_v3.md`. Giai đoạn 0 (sửa báo cáo không phụ thuộc số liệu) đã xong. Đây là lần sửa cuối, cho ra sản phẩm cuối cùng.

Quyết định đã chốt:
- Lưới ô theo **H3 độ phân giải 8** của Uber (việc 1.0).
- **Animation do Tình làm**, tách riêng khỏi dashboard, theo đủ `huong-dan-animation-chinh-sach.md`.
- Việc 1.4 làm **đủ cả phần tùy chọn** (mưa, tài xế nghỉ, giờ vào ca lệch).
- Việc 4.9 và 5.6 **chỉ làm nếu mentor yêu cầu** (mục 6).
- Không giới hạn thời gian: làm đủ mọi việc, không cắt.

Quy ước ký hiệu:
- `T7.1` là task của Tình, `H7.1` là task của Hoàng (số đầu = sprint). Sprint đánh số tiếp theo bản cũ (**S7–S11**) để mã task không trùng với T1.x–T6.x, H1.x–H6.x trong `docs/log.md`;
- `B9`–`B15` là các điểm bàn giao (nối tiếp B0–B8);
- `G7`–`G11` là kiểm tra cuối sprint;
- `W0` là thế giới không biến động, `W1` là thế giới có biến động (overlay `config/world_w1.yaml`);
- `Q..` là câu hỏi của mentor ở Phần I của `Report_version2_review.md`; `KN` là `khuyen-nghi-code-simulator.md`.

---

## 1. Nguyên tắc và Git

1. **Hợp đồng trước:** đầu S7, cả hai cùng làm một PR chung (B9) chốt khóa config, luồng ngẫu nhiên và cột mới, như Sprint 0 cũ. Sau đó mỗi người code phía mình.
2. **Mỗi file một chủ** (mục 2). File chung chỉ sửa qua PR có cả hai duyệt. Cần sửa file của người kia thì mở PR nhỏ để chủ file review.
3. **Sprint xong mới sang sprint sau:** xong hết task thì chạy mục "Kiểm tra cuối sprint"; đạt thì ghi log gate và sang sprint tiếp. Không đạt thì báo số liệu, ghi log, không nới tiêu chí.
4. Mọi thay đổi đụng `sim/`, `config.py`, `rng.py`, `schema.md` cần mục `docs/decisions.md` (ID `H-`/`T-`), mục log, và PR có chủ file duyệt (theo `CLAUDE.md`).

**Git:**
- Trước mỗi task: kéo `develop` về `develop1` (Tình) / `develop2` (Hoàng).
- Mỗi task một commit kèm mục log trong `docs/log.md` (mục của người làm).
- Xong các task của sprint: mở một PR từ nhánh của mình vào `develop`, người kia review, gộp bằng merge commit (không squash). Bàn giao người kia đang chờ thì PR sớm, không đợi hết sprint.
- Mô tả PR chép từ mục log của task.
- Cuối S11: gộp `develop → main` và gắn tag bản cuối.

---

## 2. Sở hữu file

Giữ nguyên bảng sở hữu ở mục 2 của `docs/phan_cong.md`. Thêm:

| | 1. Tình | 2. Hoàng |
|---|---|---|
| Mã mới | `analysis/animation.py`, `notebooks/06_animation.ipynb` | `sim/shocks.py`, `config/world_w1.yaml`, mục `shocks:` trong `default.yaml` |
| `analysis/` | `policy_table.py`, `qini_vs_value.py`, `interference.py`, `metrics.py`, `validation.py`, `figures.py`, `score_ties.py`, `check_dataset.py`, `io.py`; notebook 01–03; `dashboard/` | `uplift.py`, `theta.py`, `estimate.py`, `tension.py`, `confounding.py`, `scores.py`, `notebook.py`, `tlc_hourly.py`; notebook 04–05 |
| Báo cáo LaTeX | Chương 4 phần chính sách, quét θ, Qini, thiết kế thí nghiệm, thác nước, burn-in, độ vững; Phụ lục D phần liên quan | Chương 3; Chương 4 phần RQ1, chỉ số độ căng, ngưỡng, gây nhiễu; Phụ lục A |

**Chung (PR cả hai duyệt):** khóa mới trong `config.py`/`default.yaml`; `rng.py` (luồng `SHOCK = 8`); `schema.md`; `tests.md`; `calibration_targets`. Tóm tắt, mở đầu và Chương 5 viết chung.

---

## 3. Các sprint

### Sprint 7: Sửa simulator (Giai đoạn 1)

**Đầu S7, cả hai: PR hợp đồng (B9).**
- `config.py` + `default.yaml`:
  - `matching.ring_tiebreak: lowest_id | most_idle` (mặc định `most_idle`);
  - `cancel.exact_time: bool` (mặc định `true`);
  - mục `shocks:` (`enabled: false` và tham số của 5 loại biến động);
  - `policy.threshold.scope` thêm giá trị `city`;
  - tên hàm điểm `oracle`;
  - chỉ tiêu `calibration_targets` cho tỷ lệ xe bận theo giờ.
- `rng.py`: luồng `SHOCK = 8` (không đánh số lại luồng cũ).
- `schema.md`:
  - session: cột `slack_lag_slot` cho mọi chính sách, cờ `lag_slot_same_block`;
  - `run_metadata`: thêm `budget_pilot_seed`, `budget_pilot_spent_usd`;
  - `policy_results`: thêm `world_seed`;
  - bảng mới `meta/shocks`.
- `decisions.md`: ghi các khóa mới; bổ sung khóa cho hai giả thuyết H1/H2 (đã ghi ở việc 0.1).

| Tình | Hoàng |
|---|---|
| **T7.1** Chặn độ căng dự báo ở `slack_cap` cho mọi nhánh (`threshold.py`) + test (việc 1.3) | **H7.1** Lưới H3 độ phân giải 8: `space.edge_km = 0.533`, `grid_radius = 4` (61 ô); nhân lượng khách mỗi ô theo tỷ lệ diện tích; sửa `tests/test_engine.py` (đang kiểm cứng 37 ô); kiểm 6 ô kề và kích thước cụm với R = 4 trong `test_space.py` (việc 1.0) |
| **T7.2** Phạm vi `city` cho tầng vùng (`threshold.py`, ma trận vành toàn 1) + test: mọi ô cùng một quyết định (việc 1.5) | **H7.2** Luật chọn xe vành ngoài: khi hòa lấy ô nhiều xe rảnh nhất (`space.find_pickup`); ETA báo giá và lúc ghép dùng chung luật; test thế giới đối xứng: tương quan `cell_id`–số lần làm ô nguồn ≈ 0 (việc 1.1) |
| **T7.3** Chính sách oracle: `OracleHiddenView` (theo mẫu `LegacyHiddenView`), hàm điểm oracle trong `sim/policies/scores.py`, chặn dùng ngoài chính sách ngưỡng, `run_metadata` ghi cờ dùng biến ẩn; test `SessionBatch` vẫn không có cột ẩn (việc 1.5, KN 3.1) | **H7.3** Hủy đúng thời điểm: tính `t_cancel = t_ghép + 60·e/h`; ở bước 1, nếu `t_cancel < t_đón` thì hủy thay vì đón, xe rảnh theo luật nửa ETA (`trips.py`, `cancel.py`); không rút thêm số; test so với hazard chính xác, nhả ngân sách đúng (việc 1.2) |
| **T7.4** Ghi độ căng trễ cho chính sách thí nghiệm và luật cũ, cờ `lag_slot_same_block` (`policies/experiment.py`, `legacy.py`, `logger.py`); test không nhìn trước (việc 1.5, KN 3.3) | **H7.4** Biến động tự nhiên (`sim/shocks.py` mới; `demand.py`, `supply.py`; tốc độ khi mưa trong `space.py`/`matching.py`/`trips.py`): cầu theo ngày; sự kiện ở địa điểm cố định (buổi tối, cầu tăng lúc tan); mưa chiều tối (cầu tăng, xe chậm, một phần tài xế nghỉ); tài xế đi làm độc lập theo xác suất; giờ vào ca lệch. Lịch biến động rút trước theo ngày qua luồng `SHOCK`; chính sách không đọc được (việc 1.4) |
| **T7.5** `runner.py`: ghi `budget_pilot_seed`, `budget_pilot_spent_usd`, cột `world_seed`; `logger.py` ghi lịch biến động ra `meta/` (việc 1.5, Q23) | **H7.5** Test cho H7.4: tắt biến động thì trùng từng số với bản cũ; cùng ngày cùng biến động dưới mọi chính sách; độ lớn biến động đúng tham số |

**Kiểm tra cuối S7 (G7, việc 1.6):**
- `pytest -q` toàn bộ pass.
- **Hồi quy:** đặt mọi khóa mới về giá trị cũ (lưới 37 ô, `lowest_id`, `exact_time = false`, `shocks.enabled = false`) thì đầu ra 1 ngày trùng từng số với code trước S7.
- Không rò biến ẩn (`test_no_hidden_leak`), không nhìn trước, bất biến ngân sách, số ngẫu nhiên chung giữa các chính sách khi bật biến động.
- A5: ≤ 30 giây/ngày trên lưới 61 ô.
- Giao **B10** (Hoàng → Tình) và **B11** (Tình → Hoàng); PR S7 vào `develop`.

### Sprint 8: Hiệu chỉnh và sinh dữ liệu (việc 1.7, Giai đoạn 2)

Trong S8 **chỉ Hoàng sửa giá trị** `default.yaml` (như S3 cũ).

| Tình | Hoàng |
|---|---|
| **T8.1** Sau B12: `calibrate_budget` cho W0 và W1; sinh dữ liệu cho **mỗi** thế giới: luật cũ 28 ngày; luật cũ 4 mức nhắm theo `u` (độ nhạy); switchback 1 ô, 7 ô, toàn thành phố 28 ngày; A/B theo khách 28 ngày; GTE 10 seed; **GTE với đội xe rất lớn**; bật/tắt toàn bộ 5 seed ghi đầy đủ (việc 2.1) | **H8.1** Hiệu chỉnh trên W0 (lưới H3, đã sửa lỗi, không biến động): 5 chỉ tiêu cũ + chỉ tiêu mới **tỷ lệ xe bận theo giờ** (lúc 7h gần 70% đỉnh như NYC). Chỉ chỉnh `fleet_size`, `demand_scale`, `shift_start_mixture`. Ghi bảng hiệu chỉnh vào `decisions.md`, `config_hash` mới (việc 1.7) |
| **T8.2** Ghi lệnh vào `docs/datasets.md`; chạy `check_dataset` (schema + không rò biến ẩn) trên mọi bộ → giao **B13** (việc 2.1) | **H8.2** A1 (đường throughput) và A5 trên lưới mới; cập nhật test CAL và `tests.md` cho chỉ tiêu mới (việc 1.7) |
| **T8.3** A2 (số ngẫu nhiên chung) trên code mới; cập nhật `analysis/validation.py` | **H8.3** Chốt tham số biến động trong `config/world_w1.yaml`; báo các chỉ tiêu thị trường của W1 (không hiệu chỉnh lại W1) → giao **B12** (cấu hình W0 + overlay W1) |

**Kiểm tra cuối S8 (G8):**
- A1, A2, A5 và CAL (gồm chỉ tiêu mới) đạt trên W0; chỉ tiêu của W1 được ghi lại.
- Mọi bộ dữ liệu qua `check_dataset`; `config_hash` khớp `datasets.md`.
- **Biến động có tác dụng:** trên W1, tỷ lệ (ô, slot) căng **ngoài 5–8h** tăng rõ so với W0.

### Sprint 9: Phương pháp (Giai đoạn 3) và chuẩn bị đánh giá

| Tình | Hoàng |
|---|---|
| **T9.1** Hàm điểm "tắt cố định ở các giờ voucher có hại" (trả NaN ở các giờ có τ̂(h) < 0, lấy từ H9.3; θ = 0), cũng là tầng vùng `hour` của Q6 (việc 4.1) | **H9.1** Học lại DR-learner trên luật cũ của W0 và W1 (`uplift.py`); xuất hàm điểm theo mỗi USD (việc 3.1) |
| **T9.2** Code bảng thác nước ba nguồn sai số (`interference.py`): gây nhiễu (so thô − mốc không gây nhiễu, gọi `confounding.py` của Hoàng), tranh chấp xe (mức trên mỗi khách so với GTE), công suất (GTE đội xe mặc định so với GTE đội xe rất lớn); các phần cộng lại khớp (việc 4.4) | **H9.2** Chọn chỉ số độ căng (`tension.py`) trên W0 và W1: `ring1`, `system`, `hour` và các ứng viên cũ (việc 3.2) |
| **T9.3** Tách burn-in bias khỏi ảnh hưởng kéo dài: từ dữ liệu bật/tắt toàn bộ, tác dụng trên phút 15–60 mỗi giờ so với GTE, có khoảng tin cậy (việc 4.5) | **H9.3** Ngưỡng theo độ căng (`theta.py`, `estimate.py`): chia khối switchback toàn thành phố theo **độ căng trước khối**; đường tác dụng theo độ căng đủ các nhóm, có khoảng tin cậy; ngưỡng mới; giữ ngưỡng theo giờ (A) và (B) để so; **so phân bố độ căng khi không voucher và khi chính sách chạy** (việc 3.3) |
| **T9.4** Code animation `analysis/animation.py` theo đúng mục 6 của hướng dẫn mentor: lục giác bằng `RegularPolygon`, tọa độ từ `dashboard.geometry.axial_to_xy`, `completed_by_request_slot`, ba bản đồ + đường ΔN cộng dồn có dải tin cậy, thang màu cố định đối xứng an toàn mù màu, thanh màu, chú thích theo khung; test trên dữ liệu nhỏ (ma trận đúng `[n_slot, 61]`, tổng Δ khớp) (việc 5.5) | **H9.4** Giao **B14**: hàm điểm mới, chỉ số độ căng đã chọn, ngưỡng mới và cũ, danh sách giờ có hại, cho W0 và W1 |

**Kiểm tra cuối S9 (G9):**
- Có hình đường tác dụng theo độ căng với khoảng tin cậy (tiêu chí 1) và ngưỡng có khoảng tin cậy.
- Test của mọi code phân tích mới pass; animation chạy được trên dữ liệu nhỏ.
- B14 đã giao; Tình kiểm tra nạp được trong tiến trình con.

### Sprint 10: Thí nghiệm đánh giá (Giai đoạn 4)

| Tình | Hoàng |
|---|---|
| **T10.1** Bảng chính sách mở rộng trên **W0 và W1**: các chính sách cũ + ngưỡng theo độ căng + ngưỡng theo giờ + luật tắt cố định theo giờ + tầng vùng `city` + oracle; báo **tỷ lệ khoảng cách `all_on` → oracle đã lấp** và giới hạn của oracle (việc 4.1, Q4–6, Q21) | **H10.1** Hai kiểm tra nhỏ: điều chỉnh theo đặc trưng so với so thô **trên đúng mốc**; tỷ lệ bỏ chờ; **tác hại 7–8h trước và sau khi sửa lịch ca** (việc 4.7, Q16, Q20) |
| **T10.2** Quét θ (16 mức × 30 seed) trên W0, W1; chọn ngưỡng tốt nhất trên nửa seed, đo regret trên nửa còn lại; báo "% lợi ích tối đa của tầng vùng lấy lại được" (việc 4.2, Q2, Q18) | **H10.2** Gây nhiễu và độ nhạy theo `u` trên dữ liệu mới (`confounding.py`): tách so thô, ghi rõ mốc của từng ước lượng (kiểu 6,9 hay 7,4 như bản cũ) |
| **T10.3** Số lần bật/tắt ở chính sách khuyến nghị; đề xuất thời gian giữ trạng thái (việc 4.3, Q7) | **H10.3** Chạy lại notebook 04, 05 trên dữ liệu mới; sửa chữ "hiệu ứng thật" trong hình thành "mốc không gây nhiễu"/"ATE" |
| **T10.4** Qini (`qini_vs_value.py`): tương quan trong nhóm hàm theo mỗi USD; Qini có tính chi phí; giải thích vì sao "chuyến thêm / 100 USD" khớp; tìm ví dụ Qini và số chuyến lệch nhau **do cung** trên W1 (việc 4.6, Q3, Q11–13) | |
| **T10.5** Độ vững trên W1: B ∈ {0,3; 0,6; 1,0} × số xe {100%; 83%; 67%} với chính sách khuyến nghị; bảng chính sách trên 3 `world_seed` (việc 4.8, Q18, Q19) | |
| **T10.6** Chạy lại notebook 01–03 (thêm thác nước, burn-in); giao **B15** (kết quả cho báo cáo và animation) | |

**Kiểm tra cuối S10 (G10):**
- Mọi bảng kết quả nằm trong `runs/` và có lệnh trong `datasets.md`.
- Notebook 01–05 "Restart & Run All" sạch; hình xuất vào `docs/figures/`.
- Bảng thác nước cộng lại khớp; chênh lệch ghép cặp có khoảng tin cậy.
- Kết luận giả thuyết H1/H2 (ghi ở việc 0.1) được ghi vào `decisions.md`.

### Sprint 11: Báo cáo, animation, trả lời mentor (Giai đoạn 5)

| Tình | Hoàng |
|---|---|
| **T11.1** Animation bản cuối (việc 5.5): cặp `all_on` có ngân sách và chính sách khuyến nghị; cùng seed, cùng B, `--log-level full`, 10 seed; khung 5h–9h (hoặc khung có sự kiện trên W1), khoảng 1 giây/slot, dừng 2 giây ở cuối; ghi lệnh vào `datasets.md`, chạy `check_dataset`; `notebooks/06_animation.ipynb`; slide ghi "trong mô phỏng này", cặp chính sách, số seed, B; kiểm đủ **8 mục** ở mục 8 của hướng dẫn | **H11.1** Báo cáo Chương 3: lưới H3 độ phân giải 8, biến động, phương pháp ngưỡng theo độ căng; Phụ lục A (tham số mới); Bảng 4.1 sửa "theo ô H3 độ phân giải 8"; sửa lỗi `\noalign` ở `phuluc.tex`; số trang Castillo 2017 (việc 5.1) |
| **T11.2** Báo cáo Chương 4 phần của Tình: bảng chính sách W0/W1, quét θ, Qini, thiết kế thí nghiệm, thác nước, burn-in, độ vững; Phụ lục D liên quan (việc 5.1) | **H11.2** Báo cáo Chương 4 phần của Hoàng: RQ1 với đường tác dụng theo độ căng, chọn chỉ số độ căng, ngưỡng, gây nhiễu, tác hại 7–8h trước/sau khi sửa lịch ca (việc 5.1) |
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
| B9 | cả hai | PR hợp đồng: khóa config, luồng `SHOCK`, cột schema | đầu S7 | `pytest -q`; `config.py` nhận khóa mới; test hợp đồng schema |
| B10 | Hoàng → Tình | lõi đã sửa (việc 1.0, 1.1, 1.2, 1.4) | cuối S7 | test hồi quy (khóa về giá trị cũ → trùng số); số ngẫu nhiên chung khi bật biến động |
| B11 | Tình → Hoàng | chính sách đã sửa (việc 1.3, 1.5) | cuối S7 | test chính sách, không rò biến ẩn, oracle chỉ chạy với chính sách ngưỡng |
| B12 | Hoàng → Tình | `default.yaml` đã hiệu chỉnh (W0) + `world_w1.yaml` | giữa S8 | A1, A5, CAL đạt; `config_hash` |
| B13 | Tình → Hoàng | toàn bộ dữ liệu W0, W1 + `datasets.md` | cuối S8 | `check_dataset` pass; `config_hash` khớp |
| B14 | Hoàng → Tình | hàm điểm, chỉ số độ căng, ngưỡng mới/cũ, giờ có hại | cuối S9 | nạp được trong tiến trình con; tất định |
| B15 | Tình → Hoàng | bảng chính sách, quét θ, thác nước, độ vững | cuối S10 | số khớp `runs/`; notebook chạy sạch |

---

## 5. Thứ tự phụ thuộc

```
S7: B9 → (T7.x ∥ H7.x) → G7, B10, B11
S8: H8.1 → H8.2, H8.3 → B12 → T8.1 → T8.2 (B13), T8.3 → G8
S9: H9.1 → H9.2 → H9.3 → H9.4 (B14);  T9.2, T9.3, T9.4 song song;  T9.1 sau H9.3 → G9
S10: T10.1 → T10.2, T10.3, T10.5;  T10.4 ∥ H10.x → T10.6 (B15) → G10
S11: T11.1 ∥ H11.1, H11.2, T11.2 → T11.3, H11.3 → T11.4/H11.4 → G11
```

---

## 6. Việc có điều kiện (chỉ làm khi mentor yêu cầu)

- **4.9** Thêm giá và độ dài chuyến vào mô hình hiệu ứng và chi phí (Hoàng). Nếu không làm, Q22 trả lời rõ lý do.
- **5.6** Trang so sánh chính sách trên dashboard (Tình), tách riêng khỏi animation.

---

## 7. Điều kiện hoàn thành toàn bộ (G11)

- Báo cáo biên dịch không lỗi, không tham chiếu hay trích dẫn hỏng.
- Mọi con số trong báo cáo truy được về `runs/` qua `datasets.md`; áp đủ nguyên tắc viết số ở việc 5.2.
- File trả lời mentor có đủ Q1–Q27.
- Animation đạt 8 mục kiểm tra của hướng dẫn.
- `pytest -q` và `pytest -q -m slow` pass.
- PR `develop1`/`develop2` → `develop`; gộp `develop → main`; gắn tag bản cuối.

---

## 8. Đối chiếu với `ke_hoach_sua_v3.md`

| Việc | Task | Việc | Task |
|---|---|---|---|
| 1.0 | H7.1 | 4.1 | T9.1, T10.1 |
| 1.1 | H7.2 | 4.2 | T10.2 |
| 1.2 | H7.3 | 4.3 | T10.3 |
| 1.3 | T7.1 | 4.4 | T9.2 |
| 1.4 | H7.4, H7.5 | 4.5 | T9.3 |
| 1.5 | T7.2–T7.5 | 4.6 | T10.4 |
| 1.6 | G7 | 4.7 | H10.1 |
| 1.7 | H8.1–H8.3 | 4.8 | T10.5 |
| 2.1 | T8.1, T8.2 | 4.9 | có điều kiện (mục 6) |
| 3.1 | H9.1 | 5.1 | H11.1, T11.2, H11.2 |
| 3.2 | H9.2 | 5.2–5.4 | T11.4/H11.4 |
| 3.3 | H9.3 | 5.4b | T11.3, H11.3, T11.4/H11.4 |
| | | 5.5 | T9.4, T11.1 |
| | | 5.6 | có điều kiện (mục 6) |
