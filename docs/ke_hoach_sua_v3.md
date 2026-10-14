# Kế hoạch sửa đề tài sau review bản 2

Nguồn: `Report_version2_review.md` (Q = câu hỏi ở Phần I), `khuyen-nghi-code-simulator.md` (KN), `huong-dan-animation-chinh-sach.md` (ba tài liệu này do mentor gửi riêng, không lưu trong repo), và **`docs/de_xuat_tham_so_ha_noi.md` (ĐX)**: giá trị và nguồn của mọi tham số theo quy mô Hà Nội.

Phân công theo sprint (S7–S11) cho Tình và Hoàng: xem `phan_cong_v3.md`.

**Cập nhật 14/10:** mentor nhận xét thành phố và ô hơi nhỏ. Nhóm đổi sang:
- ô H3 độ phân giải 7;
- quy mô nội thành Hà Nội (315 km²);
- tiền VND, giá cước theo bảng giá GrabCar Hà Nội (ĐX).

Thay đổi này nằm ở việc 1.0 và việc mới 1.0b.

Các việc sắp theo thứ tự thực hiện. Mỗi việc ghi: **Là gì · Vì sao · Ở đâu · Làm gì**.

Nguyên tắc sắp xếp: mọi thay đổi simulator làm đổi số liệu, nên gom vào **một đợt** (Giai đoạn 1), sinh dữ liệu **một lần** (Giai đoạn 2), rồi mới chạy thí nghiệm và viết lại báo cáo.

| Giai đoạn | Nội dung | Thời gian ước tính |
|---|---|---|
| 0 | Chốt hướng, sửa những gì không phụ thuộc số liệu | ~1 ngày |
| 1 | Sửa simulator (một đợt), gồm đổi quy mô Hà Nội và tiền VND | ~5–6 ngày |
| 2 | Hiệu chỉnh và sinh dữ liệu cho hai thế giới | ~3 ngày công (máy ~1 giờ với 8 lõi; ĐX mục C, E) |
| 3 | Phương pháp | ~2 ngày |
| 4 | Thí nghiệm đánh giá | ~2–3 ngày |
| 5 | Viết lại báo cáo, sản phẩm trình bày | ~3 ngày |

---

## Giai đoạn 0. Chốt hướng và sửa những gì không phụ thuộc số liệu

### 0.1. Thống nhất với Tình và ghi quyết định — ✅ đã xong

- **Là gì:** chốt các thay đổi simulator (thêm biến động, sửa ba lỗi cài đặt) và các giả thuyết sẽ kiểm chứng.
- **Vì sao:** theo quy tắc nhóm, quyết định chốt khi hai người đồng ý. Ghi giả thuyết **trước khi chạy** để kết quả không bị nghi là chọn theo ý muốn.
- **Ở đâu:** `docs/decisions.md`.
- **Làm gì:**
  - ghi các thay đổi simulator của Giai đoạn 1;
  - ghi hai giả thuyết: *thế giới không biến động thì chính sách supply-aware ngang luật tắt theo giờ; thế giới có biến động thì chính sách supply-aware thắng*;
  - ghi chỗ code lệch spec §8 (quét đội xe bằng mặt nạ numpy thay vì hàng đợi ưu tiên).

  *Hai giả thuyết ghi chính thức vào `decisions.md` trong PR hợp đồng B9.*

### 0.2. Báo mentor hướng đi — ✅ đã xong

- **Là gì:** tin nhắn thông báo, không chờ trả lời mới làm.
- **Vì sao:** thay đổi lớn so với bản mentor vừa review; hướng này khớp góp ý ở Q4, Q20, KN 5.1.
- **Làm gì:** báo rằng nhóm thêm biến động tự nhiên và sửa các lỗi mentor chỉ ra, đặt sau khóa config, và báo kết quả trên cả thế giới cũ lẫn thế giới có biến động.

### 0.3. Sửa trích dẫn (Q25–27, Phần II mục 6) — ✅ đã xong (bản `BaoCao_SupplyAwarePromotion_v1 (5) - sua trich dan.zip`)

