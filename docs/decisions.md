# Nhật ký quyết định

File này ghi lại: mọi lệch khỏi `docs/spec.md`, mọi tham số được thêm hoặc đổi, và mọi câu hỏi chưa chốt.

Quy ước:
- Mỗi mục ghi ngày, nội dung, lý do và người duyệt.
- Khi một câu hỏi mở được trả lời, chuyển nó sang phần Nhật ký, ghi câu trả lời và người trả lời, rồi sửa spec, tests hoặc YAML tương ứng.

---

## Nhật ký

| Ngày | ID | Nội dung | Lý do | Người duyệt |
|---|---|---|---|---|
| 2026-09-30 | L1 | Config nhiều lớp: `--config` được lặp lại, file sau deep-merge đè file trước, rồi mới áp `--set`. `tests/fixtures/tiny.yaml` chỉ chứa các khóa khác `default.yaml`. | Không phải chép lại toàn bộ YAML cho cấu hình test; không đổi ngữ nghĩa tham số. | chờ duyệt |
| 2026-09-30 | L2 | Dataclass config không có giá trị mặc định: thiếu khóa là lỗi. YAML có khóa trùng cũng là lỗi. | `default.yaml` là nguồn duy nhất của tham số (quy tắc cứng 1). PyYAML mặc định lặng lẽ giữ khóa trùng cuối cùng. | chờ duyệt |
| 2026-09-30 | L3 | `config_hash` tính trên config **đã chuẩn hóa kiểu**, ví dụ `1` và `1.0` ở trường float cho cùng hash; không tính trên YAML thô. | Hai cách viết cùng một giá trị không được cho hai hash khác nhau. | chờ duyệt |
| 2026-09-30 | L4 | Kiểm tra khoảng giá trị (spec §9), gồm cả ràng buộc thời gian: `tick_s` chia hết 86400; `slot_min` chia hết 1440; một slot là số nguyên tick; `experiment.block_min` là bội của `slot_min`; `burnin_min < block_min`. | [report Bảng 3]: block switchback là bội số của slot. Spec §2 cần `slot_of_day` nguyên. | chờ duyệt |
| 2026-09-30 | L5 | `rng`: luồng WORLD băm với `world_seed` thay cho `run_seed`; các luồng khác dùng `run_seed`. Khi gọi WORLD chỉ truyền phần "…" của khóa (ví dụ mã phần thế giới). | Spec §5: WORLD không phụ thuộc `run_seed`. | chờ duyệt |
| 2026-09-30 | L6 | `hash64` = BLAKE2b 8 byte trên các số nguyên int64 little-endian. Mã luồng cố định: WORLD=1, DEMAND=2, SESSION=3, CELLSLOT=4, RIDER=5, DRIVER=6, SESSION_BATCH=7. Khóa phải là số nguyên (float, str bị từ chối). Test chốt cứng giá trị băm. | Hàm `hash()` của Python không ổn định giữa các tiến trình. Đổi hàm băm sẽ đổi mọi số ngẫu nhiên và làm hỏng khả năng tái lập dữ liệu. | chờ duyệt |
| 2026-09-30 | L7 | `requires-python >= 3.11` thay vì khóa cứng 3.11. Code viết theo cú pháp 3.11; test chạy bằng `.venv` Python 3.11. | Máy dev đang dùng 3.13 làm mặc định. | chờ duyệt |
| 2026-09-30 | L8 | Thêm `sim/__main__.py` (không có trong spec §3) để chạy được `python -m sim`. | Spec §7 dùng lệnh `python -m sim run`. | chờ duyệt |
| 2026-09-30 | L9 | Test tĩnh (`tests/test_rng.py`) cấm trong `sim/`: `import random`, `numpy.random.<hàm>` toàn cục và `default_rng`. Chỉ cho phép `np.random.Generator` (type hint) và `np.random.Philox` (chỉ trong `rng.py`). | Quy tắc cứng 4 (CRN). | chờ duyệt |
| 2026-09-30 | L10 | Đổi tên `docs/Supply-Aware Promotion Uplift.md` thành `docs/problem_statement.md`, file Survey thành `docs/survey.md`. | Tên có dấu cách, gạch dài và dấu cách trước `.md` gây lỗi khi gõ lệnh và tạo link. | chờ duyệt |

---

## Câu hỏi mở

Xếp theo mốc bị chặn. Không câu nào chặn P0.

