# Kế hoạch triển khai simulator

Nguyên tắc:
- Làm **theo mốc**. Mỗi mốc kết thúc bằng test pass và một lần review của người (Hoàng hoặc Tình).
- Hai người làm **song song** theo `docs/phan_cong.md` (sprint, sở hữu file, điểm bàn giao).
  - Các review gate (P2, P3, P6) chặn **tích hợp và sinh dữ liệu** của mốc sau.
  - Module độc lập của mốc sau được viết trước trên nhánh riêng và test bằng đồ giả.
- Mỗi task là một PR nhỏ từ nhánh cá nhân (`develop1` của Tình, `develop2` của Hoàng) vào nhánh chung `develop`. Mỗi PR có mô tả: làm gì, test nào pass, lệch khỏi spec chỗ nào (nếu có).
- Mọi lệch khỏi `docs/spec.md` hoặc thay đổi tham số đều phải ghi vào `docs/decisions.md` (ngày, nội dung, lý do, người duyệt).

Thời gian dự kiến theo lịch thực tập: **tuần 3** gồm P0–P4, **tuần 4** gồm P5–P8, **tuần 5** dành cho phân tích và nghiệm thu (ngoài phạm vi file này). Lịch chi tiết theo sprint và theo người, gồm cả tuần 5, ở `docs/phan_cong.md`.

---

## Trước khi code: việc cần chốt

| Việc | Ai | Chặn mốc nào |
|---|---|---|
| D3 (π_θ hai tầng), D4 (slack), D5 (max_pickup_eta 30 phút): **đã chốt** theo YAML (`decisions.md` T-17) | Tình, Hoàng | — |
| Mức ngân sách B (`fraction = 0,3`) và `explore_frac = 0,05`: **đã chốt** (T-17) | Tình, Hoàng | — |
| Thống nhất hợp đồng dữ liệu NYC (spec §10, T-14) | Tình | P7 (làm sau P8 nếu còn thời gian) |

---

## P0. Khung dự án (0,5 ngày)

- **Làm:**
  - Cấu trúc thư mục theo spec §3.
  - `pyproject.toml`: Python 3.11, numpy, pandas, pyarrow, pyyaml, pytest.
  - `config.py` (load, kiểm khóa lạ, `--set`, hash) và `rng.py` (spec §5).
  - `cli.py` với lệnh `run` rỗng.
- **Xong khi:** `tests/test_config.py` pass; `rng_for` cho cùng khóa thì ra cùng số, khác khóa thì khác số.

## P1. Thế giới tĩnh (1 ngày)

- **Làm:**
  - M1 `space.py`: lưới, torus, D, T, ETA.
  - `population.py`: trọng số ô, rider, lịch ca tài xế.
  - M2 `demand.py`: Poisson, chọn rider, chọn đích, rút sẵn số ngẫu nhiên của session.
- **Xong khi:** test M1, M2 trong `tests.md` pass. In được bảng tóm tắt thế giới: số ô, thời gian T trung bình, số rider, số tài xế online theo giờ.

## P2. Vòng lặp lõi (1,5 ngày)

- **Làm:**
  - `state.py` (SoA) và `engine.py` (10 bước).
  - M4, M5, M6, M7, M8, M9, M11 (bản đủ để tính slack).
  - Chính sách `all_off` / `all_on`, chưa có ngân sách.
  - Log tối thiểu cho `policy_results`.
- **Xong khi:**
  - test M4–M9, M11 và tích hợp (`smoke_day`, `conservation`, `cooldown`, `driver_state_consistency`) pass;
  - chạy được `mode throughput_curve`.
- **Review gate:** người xem đồ thị throughput đầu tiên trước khi sang P3.

## P3. Hiệu chỉnh và hiệu năng (1 ngày)

- **Làm:**
  - Chạy kiểm thử [CAL] và A1, chỉnh các tham số `[assume]` theo thứ tự trong `tests.md` §4.
  - Profile và tối ưu để đạt A5.