- **Là gì:** một số trích dẫn sai hoặc lệch so với bài gốc; có một chỗ trích ngược chiều.
- **Vì sao:** trích sai làm người đọc mất niềm tin vào cả báo cáo.
- **Ở đâu:** Chương 1, 2, 3; `thesis.bib`.
- **Làm gì:**
  - **Holtz và cộng sự:** bỏ vế "xác nhận độ chệch lớn nhất khi thiếu cung" (bài gốc gợi ý ngược lại); chỉ giữ ý "độ chệch do tranh chấp có thể rất lớn".
  - **Zhao & Harinen:** bỏ khỏi luật "τ/c ≥ λ" và công thức κ; thay bằng nguồn về bài toán cái túi phân số / Lagrange. Chuyển sang trích ở chỗ "voucher chỉ trả khi chuyến hoàn thành".
  - **Castillo và cộng sự:** "0,25–0,45" → "0,25–0,5", ghi số trang, nói rõ ngưỡng phụ thuộc điều kiện thị trường.
  - **Độ kiên nhẫn log-normal mode 5 phút:** ghi "lấy cảm hứng từ" Castillo; đổi nhãn nguồn trong config thành `assume`.
  - **Mô hình logit:** thêm Peng và cộng sự (2025) làm nguồn gốc.
  - **Yadlowsky và cộng sự:** sửa thành "Qini đo chất lượng xếp hạng gộp trên mọi tỷ lệ phát, không tính chi phí, giả định SUTVA".
  - **Hu & Wager:** thêm vế đánh đổi của burn-in.

### 0.4. Thống nhất ký hiệu và văn phong — ✅ đã xong (bản `BaoCao_SupplyAwarePromotion_v1 (6) - sua ky hieu va van phong.zip`)

- **Là gì:** cùng một khái niệm đang có nhiều ký hiệu; văn phong Mục 1.3, 1.5, 2.2 khác phần còn lại.
- **Làm gì:** chọn một ký hiệu cho mỗi khái niệm (GTE hoặc GATE; $A_s$ hoặc $Z_i$; không dùng $V$ cho hai nghĩa); viết lại ba mục cho cùng giọng.

### 0.5. Sửa lỗi không phụ thuộc số liệu (Q23, Q24) — ✅ đã xong (bản `BaoCao_SupplyAwarePromotion_v1 (7) - sua loi khong phu thuoc so lieu.zip`)

- **Làm gì:**
  - Mục 3.2: "γ = 1" → **γ = 1/2**;
  - Mục 3.7: tham chiếu công thức Qini đang trỏ nhầm sang công thức logit;
  - giải thích vì sao **B = 5.545,80** chứ không phải 0,3 × 18.630,5: B tính từ một lượt chạy thử `all_on` với seed riêng, không phải từ lượt chạy GTE.

### 0.6. Đổi tên và chọn đại lượng so sánh (Q14, Q15) — ✅ đã xong (bản `BaoCao_SupplyAwarePromotion_v1 (8) - moc khong gay nhieu.zip`; chọn ATE)

- **Là gì:** "hiệu ứng thật" đo trên lát phát ngẫu nhiên vẫn chịu ảnh hưởng tranh chấp xe; phép tách so thô đang lẫn ATE và ATT.
- **Làm gì:**
  - đổi "hiệu ứng thật" thành **"mốc không gây nhiễu"**;
  - chọn rõ so với **ATE hay ATT**, rồi viết phần "phóng đại" cho nhất quán.

### 0.7. Trích H3 và ghi hạn chế, hướng phát triển — ✅ đã xong (bản `BaoCao_SupplyAwarePromotion_v1 (9) - H3 han che huong phat trien.zip`)

- **Làm gì:**
  - giải thích kích thước ô bằng lưới H3 của Uber (độ phân giải 8, khoảng 0,74 km²). *(Cập nhật 14/10: ô đổi sang H3 độ phân giải 7 ở việc 1.0; câu trong Bảng 4.1 và trích dẫn sửa lại ở 5.1.)*
  - ghi hạn chế: **khách không đặt lại** sau khi bỏ hoặc hủy, nên có thể phóng đại thiệt hại khi thiếu xe (KN 5.3).
  - ghi hướng phát triển: chạy simulator trên dữ liệu thành phố thật (NYC, TP.HCM), với nhịp cầu khác nhau theo loại khu vực.

---

## Giai đoạn 1. Sửa simulator (một đợt)

Thay đổi mô hình (1.1, 1.2, 1.4) đặt sau **khóa config**: tắt khóa thì chạy như cũ. Thay đổi giá trị (1.0, 1.0b) vẫn chạy lại được bằng giá trị cũ trong file ghim của bộ kiểm hồi quy G7. Mỗi thay đổi đụng tới `sim/`, `config.py` hoặc `schema.md` cần một mục trong `docs/decisions.md`, mục log và PR có chủ file duyệt (theo `CLAUDE.md`).

### 1.0. Đổi quy mô theo Hà Nội: ô H3 độ phân giải 7, thành phố 315 km² (ĐX mục B1–B3)

- **Là gì:** ô hiện có cạnh 0,75 km (1,46 km²), thành phố 37 ô (54 km²). Mentor nhận xét như vậy hơi nhỏ, gợi ý ô cỡ một phường trung tâm.
- **Vì sao:**
  - kích thước ô và thành phố cần có căn cứ. H3 là lưới các nền tảng gọi xe dùng để đo cung–cầu theo ô;
  - quy mô và tốc độ lấy theo Hà Nội, thị trường mục tiêu;
  - đằng nào cũng sinh lại toàn bộ dữ liệu, nên đổi lúc này không tốn thêm một lần chạy.
