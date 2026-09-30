# CLAUDE.md — Simulator gọi xe (Supply-Aware Promotion Impact Framework)

Đọc file này đầu tiên mỗi phiên làm việc.

## Dự án là gì

Simulator agent-based cho ride-hailing (solo, không đi chung) trên lưới ô lục giác. Mục đích:
- sinh dữ liệu có confounding kiểm soát được;
- đo giá trị thật của chính sách voucher theo vùng và khung giờ;
- tìm ngưỡng căng cung θ\* để tắt khuyến mãi.

Chỉ tiêu chính là **N(π) = số chuyến hoàn thành** dưới cùng ngân sách voucher B. Lợi nhuận V(π) là chỉ tiêu phụ.

## Tài liệu (đọc theo thứ tự)

1. `docs/Simulation_design_fix.pdf`: báo cáo thiết kế. Nói *vì sao*.
2. `docs/spec.md`: đặc tả cài đặt. Nói *làm thế nào*. **Nguồn sự thật cho code.**
3. `config/default.yaml`: mọi tham số.
4. `docs/schema.md`: định dạng dữ liệu đầu ra.
5. `docs/tests.md`: kiểm thử và tiêu chí đạt.
6. `docs/plan.md`: các mốc.
7. `docs/phan_cong.md`: phân công theo sprint cho Tình và Hoàng, sở hữu file, điểm bàn giao. **Chỉ làm task hiện tại của mình.**
8. `docs/decisions.md`: nhật ký quyết định, mọi lệch khỏi spec và mục **Câu hỏi mở**.

Tài liệu nền (không phải nguồn sự thật cho code): `docs/problem_statement.md` (đề bài gốc), `docs/survey.md` (khảo sát; bản export bị lỗi định dạng), `docs/BaoCao_*.pdf`.

## Stack và lệnh

- Python 3.11, numpy, pandas, pyarrow, pyyaml, pytest. Không thêm thư viện khác nếu chưa hỏi. `numba` chỉ được dùng ở P3 nếu cần, và phải có fallback.
- Cài đặt: `py -3.11 -m venv .venv`, kích hoạt, rồi `pip install -e ".[dev]"`.
- Test nhanh: `pytest -q`
- Test chậm (nghiệm thu): `pytest -q -m slow`
- Chạy: `python -m sim run --mode <mode> --config config/default.yaml [--config overlay.yaml] [--set a.b=c]`
- Profile: thêm `--profile`

## Quy tắc cứng (không được vi phạm)

1. **Không hard-code tham số.** Mọi hằng số lấy từ `config/default.yaml`. Cần tham số mới thì thêm vào YAML kèm chú thích nguồn và ghi `docs/decisions.md`.
2. **Không nhìn trước.** Quyết định ở slot k chỉ dùng snapshot của các slot < k, qua `SnapshotView`.
3. **Không rò biến ẩn.**
   - Chính sách và dữ liệu `observed/`, `market/` không được chứa cột nào trong **danh sách ẩn của `docs/schema.md`** (`u_latent`, alpha, beta_price, beta_eta, delta_promo, max_wait_min, propensity_true, p_request_*, direct_request_effect_fixed_market, và mọi số rút sẵn của session).
   - Riêng `LegacyPolicy` được dùng `u_latent` qua `LegacyHiddenView`. Các số rút sẵn `u_target`, `u_explore`, `u_explore_arm`, `u_score` được đưa vào `SessionBatch` cho chính sách dùng; chính sách không tự rút số.
4. **CRN.**
   - Mọi số ngẫu nhiên lấy qua `rng.rng_for(stream, *key)` với khóa ổn định (session_id, cell, tick, driver_id…).
   - Không dùng `np.random.*` toàn cục, không dùng `random`.
   - Đổi chính sách không được làm thay đổi số ngẫu nhiên của bất kỳ session nào.
5. **Cung độc lập với chính sách.** `supply.early_exit_enabled` mặc định false. Repositioning chỉ dùng trọng số tĩnh, không đọc cầu hay snapshot hiện tại.
6. **Không làm mất hiện tượng cần đo.** Không giảm `max_pickup_eta_min`, không giới hạn tìm xe ở vành 1, không bỏ hủy trong lúc xe đi đón để "cho nhanh" hoặc "cho đẹp".
7. **Hiệu năng.**
   - Trạng thái xe, order, session lưu dạng struct-of-arrays numpy. Không tạo object Python cho mỗi xe hay khách trong vòng lặp nóng.
   - Không lặp qua toàn bộ đội xe mỗi tick.
   - Mục tiêu ≤ 30 giây / ngày mô phỏng.
8. **Ngân sách.** Bất biến `spent + committed + reserved ≤ B` phải luôn đúng khi `budget.enforce = true`.
9. **Không thêm tính năng ngoài spec** (surge pricing, pooling, học mô hình uplift…). Học mô hình uplift chỉ làm trong `analysis/` (tuần 5), không bao giờ trong `sim/`.

## Cách làm việc

- Đọc mục tương ứng trong `spec.md` và `tests.md` trước khi code một module.
- Viết test trước hoặc cùng lúc với code. Mốc chỉ xong khi các test của mốc pass.
- Mỗi task là một nhánh (`tinh/<task>` hoặc `hoang/<task>`) và một PR nhỏ vào `develop1`; người kia review. Trong mô tả PR ghi: test nào pass, lệch spec ở đâu.
- **Hai người làm song song** theo `docs/phan_cong.md`:
  - chỉ sửa file mình sở hữu (mục 2 của file đó);
  - cần sửa file của người kia thì mở PR nhỏ để chủ file review;
  - file chung chỉ sửa qua PR có cả hai duyệt;
  - trước khi dùng thứ người kia bàn giao, chạy đúng phần "Người nhận kiểm tra" trong bảng bàn giao.
- **Khi spec mơ hồ hoặc mâu thuẫn:** dừng lại, ghi câu hỏi vào `docs/decisions.md` mục "Câu hỏi mở", và hỏi người. Không tự chọn một cách rồi đi tiếp.
- **Khi test nghiệm thu không đạt** (đặc biệt A1, đường throughput): báo cáo số liệu. Không nới tiêu chí đạt, không sửa test cho pass.
- Code comment và docstring bằng tiếng Anh; tài liệu trong `docs/` bằng tiếng Việt.
- Tên biến khớp tên trong `spec.md` và `schema.md` (ví dụ `slack`, `cell_propensity`, `pickup_eta_min`).

## Cấu trúc thư mục

```
sim/            # mã nguồn (spec §3)
tests/          # pytest; fixtures/tiny.yaml cho test nhanh
config/         # default.yaml
docs/           # thiết kế, spec, schema, tests, plan, phan_cong, decisions
analysis/       # phân tích tuần 5 (tạo khi cần; sim/ không import từ đây)
runs/           # output (không commit)
```

## Trạng thái hiện tại

- Sprint đang làm: **S0**, làm chung: PR hợp đồng giao diện + khung chạy được (xem `docs/phan_cong.md`).
  - 1. Tình: S0; tiếp theo T1.1–T1.5.
  - 2. Hoàng: S0; tiếp theo H1.1–H1.4.
- Mốc P0 đã xong trên `develop1`, chờ Hoàng review (gate P0).
- Câu hỏi Q1–Q16 đã chốt ngày 30/09 (`decisions.md` T-01…T-18). D3, D4, D5, mức B và `explore_frac` tạm chốt theo YAML; mentor có thể đổi bằng config, không sửa code.