### Q1. Simulator chính là ABM theo spec hay `marketplace_sim.py`? (ảnh hưởng toàn bộ kế hoạch)
- `docs/BaoCao_MaNguon.pdf` (29/09) kết luận: simulator chính là `marketplace_sim.py`; ABM 13 module chỉ là "bản rút gọn, tùy chọn, để kiểm tra ngoài". `docs/problem_statement.md` cũng dựa trên `marketplace_sim.py` (`--selfcheck`, các cột `util_lag`, `realized_*`).
- Trong khi đó CLAUDE.md, spec và plan (30/09) coi ABM là sản phẩm chính, và `marketplace_sim.py` không có trong repo.
- Liên quan: đề bài xếp repositioning vào "ngoài phạm vi", nhưng `reposition.enabled: true` là mặc định (quy tắc tĩnh).
- **Đề xuất:** xác nhận ABM là hướng hiện tại và ghi chú trong báo cáo mã nguồn rằng kết luận đó đã cũ. Nếu còn dùng `marketplace_sim.py` để đối chiếu thì đưa nó vào repo. Mentor xác nhận việc bật M9 mặc định.

### Q2. Đội xe khởi động lạnh lúc t = 0 (chặn P2)
- t = 0 là 00:00 (spec §2: `hour = (t % 86400) // 3600`). Ca sớm nhất bắt đầu lúc 6:00, nên **từ 00:00 đến 6:00 ngày đầu không có xe nào online**.
- Ở trạng thái dừng (mỗi ngày lặp cùng lịch ca), các ca bắt đầu 15–23 giờ kéo qua nửa đêm. Monte Carlo trên `shift_start_mixture` mặc định cho tỷ lệ đội xe online: 00:00 ≈ 40%, 01:00 ≈ 32%, 03:00 ≈ 18%, 05:00 ≈ 8%.
- Hệ quả: warm-up 60 phút không đưa hệ về trạng thái dừng. Với `days_per_run = 1`, khoảng 01:00–06:00 (5/24 cửa sổ đánh giá) gần như không có cung.
- **Đề xuất:** lúc t = 0, xe nào có ca "hôm trước" (theo lịch lặp) còn phủ t = 0 thì đặt `idle` tại ô xuất phát, `shift_end` theo lịch. Cách khác: dời t = 0 sang giờ khác, hoặc kéo dài warm-up.

### Q3. Cửa sổ đánh giá lệch ngày lịch, ảnh hưởng ngân sách "theo ngày" (chặn P4)
- Cửa sổ là [01:00 ngày 0, 01:00 ngày 1), nhưng ngân sách reset lúc 00:00 (t = 86400). Như vậy:
  - (a) warm-up 00:00–01:00 tiêu ngân sách của ngày 0;
  - (b) giờ cuối cửa sổ (00:00–01:00 ngày 1) nhận thêm một B mới, nên chi tiêu trong một cửa sổ 1 ngày có thể vượt B.
- Cùng vấn đề với "chi tiêu voucher trung bình mỗi ngày" của pilot (để tính B) và với κ auto (chi tiêu ≤ B tính trên khoảng nào).
- **Đề xuất:** ngày ngân sách d là [window_start + d·86400, window_start + (d+1)·86400). Trong warm-up thì chọn một trong hai: (i) không phát voucher; (ii) có ngân sách riêng, không tính vào B.

### Q4. Test M1 "`ETA_in(I)` giảm ngặt theo I" mâu thuẫn với sàn `eta_floor_min` (chặn P1)
- Với default, `ETA_in` chạm sàn 1 phút từ I ≥ 5 (giờ đêm, 22,5 km/h) và I ≥ 13 (cao điểm, 13,5 km/h), sau đó là hằng số. Test "giảm ngặt" không thể pass.
- **Đề xuất sửa `docs/tests.md`:** "không tăng theo I; giảm ngặt khi còn trên sàn". Chưa tự sửa test, cần người duyệt.

### Q5. `tiny.yaml` cần "2 giờ mô phỏng" nhưng chưa có khóa để biểu diễn (chặn test P1–P2)
- Cửa sổ dài `days_per_run × 1440` phút, với `days_per_run` nguyên ≥ 1.
- **Đề xuất:** thêm `time.window_min: null` (null nghĩa là `days_per_run × 1440`). Cần chốt luôn cách tính ngân sách ngày cho cửa sổ ngắn hơn 1 ngày (xem Q3).

### Q6. Hằng 1440 trong công thức `session_id` (chặn P1)
- `((day*1440 + tick_of_day)*N + cell)*1000 + k` chỉ đúng khi `tick_s = 60`. Nếu `tick_s < 60`, ID sẽ trùng nhau.
- **Đề xuất:** thay 1440 bằng `ticks_per_day = 86400 // tick_s`. Với cấu hình mặc định kết quả không đổi.