- **Ở đâu:** các mục `space`, `supply`, `demand` của `config/default.yaml` (giá trị của Hoàng); `tests/test_engine.py` (đang kiểm cứng 37 ô); `tests/test_space.py` (kích thước cụm 7 ô).
- **Làm gì** (giá trị và nguồn ở ĐX):
  - **ô H3 độ phân giải 7:** `edge_km = 1.41` (diện tích 5,16 km²);
  - **bán kính 4:** 61 ô, 315 km², cỡ nội thành Hà Nội. Mặt xuyến với R = 4 đã được kiểm trong spec;
  - **tốc độ theo TomTom 2025, Hà Nội:** trung bình 18 km/h; `speed_factor_by_hour` mới (đêm ×1,45, cao điểm sáng ×0,85, cao điểm tối ×0,76);
  - **ca tài xế 11,2 giờ** (khảo sát), sd 2,0, chặn [4, 14];
  - **điểm xuất phát cho hiệu chỉnh 1.7:**
    - `fleet_size = 1300` (1.000 giữ mật độ giờ-xe cũ nhưng cho 23 chuyến/xe/ngày, vượt dải [8; 18]; xem ĐX B2);
    - `n_riders = 120000` (giữ 1,3 session/khách/ngày của mô hình cũ; ĐX B3);
    - `base_sessions_per_cell_h = 124` (giữ mật độ khách);
    - `dest_decay_rings = 1.2` (quãng đường TB ≈ 6 km);
  - giữ `max_pickup_eta_min = 30` (quy tắc cứng 6). Đi giữa hai ô kề mất ~11 phút, ~14 phút giờ cao điểm;
  - sửa test đang giả định 37 ô và kích thước cụm;
  - **đo A5 ngay** trên cấu hình mới, vì số session tăng ~5,8 lần và số xe ~5,4 lần. Tiêu chí mới do nhóm quyết: **A5-HN ≤ 60 giây/ngày mô phỏng/một tiến trình** (ĐX mục E); vượt thì profile và tối ưu đúng bước nặng nhất, tối đa 1 ngày công, `numba` kèm fallback được phép; vẫn vượt thì ghi số thật, không nới thêm.

### 1.0b. Đổi tiền sang VND và giá cước theo GrabCar Hà Nội (ĐX mục A2, B4)

- **Là gì:** mô hình đang tính tiền bằng USD: giá = 3 USD + 1,70 USD/phút, voucher 20% không trần.
- **Vì sao:**
  - thị trường mục tiêu là Hà Nội; giá và voucher thật có công bố, nên dùng được trực tiếp;
  - độ dài chuyến và giá quyết định chi phí voucher, tức quyết định ai đáng được phát.
- **Ở đâu:** toàn repo (đổi tên); `sim/pricing.py`, `sim/budget.py`, các mục `pricing`, `voucher`, `budget` (Tình); `riders.beta_price` (Hoàng).
- **Làm gì:**
  - **đổi tên** `_usd` → `_vnd`, `cents` → đồng nguyên trên toàn repo (~1.150 chỗ, 79 file), bằng một script tìm–thay chạy một lần trong PR hợp đồng;
  - **công thức giá:** 28.473đ cho 2 km đầu + 9.818đ/km + 442đ/phút sau 2 km + phí nền tảng 10.000đ (thuộc nền tảng);
    - khóa mới: `pricing.open_fare_vnd`, `open_km`, `per_km_vnd`, `per_min_vnd`, `platform_fee_vnd`;
    - bỏ `target_mean_fare_usd`;
  - **voucher 25%, tối đa 20.000đ** (`voucher.pct_of_fare`, `voucher.max_vnd`);
  - **phí ứng dụng 25%** (`commission_rate`);
  - **độ nhạy giá:** `riders.beta_price_per_kvnd = 0.022` (giữ β × giá TB như mô hình cũ). `alpha0`, `delta0` hiệu chỉnh lại ở 1.7;
  - **kiểm tương đương đơn vị:**
    - viết lại giá trị cũ theo đơn vị mới (1 USD = 100 đơn vị) rồi chạy;
    - số chuyến, số request, số hủy phải trùng khớp với code cũ; cột tiền khớp ×100 trong sai số 1e-6;
    - đạt thì sinh lại mốc hồi quy G7 **một lần** (đính chính T-39 b, cả hai đồng ý);
  - **test:** chuyến 6 km, 20 phút có giá ≈ 83.638đ; voucher chạm trần 20.000đ; sổ ngân sách tính bằng đồng nguyên;
  - từ PR hợp đồng tới khi hiệu chỉnh xong (1.7), test CAL chậm sẽ không đạt vì có chỉ tiêu mới chưa hiệu chỉnh. Ghi log, không nới dải.