- **Xong khi:**
  - **A1 pass** (có đoạn throughput giảm, slack < 0,45 ở vùng giảm);
  - **A5 pass** (≤ 30 giây / ngày);
  - mọi chỉ tiêu CAL nằm trong khoảng.
  - Cập nhật `default.yaml` và ghi `docs/decisions.md`.
- **Review gate:** nếu A1 không đạt sau khi thử các núm được phép, **dừng và báo**. Không đi tiếp, vì cả đề tài dựa trên hiện tượng này.

## P4. Chính sách và ngân sách (1,5 ngày)

- **Làm:**
  - `BudgetLedger` và `calibrate_budget`.
  - `LegacyPolicy` (ε cấp ô, nhắm rider, explore).
  - `ThresholdPolicy` (dự báo persistence và ar, hysteresis, hàm điểm, κ auto).
  - `scores.py` (random, heuristic_low_freq, loader).
- **Xong khi:** test M3, test chính sách pass; bất biến ngân sách giữ đúng trong 1 ngày chạy.

## P5. Thí nghiệm và logger đầy đủ (1 ngày)

- **Làm:**
  - M10: cụm 1 / 7 / all, switchback, rider_ab, burn-in.
  - M12: đủ các bảng theo `schema.md`, tách `observed/`, `hidden/`, `market/`.
  - `mode generate`.
- **Xong khi:** test M10, M12, `test_no_hidden_leak` pass; `generate` 2 ngày tạo đủ bảng đúng schema.

## P6. Runner và nghiệm thu (1 ngày)

- **Làm:** `mode evaluate`, `sweep_theta`, `gte`; chạy song song theo seed; bảng `theta_sweep`.
- **Xong khi:**
  - A2 pass (CRN);
  - A3 có số liệu;
  - `sweep_theta` với 12 θ × 10 seed chạy xong và vẽ được đường N(π_θ) theo θ.
- **Review gate:** người xem đường N(π_θ). Kiểm tra có điểm cực đại bên trong lưới θ không. Nếu đường phẳng, xem lại mức ngân sách và cường độ voucher.

## P7. Bản NYC (song song với Tình, 1–2 ngày)

> Hạ ưu tiên: làm sau P8 nếu còn thời gian (`docs/decisions.md` T-14).

- **Làm:** nạp dữ liệu theo spec §10, luật T gần/xa, vùng đệm, lấy mẫu 5–10%.
- **Xong khi:** chạy 1 ngày NYC không lỗi; A5 vẫn đạt với mức lấy mẫu đã chọn; so sánh vài chỉ số (số chuyến theo giờ, thời gian chuyến) với dữ liệu thật.

## P8. Sinh dữ liệu cho phân tích (0,5 ngày)

- **Làm:**
  - `generate` 28 ngày với chính sách cũ (dữ liệu quan sát có confounding).
  - `generate` 28 ngày với `cluster_switchback` ở cụm cấp 1, 7 và all.
  - `generate` 28 ngày với `rider_ab` (cần để đo độ chệch A/B theo rider, RQ3; T-16).
  - `gte` và `sweep_theta` với chính sách tham chiếu.
- **Xong khi:** thư mục `runs/` có đủ dữ liệu; `docs/datasets.md` mô tả từng bộ (config_hash, số ngày, chính sách, dung lượng).

---

## Rủi ro và cách xử lý

| Rủi ro | Dấu hiệu | Xử lý |
|---|---|---|
| Không tái tạo được WGC | A1 không có đoạn giảm | Tăng bán kính lưới, giảm tốc độ giờ cao điểm, tăng `max_wait`; báo mentor nếu vẫn không được |
| Quá chậm | A5 > 30 giây | Tối ưu theo spec §8; giảm `n_riders`; cuối cùng mới dùng numba |
| Đường N(π_θ) phẳng | Mọi θ cho N như nhau trong khoảng sai số | Kiểm tra B có quá lớn (không cần cắt) hay quá nhỏ; kiểm tra uplift CAL |
| Rò biến ẩn | `test_no_hidden_leak` fail | Chặn ở `SessionBatch`, không sửa test |