### Q7. Số ngẫu nhiên cho `score_fn = random` (chặn P1, vì danh sách số rút sẵn chốt ở P1)
- Spec §6 nói score random là "Uniform từ luồng SESSION", nhưng §4.2 không liệt kê số này trong các số rút sẵn. Nếu chỉ rút khi chính sách là random, thứ tự rút trong luồng SESSION sẽ phụ thuộc chính sách, tức phá CRN.
- **Đề xuất:** luôn rút sẵn `u_score` ở cuối danh sách §4.2, sau `e_cancel`.

### Q8. A1: đội xe trong `throughput_curve` (chặn P2)
- Spec §7 chỉ đặt `hour_profile` và `speed_factor_by_hour` thành hằng số. Số xe online vẫn đổi theo `shift_start_mixture`, nên không có "fleet cố định, trạng thái ổn định" như A1 yêu cầu. Spec cũng chưa nói đo `completed_per_h` trên khoảng thời gian nào.
- Ghi chú: report đo đường throughput bằng cách "giữ nhu cầu cố định, giảm số xe", còn tests.md A1 giữ số xe và quét cầu. Cả hai đều hợp lệ; spec thắng.
- **Đề xuất:** trong `throughput_curve`, mọi xe online suốt lượt chạy (bỏ lịch ca), và đo trên toàn cửa sổ sau warm-up.

### Q9. Định nghĩa utilization (chặn P2)
- Spec §4.11 dùng `(E + O) / (I + E + O)`; report M11 dùng `(L − I) / L`, với L là số xe online, gồm cả xe đang repositioning. Hai công thức khác nhau khi có xe repositioning, mà M9 bật mặc định.
- **Đề xuất:** giữ công thức spec và ghi rõ xe repositioning không được tính.

### Q10. Định nghĩa slack không thống nhất giữa các tài liệu (thuộc D4, chờ mentor)
- Spec và report dùng `slack = I / E`. `BaoCao_MaNguon.pdf` Bảng 7 viết "(xe − đang chở) / đang đón", tức (I + E) / E = 1 + I/E.
- Ngưỡng WGC 0,25–0,45 và `theta_grid` chỉ có nghĩa với I/E.
- **Đề xuất:** đối chiếu lại Castillo et al. (2025) và sửa tài liệu bị sai.

### Q11. Danh sách cột ẩn: CLAUDE.md và schema.md khác nhau (chặn P5)
- CLAUDE.md quy tắc 3 dùng tên `alpha, beta, delta, max_wait`. `docs/schema.md` dùng `beta_price, beta_eta, delta_promo, max_wait_min` và có thêm `e_cancel, u_book`.
- **Đề xuất:** `test_no_hidden_leak` lấy hợp của hai danh sách, và schema.md là nguồn chuẩn.

### Q12. A2(b): `all_on` có áp ngân sách không? (chặn P6)
- So sánh π1 = all_on với π2 = threshold θ = 0,3 (có ngân sách). Nếu all_on không áp ngân sách, hai chính sách không cùng B.

---

## Ghi chú kỹ thuật (đã kiểm, không cần quyết định)

- Kiểm bằng script: với R = 1..4, torus cho mỗi ô đúng 6 ô kề phân biệt và khoảng cách tối đa bằng R; bất đẳng thức tam giác đúng (đã kiểm với R ≤ 3). Với R = 3, cụm cấp 7 có kích thước [3, 3, 4, 6, 7, 7, 7] và mỗi ô cách tâm cụm ≤ 1. Đều khớp spec.
- Với R = 3 và tốc độ thấp nhất (0,75 × 18 km/h), T xa nhất (3 vành) ≈ 22,5 phút, nhỏ hơn `max_pickup_eta_min = 30`. Ở cấu hình mặc định, nhánh "ETA > max_pickup_eta" không bao giờ xảy ra: mọi order được ghép ngay khi còn bất kỳ xe rảnh nào trong lưới. Đúng ý đồ WGC, nhưng test M5 cho giới hạn này phải đặt giới hạn nhỏ hơn trong fixture.
- `T[a, a, h]` đúng bằng `ETA_in(1, h)` vì `nn_const = intra_cell_dist_factor = 0,5`. Không sai, chỉ là trùng hợp đáng biết khi đọc số.
- `docs/survey.md` bị hỏng khi export: mất toàn bộ ký tự `/ \ : | ?`, nên URL, công thức LaTeX và bảng đều vỡ. Cần export lại từ bản gốc.