### 1.1. Sửa luật chọn xe ở vành ngoài (KN 2.1)

- **Là gì:** khi ô của khách hết xe, simulator lấy xe từ vành ô xung quanh. Mọi ô cùng vành có cùng thời gian đi, nên luôn "hòa", và luật hiện tại luôn chọn **ô có số thứ tự nhỏ nhất**.
- **Vì sao:** các ô số nhỏ bị rút xe nhiều hơn và căng hơn một cách nhân tạo (32,8% so với 23,2% số (ô, slot) căng).
- **Ở đâu:** `sim/space.py`, hàm `find_pickup` (Hoàng).
- **Làm gì:** khi hòa, chọn ô **có nhiều xe rảnh nhất**; bật làm mặc định, giữ luật cũ sau khóa config. Thêm test: trên thế giới đối xứng, số thứ tự ô không liên quan tới số lần bị rút xe.

### 1.2. Sửa thời điểm khách hủy (KN 2.2)

- **Là gì:** simulator xét "xe đã tới" ở bước 1 nhưng xét "khách hủy" ở bước 8. Khách lẽ ra hủy trong phút cuối trước khi xe tới thì không được xét.
- **Vì sao:** bỏ sót khoảng 7% số lần hủy; hủy là một kênh chính khiến voucher gây hại.
- **Ở đâu:** `sim/cancel.py`, `sim/trips.py` (Hoàng).
- **Làm gì:** tính chính xác thời điểm khách hủy; nếu trước lúc xe tới thì hủy thay vì đón. Không rút thêm số ngẫu nhiên. Bật làm mặc định.

### 1.3. Chặn độ căng dự báo ở 10 (KN 2.3) — ✅ đã xong (T7.1, PR #23)

- **Là gì:** với phạm vi theo ô, độ căng có thể bằng vô cùng và được đưa thẳng vào hàm điểm, trong khi mô hình được học trên dữ liệu đã chặn ở 10.
- **Ở đâu:** `sim/policies/threshold.py` (Tình).
- **Làm gì:** chặn ở 10 cho mọi trường hợp.

### 1.4. Thêm biến động tự nhiên và sửa lịch ca sáng (Q4, Q20, KN 5.1)

- **Là gì:** hiện mỗi ngày lặp lại y hệt (cùng lịch ca, cùng hình dạng cầu, không có cú sốc), nên thiếu xe chỉ rơi vào 5–8h.
- **Vì sao:** khi thiếu xe đoán được bằng giờ, không thể chứng minh việc đo độ căng theo vùng có giá trị. Lúc 7h, simulator chỉ có 25% số xe so với đỉnh, trong khi NYC là 70%.
- **Ở đâu:**
  - module mới `sim/shocks.py`; sửa `demand.py`, `supply.py` và tốc độ khi mưa (Hoàng);
  - file chung: mục mới `shocks:` trong `config/default.yaml`, luồng `SHOCK = 8` trong `rng.py`, `WorldPart.VENUES = 4`;
  - W0 tắt, W1 bật (overlay `config/world_w1.yaml`).
- **Làm gì** (giá trị và nguồn ở ĐX mục B5): làm đủ cả 5 loại.
  - **Cầu dao động giữa các ngày:** hệ số ngày ~ LogNormal, σ = 0,12 (NYC TLC).
  - **Sự kiện ở địa điểm cố định**, hai loại (`shocks.events.venues`); vị trí rút một lần theo `world_seed`:
    - sân vận động: 2 địa điểm (Mỹ Đình, Hàng Đẫy), mỗi địa điểm p = 0,05/ngày (≈ 2,8 sự kiện/28 ngày; với p = 0,03 một địa điểm chỉ còn 0,8, gần như không có trong dữ liệu), tan 21h30–23h, cầu ô ×20, vành kề ×3, trong 60 phút;
    - phố đi bộ: p = 0,43/ngày, tan 21–24h, cầu ô ×2, vành kề ×1,3, trong 60 phút.
  - **Mưa:** p = 0,31/ngày (trung bình năm ở Hà Nội), bắt đầu 14–19h, dài 1–3 giờ; cầu ×1,25, tốc độ ×0,85, 10% tài xế nghỉ suốt cơn mưa.
  - **Tài xế đi làm** 90% số ngày, độc lập với nhau.
  - **Giờ vào ca lệch:** độ lệch chuẩn 20 phút.
  - **Sửa lịch ca sáng:** làm ở 1.7, bằng hiệu chỉnh `shift_start_mixture`.
  - Mọi chính sách gặp **cùng một cú sốc**; chính sách **không được đọc** lịch cú sốc. Lịch ghi ra `meta/shocks` để phân tích.

