# Kế hoạch sửa đề tài sau review bản 2

Nguồn: `Report_version2_review.md` (Q = câu hỏi ở Phần I), `khuyen-nghi-code-simulator.md` (KN), `huong-dan-animation-chinh-sach.md`.

Phân công theo sprint (S7–S11) cho Tình và Hoàng: xem `phan_cong_v3.md`.

Các việc sắp theo thứ tự thực hiện. Mỗi việc ghi: **Là gì · Vì sao · Ở đâu · Làm gì**.

Nguyên tắc sắp xếp: mọi thay đổi simulator làm đổi số liệu, nên gom vào **một đợt** (Giai đoạn 1), sinh dữ liệu **một lần** (Giai đoạn 2), rồi mới chạy thí nghiệm và viết lại báo cáo.

| Giai đoạn | Nội dung | Thời gian ước tính |
|---|---|---|
| 0 | Chốt hướng, sửa những gì không phụ thuộc số liệu | ~1 ngày |
| 1 | Sửa simulator (một đợt) | ~3–4 ngày |
| 2 | Sinh dữ liệu cho hai thế giới | ~1 ngày chạy máy |
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
  - giải thích kích thước ô bằng lưới H3 của Uber (độ phân giải 8, khoảng 0,74 km²). *(Cập nhật: kích thước ô sẽ đổi theo đúng H3 độ phân giải 8 ở việc 1.0; câu trong Bảng 4.1 sửa lại ở 5.1.)*
  - ghi hạn chế: **khách không đặt lại** sau khi bỏ hoặc hủy, nên có thể phóng đại thiệt hại khi thiếu xe (KN 5.3).
  - ghi hướng phát triển: chạy simulator trên dữ liệu thành phố thật (NYC, TP.HCM), với nhịp cầu khác nhau theo loại khu vực.

---

## Giai đoạn 1. Sửa simulator (một đợt)

Mọi thay đổi đặt sau **khóa config**. Tắt khóa thì chạy như cũ. Mỗi thay đổi đụng tới `sim/`, `config.py` hoặc `schema.md` cần một mục trong `docs/decisions.md`, mục log và PR có chủ file duyệt (theo `CLAUDE.md`).

### 1.0. Đổi kích thước ô theo H3 độ phân giải 8

- **Là gì:** ô hiện có cạnh 0,75 km, diện tích 1,46 km², nằm giữa H3 độ phân giải 8 (0,737 km²) và 7 (5,16 km²), không khớp mức nào.
- **Vì sao:** kích thước ô cần có căn cứ; H3 là lưới các nền tảng gọi xe dùng để đo cung–cầu theo ô. Đằng nào cũng sinh lại toàn bộ dữ liệu, nên đổi lúc này không tốn thêm một lần chạy.
- **Ở đâu:** `config/default.yaml` (file chung); `tests/test_engine.py` (đang kiểm cứng 37 ô).
- **Làm gì:**
  - chọn **độ phân giải 8**: cạnh **0,533 km**, để diện tích ô bằng diện tích trung bình của ô H3 (0,737 km²). Cạnh trung bình H3 là 0,531 km, nên hai số khớp nhau;
  - chọn **bán kính lưới R = 4**: 61 ô, khoảng 45 km², gần quy mô thành phố hiện tại (54 km²). Mặt xuyến với R = 4 đã được kiểm trong spec (mọi ô có đủ 6 ô kề);
  - giữ **mật độ cầu theo diện tích**: nhân lượng khách mỗi ô theo tỷ lệ diện tích (khoảng 0,5 lần), rồi để bước hiệu chỉnh 1.7 chỉnh tiếp lượng khách và số xe;
  - sửa test đang giả định 37 ô.

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

### 1.3. Chặn độ căng dự báo ở 10 (KN 2.3)

- **Là gì:** với phạm vi theo ô, độ căng có thể bằng vô cùng và được đưa thẳng vào hàm điểm, trong khi mô hình được học trên dữ liệu đã chặn ở 10.
- **Ở đâu:** `sim/policies/threshold.py` (Tình).
- **Làm gì:** chặn ở 10 cho mọi trường hợp; PR nhỏ cho Tình duyệt.

### 1.4. Thêm biến động tự nhiên và sửa lịch ca sáng (Q4, Q20, KN 5.1)