### 1.5. Thêm code không làm đổi số liệu (Q4–6, Q8, Q18, Q21, Q23; KN 3.1–3.3)

Làm cùng đợt để chỉ sinh dữ liệu một lần.

| Thêm gì | Để làm gì | Ở đâu |
|---|---|---|
| Phạm vi `city` cho tầng vùng | So tầng vùng theo độ căng toàn thành phố | `threshold.py`, `config.py` |
| Chính sách **oracle**, qua cổng riêng tới hệ số ẩn | Biết chính sách đề xuất lấp được bao nhiêu phần khoảng cách tối đa | `sim/policies/` (Tình) |
| Ghi độ căng trễ cho **mọi** chính sách, cộng cờ "slot trước cùng khối switchback" | Chia tác dụng theo độ căng mà không dính cạm bẫy biến hậu can thiệp | `policies/`, `schema.md` |
| Ghi lượt chạy dùng tính B, và `world_seed`, vào kết quả | Người đọc khỏi phải đoán (Q23); dễ gộp nhiều thế giới | `runner.py` |

### 1.6. Kiểm thử

- Tắt mọi khóa mới (và đặt giá trị cũ theo đơn vị mới) thì chạy như cũ. Kiểm bằng mốc hồi quy G7 (`tests/test_regression_s7.py`), mốc này sinh lại một lần sau khi đổi đơn vị (1.0b).
- Cùng ngày thì cùng cú sốc dưới mọi chính sách.
- Không rò biến ẩn, không nhìn trước.
- Bất biến ngân sách.
- Nghiệm thu A1–A5 đạt (A5 theo tiêu chí A5-HN 60 giây/ngày/tiến trình, ĐX mục E).
- Oracle chỉ dùng được với chính sách ngưỡng.

### 1.7. Hiệu chỉnh lại

- **Là gì:** quy mô Hà Nội, giá VND, các bản sửa và biến động làm đổi mức trung bình của thị trường.
- **Làm gì** (ĐX mục C, D): hiệu chỉnh trên W0.
  - **Núm được chỉnh:** `fleet_size`, `demand_scale`, `shift_start_mixture`, `dest_decay_rings`, `alpha0`, `delta0`.
  - **Chỉ tiêu:**
    - P(đặt) 13–17%;
    - mức tăng đặt xe khi có voucher +35–70%;
    - (ô, slot) căng 10–35%, dư 30–80%;
    - tỷ lệ xe bận lúc 6/7/8h theo NYC;
    - **quãng đường TB 5–8 km** (mới, thay chỉ tiêu giá TB);
    - **8–18 chuyến/tài xế/ngày** (mới).
  - **Chỉ kiểm, không chỉnh theo:** thời gian chờ đón TB 3–8 phút; thời gian chuyến TB 15–25 phút; tỷ lệ hủy và bỏ chờ (chỉ báo cáo).
  - W1 không hiệu chỉnh lại; chỉ báo các chỉ tiêu.

---

## Giai đoạn 2. Sinh dữ liệu cho hai thế giới

### 2.1. Sinh dữ liệu W0 và W1

- **Là gì:** W0 = simulator đã sửa lỗi, **không** biến động. W1 = đã sửa lỗi, **có** biến động.
- **Vì sao:** so hai thế giới là phép thử cho giả thuyết supply-aware. Dữ liệu cũ không dùng lại được vì code đã sửa lỗi.
- **Làm gì:** mỗi thế giới sinh:
  - dữ liệu luật cũ 28 ngày;
  - luật cũ với 4 mức nhắm theo `u` (độ nhạy gây nhiễu);
  - switchback 1 ô, 7 ô, toàn thành phố;
  - A/B theo khách;
  - GTE;
  - GTE với đội xe rất lớn (để tách phần "công suất" ở 4.4);
  - bật/tắt toàn bộ 5 seed, ghi đầy đủ (cho 4.5).

  Ghi lệnh vào `docs/datasets.md`. Khoảng 615 ngày mô phỏng cho cả hai thế giới, ước ~1,1 giờ máy với `runner.n_procs = 8` ở 50 giây/ngày/tiến trình (bảng ngân sách ở ĐX mục E; cập nhật sau khi H7.1 đo A5-HN).

---

## Giai đoạn 3. Phương pháp

### 3.1. Học lại mô hình chọn khách

- **Làm gì:** chạy lại DR-learner (theo mỗi 1.000đ) trên dữ liệu luật cũ mới.

### 3.2. Chọn lại chỉ số độ căng (Q5)

- **Làm gì:** chấm lại theo hai tiêu chí cũ, so `ring1`, `system`, `hour` trên W0 và W1.

### 3.3. Đổi cách ước lượng ngưỡng: theo độ căng thay vì theo giờ (Q8–10, tiêu chí 1)