- **Là gì:** hiện mỗi ngày lặp lại y hệt (cùng lịch ca, cùng hình dạng cầu, không có cú sốc), nên thiếu xe chỉ rơi vào 5–8h.
- **Vì sao:** khi thiếu xe đoán được bằng giờ, không thể chứng minh việc đo độ căng theo vùng có giá trị. Lúc 7h, simulator chỉ có 25% số xe so với đỉnh, trong khi NYC là 70%.
- **Ở đâu:** module mới `sim/shocks.py`; sửa `demand.py`, `supply.py` (Hoàng); mục mới `shocks:` trong `config/default.yaml` và luồng ngẫu nhiên mới trong `rng.py` (file chung).
- **Làm gì:** dùng tham số tự đặt, chọn cho gần thực tế, ghi nhãn nguồn.
  - **Bắt buộc:** sự kiện ở địa điểm cố định (tạo thiếu xe theo khu vực); cầu dao động giữa các ngày; sửa lịch ca sáng.
  - **Tùy chọn:** mưa (cầu tăng, xe chậm), tài xế nghỉ độc lập, giờ vào ca lệch.
  - Mọi chính sách gặp **cùng một cú sốc**; chính sách **không được đọc** lịch cú sốc.
  - Chi tiết tham số chốt khi bắt đầu làm.

### 1.5. Thêm code không làm đổi số liệu (Q4–6, Q8, Q18, Q21, Q23; KN 3.1–3.3)

Làm cùng đợt để chỉ sinh dữ liệu một lần.

| Thêm gì | Để làm gì | Ở đâu |
|---|---|---|
| Phạm vi `city` cho tầng vùng | So tầng vùng theo độ căng toàn thành phố | `threshold.py`, `config.py` |
| Chính sách **oracle**, qua cổng riêng tới hệ số ẩn | Biết chính sách đề xuất lấp được bao nhiêu phần khoảng cách tối đa | `sim/policies/` (Tình) |
| Ghi độ căng trễ cho **mọi** chính sách, cộng cờ "slot trước cùng khối switchback" | Chia tác dụng theo độ căng mà không dính cạm bẫy biến hậu can thiệp | `policies/`, `schema.md` |
| Ghi lượt chạy dùng tính B, và `world_seed`, vào kết quả | Người đọc khỏi phải đoán (Q23); dễ gộp nhiều thế giới | `runner.py` |

### 1.6. Kiểm thử

- Tắt mọi khóa mới thì chạy như cũ.
- Cùng ngày thì cùng cú sốc dưới mọi chính sách.
- Không rò biến ẩn, không nhìn trước.
- Bất biến ngân sách.
- Nghiệm thu A1–A5 đạt.
- Oracle chỉ dùng được với chính sách ngưỡng.

### 1.7. Hiệu chỉnh lại

- **Là gì:** biến động và các bản sửa làm đổi mức trung bình của thị trường.
- **Làm gì:** chạy lại 5 chỉ tiêu hiệu chỉnh cũ, thêm chỉ tiêu **"tỷ lệ xe bận theo giờ"** để lịch ca sáng gần thực tế. Chỉ chỉnh lượng khách, số xe và lịch ca.

---

## Giai đoạn 2. Sinh dữ liệu cho hai thế giới

### 2.1. Sinh dữ liệu W0 và W1

- **Là gì:** W0 = simulator đã sửa lỗi, **không** biến động. W1 = đã sửa lỗi, **có** biến động.
- **Vì sao:** so hai thế giới là phép thử cho giả thuyết supply-aware. Dữ liệu cũ không dùng lại được vì code đã sửa lỗi.
- **Làm gì:** mỗi thế giới sinh:
  - dữ liệu luật cũ 28 ngày;
  - switchback 1 ô, 7 ô, toàn thành phố;
  - A/B theo khách;
  - GTE;
  - GTE với đội xe rất lớn (để tách phần "công suất" ở 4.4).

  Ghi lệnh vào `docs/datasets.md`.

---

## Giai đoạn 3. Phương pháp

### 3.1. Học lại mô hình chọn khách

- **Làm gì:** chạy lại DR-learner (theo mỗi USD) trên dữ liệu luật cũ mới.

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
  - quét θ (16 mức × 30 seed);
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
  - tính tương quan Qini–số chuyến **trong nhóm hàm theo mỗi USD**;
  - thử **Qini có tính chi phí** (trục hoành là tiền đã chi);
  - giải thích vì sao "chuyến thêm trên 100 USD" vẫn khớp số chuyến dù dữ liệu A/B bị chệch;
  - **kiểm tra lại cơ chế phản ví dụ:** trên W1 có ví dụ Qini cao mà ít chuyến **do cung** không.