- **Là gì:** hiện tác dụng của voucher được tính **theo giờ**, còn độ căng chỉ quyết định cắt ai trước. Ngưỡng 0,25 thực chất là một luật theo giờ đổi sang thang độ căng.
- **Vì sao:** phương pháp chưa thật sự supply-aware, và sẽ hỏng khi thiếu xe xảy ra ngoài giờ cố định. Mentor chấm tiêu chí 1 "một phần" vì chưa có đường tác dụng theo độ căng.
- **Ở đâu:** `analysis/theta.py`, `analysis/estimate.py`; Mục 3.6 của báo cáo.
- **Làm gì:**
  - từ switchback toàn thành phố, chia các khối theo **độ căng đo trước khi khối bắt đầu** (không dùng độ căng trong khối, vì đó là biến bị voucher tác động);
  - vẽ **đường tác dụng voucher theo độ căng**, đủ các nhóm, có khoảng tin cậy;
  - chọn ngưỡng tại chỗ voucher bắt đầu có hại;
  - giữ phương pháp theo giờ cũ để so sánh;
  - giải thích vì sao tác hại thấy rõ ở cấp thành phố nhưng không rõ ở cấp ô;
  - **so phân bố độ căng đo khi không phát voucher với khi chính sách đang chạy** (Phần II mục 4, D.5). Voucher làm thêm xe đi đón nên độ căng thấp hơn. Nếu lệch đáng kể, ngưỡng phải tính trên độ căng đo dưới chính sách. Đây cũng là phép kiểm giả thuyết "mô hình (B) cắt quá tay".

---

## Giai đoạn 4. Thí nghiệm đánh giá

### 4.1. Bảng chính sách mở rộng, trên W0 và W1 (Q4–6, Q21) — thí nghiệm trung tâm

- **Là gì:** so số chuyến của các chính sách dưới cùng ngân sách.
- **Vì sao:** trả lời câu hỏi lớn nhất của mentor: supply-aware có thật sự cần, hay chỉ là luật tắt theo giờ đội lốt.
- **Làm gì:** ngoài các chính sách cũ, thêm:
  - ngưỡng theo độ căng (phương pháp mới);
  - ngưỡng theo giờ (phương pháp cũ);
  - luật tắt cố định ở các giờ voucher có hại (viết bằng hàm điểm trả NaN ở các giờ đó, θ = 0). Đây cũng chính là "tầng vùng dùng `hour`" của Q6, nên chỉ chạy một lần;
  - tầng vùng dùng `city`;
  - oracle. Báo thêm **tỷ lệ khoảng cách từ `all_on` tới oracle mà chính sách đề xuất lấp được** (Q21), và ghi rõ oracle chỉ là mốc trên của chính sách dựa trên từng khách, vì nó không biết ảnh hưởng lên khách khác (KN 3.1).

### 4.2. Quét ngưỡng và tính regret (Q2, Q18)

- **Làm gì:**
  - quét θ (16 mức × 30 seed; đặt `sweep.theta_grid` 16 mức, `sweep.n_seeds = 30`);
  - chọn ngưỡng tốt nhất trên **một nửa** số seed, đo regret trên **nửa còn lại**;
  - diễn đạt kết quả theo "lấy lại bao nhiêu % lợi ích tối đa của tầng vùng".

### 4.3. Đo số lần bật/tắt (Q7)

- **Làm gì:** đo trên chính sách khuyến nghị cuối cùng; đề xuất thời gian tối thiểu giữ trạng thái cho vận hành.

### 4.4. Bảng thác nước ba nguồn sai số (Q17, tiêu chí 4)

- **Là gì:** tách khoảng cách giữa so thô trên dữ liệu lịch sử và đáp án đúng thành ba phần trên cùng một mốc; các phần cộng lại phải khớp.
- **Vì sao:** mentor chấm tiêu chí 4 **"chưa đạt"**.
- **Làm gì:**
  - gây nhiễu: so thô trừ mốc không gây nhiễu;
  - tranh chấp xe: so mức trên mỗi khách với GTE;
  - công suất: GTE đội xe mặc định so với GTE đội xe rất lớn.

### 4.5. Tách hai nguồn chệch của switchback toàn thành phố (Phần II mục 6)

- **Làm gì:** từ lượt chạy bật/tắt toàn bộ, tính tác dụng chỉ trên phút 15–60 mỗi giờ rồi so với GTE. Phần chênh là burn-in bias, phần còn lại là ảnh hưởng kéo dài. Báo khoảng tin cậy trước khi giải thích.

### 4.6. Phân tích lại Qini (Q3, Q11–13)

- **Làm gì:**
  - tính tương quan Qini–số chuyến **trong nhóm hàm theo mỗi 1.000đ**;
  - thử **Qini có tính chi phí** (trục hoành là tiền đã chi);
  - giải thích vì sao "chuyến thêm trên 100.000đ" vẫn khớp số chuyến dù dữ liệu A/B bị chệch;
  - **kiểm tra lại cơ chế phản ví dụ:** trên W1 có ví dụ Qini cao mà ít chuyến **do cung** không.

### 4.7. Hai kiểm tra nhỏ (Q16, KN 5.2)

- Vì sao điều chỉnh theo đặc trưng (11,7) lại chệch hơn so thô (10,5). Một phần là do khác mốc (7,4 so với 6,9). So trên đúng mốc, độ chệch vẫn lớn hơn (+0,043 so với +0,036). Giả thuyết cho phần còn lại: luật cũ ưu tiên khách ít đi xe nhưng có $u$ cao; hai hướng chọn lọc bù trừ nhau.
- Đo tỷ lệ **bỏ chờ** trên thế giới mới (trước đây gần 0%).
- So **tác hại lúc 7–8h trước và sau khi sửa lịch ca** (Q20): nếu tác hại giảm mạnh, phần lớn tác hại cũ là do lịch ca; ghi rõ trong báo cáo.

### 4.8. Độ vững (Q18, Q19)

- **Làm gì:**
  - trên W1, quét ngân sách B (0,3 / 0,6 / 1,0 lần chi tiêu khi phát cho tất cả) và số xe (100% / 83% / 67% số xe sau hiệu chỉnh) với chính sách khuyến nghị;
  - lặp bảng chính sách trên 3 `world_seed`.

### 4.8b. Độ nhạy theo các giả định thiếu số liệu Hà Nội (ĐX mục D3)

- **Là gì:** cầu theo giờ, độ dài chuyến và tham số hủy không có số liệu Hà Nội, nên là giả định.
- **Vì sao:** cần chứng minh kết luận không phụ thuộc vào các giả định này.
- **Làm gì:** chạy chính sách khuyến nghị và các chính sách so sánh dưới:
  - hình cầu theo giờ: cũ và NYC TLC;
  - hazard hủy ×0,5, ×1, ×2;
  - quãng đường TB ~5 km và ~8 km (`dest_decay_rings` 1,0 và 2,0).

  Báo θ\* và chênh lệch giữa các chính sách có đổi không.

### 4.9. (Chỉ làm nếu mentor yêu cầu) Thêm giá hoặc độ dài chuyến vào mô hình (Q22)

- **Làm gì:** đưa vào cả mô hình hiệu ứng lẫn mô hình chi phí, so số chuyến.

---

## Giai đoạn 5. Viết lại báo cáo và sản phẩm trình bày

### 5.1. Viết lại Chương 3 và Chương 4

- **Làm gì:**
  - Chương 3 thêm:
    - quy mô Hà Nội (ô H3 độ phân giải 7, 315 km², tốc độ TomTom);
    - giá cước VND theo GrabCar;
    - biến động;
    - phương pháp ngưỡng theo độ căng.
  - Chương 4 thay toàn bộ số (tiền VND), báo W0 và W1 cạnh nhau.
  - Phụ lục A ghi nguồn từng tham số theo ĐX.

  Sửa luôn các lỗi nhỏ còn tồn:
  - Bảng 4.1:
    - dòng "Lưới" đổi thành "ô H3 độ phân giải 7 (5,16 km²), 61 ô, 315 km², quy mô nội thành Hà Nội";
    - các dòng giá, voucher, ngân sách đổi sang VND;
  - `phuluc.tex` dòng 165: thêm `\\` cuối dòng "Thư viện & …" (lỗi biên dịch `Misplaced \noalign` có từ bản gốc);
  - thêm số trang cho trích dẫn Castillo 2017 (con số 0,25–0,5, Q25);
  - thêm trích dẫn cho các nguồn mới trong ĐX (Grab, TomTom, Brodeur & Nield, …), mỗi nguồn trích **một lần**;
  - hướng phát triển (đã viết ở 0.7): thêm bản đồ thật của **Hà Nội** cạnh NYC, TP.HCM.

### 5.2. Áp nguyên tắc viết số (Phần II mục 5)

- Tách rõ lợi ích **xếp theo mỗi 1.000đ** và **tầng vùng**.
- Regret diễn đạt theo **% lợi ích tối đa** của tầng vùng.
- Không phân biệt được về thống kê thì viết **"ngang nhóm dẫn đầu"**, không viết "cao nhất".
- Khoảng "phóng đại" tính đúng từ số, và **ghi rõ mốc so sánh của từng ước lượng**. Ở bản cũ, 45–60% là đúng: phép điều chỉnh theo đặc trưng so với mốc 7,4 (chỉ các ô đang bật), không phải 6,9; con số 70% của mentor là do báo cáo chưa ghi mốc này.
- Báo khoảng tin cậy trước khi giải thích.