### 4.7. Hai kiểm tra nhỏ (Q16, KN 5.2)

- Vì sao điều chỉnh theo đặc trưng (11,7) lại chệch hơn so thô (10,5). Một phần là do khác mốc (7,4 so với 6,9). So trên đúng mốc, độ chệch vẫn lớn hơn (+0,043 so với +0,036). Giả thuyết cho phần còn lại: luật cũ ưu tiên khách ít đi xe nhưng có $u$ cao; hai hướng chọn lọc bù trừ nhau.
- Đo tỷ lệ **bỏ chờ** trên thế giới mới (trước đây gần 0%).
- So **tác hại lúc 7–8h trước và sau khi sửa lịch ca** (Q20): nếu tác hại giảm mạnh, phần lớn tác hại cũ là do lịch ca; ghi rõ trong báo cáo.

### 4.8. Độ vững (Q18, Q19)

- **Làm gì:**
  - trên W1, quét ngân sách B (0,3 / 0,6 / 1,0 lần chi tiêu khi phát cho tất cả) và số xe (100% / 83% / 67% số xe sau hiệu chỉnh, tương ứng 240 / 200 / 160 của bản cũ) với chính sách khuyến nghị;
  - lặp bảng chính sách trên 3 `world_seed`.

### 4.9. (Nếu còn thời gian) Thêm giá hoặc độ dài chuyến vào mô hình (Q22)

- **Làm gì:** đưa vào cả mô hình hiệu ứng lẫn mô hình chi phí, so số chuyến.

---

## Giai đoạn 5. Viết lại báo cáo và sản phẩm trình bày

### 5.1. Viết lại Chương 3 và Chương 4

- **Làm gì:** Chương 3 thêm biến động, lưới H3 độ phân giải 8 và phương pháp ngưỡng theo độ căng; Chương 4 thay toàn bộ số, báo W0 và W1 cạnh nhau. Sửa luôn hai lỗi nhỏ còn tồn:
  - Bảng 4.1, dòng "Lưới": đổi "cùng bậc với ô H3" thành "theo ô H3 độ phân giải 8";
  - `phuluc.tex` dòng 165: thêm `\\` cuối dòng "Thư viện & …" (lỗi biên dịch `Misplaced \noalign` có từ bản gốc);
  - thêm số trang cho trích dẫn Castillo 2017 (con số 0,25–0,5, Q25).

### 5.2. Áp nguyên tắc viết số (Phần II mục 5)

- Tách rõ lợi ích **xếp theo mỗi USD** và **tầng vùng**.
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

- **Làm gì:** kênh bỏ chờ (nếu vẫn yếu); khách không đặt lại; số thế giới mô phỏng đã thử; ETA báo không tính hàng đợi đơn đang chờ.

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

### 5.6. (Tùy chọn) Trang so sánh chính sách trên dashboard

- **Làm gì:** chỉ làm sau 5.5. `dashboard/` là phần của Tình; Hoàng duyệt.

---

## Không làm

- **Ghép xe tối ưu theo lô (Hungarian):** nó chữa đúng hiện tượng cần đo.
- **Cho tài xế phản ứng theo voucher hoặc thu nhập:** ngoài phạm vi; giữ cung độc lập với chính sách.
- **Tối ưu hiệu năng:** đã đủ nhanh.
- **Học mô hình uplift trong `sim/`.**
- **Bản đồ thành phố thật (TP.HCM, NYC):** để hướng phát triển. Lưới vẫn là thành phố giả, nhưng kích thước ô theo H3 (việc 1.0).
- **Chạy thêm cặp `all_off`–`all_on` trong animation:** hướng dẫn ghi là tùy chọn; không cần.

---

## Phương án tối thiểu (nếu thiếu thời gian)

- Giai đoạn 0.
- 1.0–1.3, 1.5–1.7; ở 1.4 chỉ làm phần bắt buộc.
- Giai đoạn 2 và 3.
- Giai đoạn 4: chỉ 4.1, 4.2, 4.4.
- Giai đoạn 5, gồm cả 5.4b (trả lời mentor) và 5.5 (animation).

Phương án này vẫn trả lời được các câu hỏi nặng nhất của mentor, và đạt tiêu chí 1 và 4.