### 5.3. Viết lại tóm tắt, đóng góp và trả lời RQ (Q1–3)

- **Làm gì:**
  - giữ supply-aware là chủ đề;
  - ghi tách hai con số lợi ích;
  - nói thẳng cơ chế của phản ví dụ Qini ngay trong phần trả lời RQ3;
  - kết luận supply-aware dựa trên so sánh W0 và W1.

### 5.4. Ghi hạn chế

- **Làm gì:** ghi các hạn chế sau:
  - kênh bỏ chờ (nếu vẫn yếu);
  - khách không đặt lại;
  - số thế giới mô phỏng đã thử;
  - ETA báo không tính hàng đợi đơn đang chờ;
  - lưới là thành phố giả quy mô Hà Nội, không phải bản đồ thật;
  - cầu theo giờ, độ dài chuyến, tỷ lệ xe bận và tham số hủy là giả định hoặc lấy theo NYC (kèm kết quả độ nhạy 4.8b).

### 5.4b. Bản trả lời 27 câu hỏi của mentor (Phần I của review)

- **Là gì:** review yêu cầu nhóm *"trả lời ngắn, có số nếu được, và nói rõ câu nào cần chạy thêm mới trả lời được"*.
- **Vì sao:** đây là sản phẩm mentor chờ trước buổi review; kế hoạch trước chưa có.
- **Ở đâu:** một file Markdown riêng (ví dụ `docs/tra_loi_review_v2.md`).
- **Làm gì:** mỗi câu Q1–Q27 trả lời 1–3 câu, kèm số liệu mới và mục trong báo cáo. Câu nào không làm (ví dụ Q22 nếu bỏ 4.9) thì ghi rõ lý do.

### 5.5. Làm animation cho seminar (mentor giao)

- **Là gì:** GIF khoảng 20 giây, ba bản đồ lục giác cạnh nhau:
  1. chênh lệch **lượt đặt**;
  2. chênh lệch **chuyến hoàn thành**, cùng thang màu với bản đồ 1;
  3. độ căng, ô bị tắt voucher gạch chéo.

  Bên dưới là đường chênh lệch số chuyến cộng dồn, kèm khoảng tin cậy.
- **Vì sao:** cho bên vận hành *thấy* "lượt đặt tăng không có nghĩa là chuyến tăng".
- **Ở đâu:** `analysis/animation.py` và một notebook; không sửa `sim/`.
- **Làm gì:**
  - cặp chính sách: `all_on` có ngân sách (cũ) và chính sách khuyến nghị (mới); hai lượt chạy cùng seed, cùng B, `--log-level full`; ghi lệnh vào `docs/datasets.md` và chạy `check_dataset`;
  - khung giờ 5h–9h (hoặc khung có sự kiện trên W1), mỗi slot khoảng 1 giây, dừng 2 giây ở khung cuối;
  - chênh lệch lấy trung bình 10 seed;
  - chuyến hoàn thành tính theo **lúc đặt xe**, không dùng cột `n_completed`;
  - thang màu cố định, đối xứng quanh 0, an toàn cho người mù màu;
  - mỗi khung một câu chú thích;
  - kiểm tra tổng chênh lệch khớp bảng kết quả;
  - slide ghi "trong mô phỏng này", cặp chính sách, số seed và B;
  - có test (ma trận đúng kích thước theo số ô của lưới mới, tổng chênh lệch khớp bảng gốc) và log.

### 5.6. (Chỉ làm nếu mentor yêu cầu) Trang so sánh chính sách trên dashboard

- **Làm gì:** chỉ làm sau 5.5. `dashboard/` là phần của Tình; Hoàng duyệt.

---

## Không làm

- **Ghép xe tối ưu theo lô (Hungarian):** nó chữa đúng hiện tượng cần đo.
- **Cho tài xế phản ứng theo voucher hoặc thu nhập:** ngoài phạm vi; giữ cung độc lập với chính sách.
- **Tối ưu hiệu năng rộng:** chỉ tối ưu đúng bước nặng nhất, tối đa 1 ngày công, khi A5-HN đo ở 1.0 vượt 60 giây/ngày/tiến trình (ĐX mục E). Không viết lại engine.
- **Học mô hình uplift trong `sim/`.**
- **Bản đồ thành phố thật (Hà Nội, TP.HCM, NYC):** để hướng phát triển. Lưới vẫn là thành phố giả, nhưng kích thước ô theo H3, còn quy mô, tốc độ và giá theo Hà Nội (việc 1.0, 1.0b).
- **Mô phỏng xe máy:** chỉ mô phỏng ô tô 4 chỗ (ĐX mục A1).
- **Chạy thêm cặp `all_off`–`all_on` trong animation:** hướng dẫn ghi là tùy chọn; không cần.
