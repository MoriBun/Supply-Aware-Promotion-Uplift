# Phân công theo sprint

Người làm: **1. Phan Văn Tình**, **2. Nguyễn Huy Hoàng**. Người hướng dẫn: Nguyễn Bảo Long.

Phạm vi: simulator P1–P8 (`docs/plan.md`) và phân tích tuần 5 (`docs/problem_statement.md` §7–8).

**Giả định:** ABM theo `docs/spec.md` là simulator chính (Q1 trong `docs/decisions.md`). Nếu mentor chọn `marketplace_sim.py` thì phải lập lại kế hoạch này.

Quy ước ký hiệu:
- `T1.1` là task của Tình, `H1.1` là task của Hoàng (số đầu = sprint);
- `B0`–`B8` là các điểm bàn giao giữa hai người;
- `Q..` là câu hỏi mở trong `docs/decisions.md`.

---

## 1. Nguyên tắc để hai người độc lập

1. **Hợp đồng trước:** Sprint 0 chốt chữ ký hàm, tên cột và khóa config giữa hai luồng. Sau đó mỗi người code phía mình.
2. **Khung chạy được:** module phía bên kia luôn có một stub tối thiểu chạy được, nên không ai phải chờ ai để chạy thử.
3. **Mỗi file một chủ.** File chung chỉ sửa qua PR có cả hai duyệt. Cần sửa file của người kia thì mở PR nhỏ để chủ file review.
4. **Test bằng đồ giả** (`tests/fakes.py`). Các điểm tích hợp có lịch và có checklist (mục 5).
5. **Review chéo:** PR của người này do người kia duyệt, để cả hai hiểu toàn bộ pipeline, không thành hai "silo" (đề bài §7).

**Git:**
- `develop1` là nhánh tích hợp.
- Mỗi task một nhánh `tinh/<task>` hoặc `hoang/<task>`, PR vào `develop1`, người kia review.
- Sau mỗi gate (P0, P2, P3, P6), gộp `develop1 → main`.

**Gate:** P2 (đồ thị throughput), P3 (A1) và P6 (đường N(π_θ)) chặn **tích hợp và sinh dữ liệu**. Chúng không chặn việc viết module độc lập của mốc sau trên nhánh riêng.

---

## 2. Phân vai và sở hữu file

| | 1. Tình: ngân sách, chính sách, giám sát, dữ liệu | 2. Hoàng: lõi mô phỏng (đường găng) |
|---|---|---|
| Module | `pricing.py` (M3), `budget.py`, `policies/*` (gồm `fixed`), `experiment.py` (M10), `monitor.py` (M11 + SnapshotView), `logger.py` (M12), `runner.py`, `cli.py` | `space.py` (M1), `population.py`, `demand.py` (M2), `state.py`, `choice.py` (M4), `matching.py` (M5), `trips.py` (M6), `cancel.py` (M7), `supply.py` (M8), `reposition.py` (M9), `engine.py` |
| Test | `fakes`, `test_pricing` (giá + ledger), `test_policies`, `test_experiment`, `test_monitor`, `test_logger`, `test_runner`, `test_cli`, `test_acceptance` (A2, A3) | `test_space`, `test_demand`, `test_choice`, `test_matching`, `test_trips_cancel`, `test_supply`, `test_integration`; A1, CAL, A5, A4 |
| Khác | P6, P8, `docs/datasets.md`; tuần 5: đánh giá và phân bổ; NYC phía dữ liệu | P3 (chỉ Hoàng sửa giá trị `default.yaml` trong S3); tuần 5: ước lượng; NYC phía simulator |

**Chung (PR cả hai duyệt):**
- File: `sim/config.py`, `sim/rng.py`, `sim/__init__.py`, `sim/__main__.py`, `docs/*`, `CLAUDE.md`, `README.md`, `pyproject.toml`, `tests/__init__.py`, `tests/conftest.py`, `tests/fixtures/`, `tests/test_config.py`, `tests/test_rng.py`.
- Khóa mới trong `config/default.yaml` chỉ thêm qua PR chung, vì `config.py` từ chối khóa lạ.
- Giá trị trong `default.yaml` sửa theo mục:
  - Hoàng: `space`, `time`, `demand`, `riders`, `matching`, `cancel`, `supply`, `reposition`;
  - Tình: `pricing`, `voucher`, `budget`, `policy`, `experiment`, `monitor`, `sweep`, `generate`, `gte`.
  - Riêng Sprint 3 chỉ Hoàng sửa giá trị (hiệu chỉnh).
- `docs/decisions.md`: thêm dòng ở cuối, ID mới có tiền tố `H-` (Hoàng) hoặc `T-` (Tình) để khỏi trùng.

---

## 3. Các sprint

### Sprint 0: Hợp đồng và khung chạy được (ngày 1, cả hai)

**Việc chung:**
- Hoàng review P0 trên `develop1`; gộp `develop1 → main` (gate P0); xóa nhánh trống `p0-skeleton`.
- ~~Đội tự chốt Q4, Q5, Q6, Q7, Q9, Q11, Q15~~ **Đã chốt toàn bộ Q1–Q16 ngày 30/09** (`decisions.md` T-01…T-18). Hoàng đọc và phản đối trong S0 nếu không đồng ý điểm nào.
- Hoàng gửi mentor bản tóm tắt T-01…T-18 để xác nhận, nhấn mạnh T-03 (kỳ ngân sách), T-12 (all_on có ngân sách) và T-14 (hạ ưu tiên NYC). T-01 và T-17 đã chốt, không cần mentor xác nhận.

**PR "hợp đồng + khung chạy được"** (làm cặp, chỉ chữ ký, dataclass và stub):
1. **`state.py`:**
   - enum trạng thái xe và order;
   - cột SessionBuffer/OrderBuffer theo `schema.md` (dtype, bước nào ghi);
   - mảng DriverState (spec §8);
   - bộ đếm theo ô `idle/enroute/ontrip/waiting_count[N]` và `SlotCounters`.
2. **`rng.py`:**
   - thứ tự rút số cố định của luồng SESSION, kết thúc bằng `u_score` (T-07);
   - `session_id` tính theo `ticks_per_day` (T-06);
   - mã `kind` số nguyên cho CELLSLOT (`cluster_level: all` là chuỗi, `rng_for` sẽ từ chối).
3. **`World`:**
   - các trường: N, `cell_q/r`, D, T, diện tích ô, `w`, rider kèm `zf`, lịch ca, cửa sổ đánh giá, mặt nạ ô tính vào N(π);
   - hàm `quote_eta(...) -> (eta_min, no_supply)`.
4. **`policies/base.py`:**
   - cài thật các dataclass: Policy, `CellDecision` (+ `s_hat`, `cluster_id`, `block`, `in_burnin`), `OfferDecision` (+ `propensity_true`, `budget_blocked`), LegacyHiddenView (lấy `u_latent`, `zf` theo `rider_id`);
   - `SessionBatch`: tên cột theo schema, thêm `rider_id` và `u_target`, `u_explore`, `u_explore_arm`, `u_score`. Chính sách không được tự gọi `rng_for(SESSION, …)`;
   - `SnapshotView`: trả NaN trước lần công bố đầu, báo lỗi khi đọc slot ≥ k.
5. **`budget.py`:**
   - API theo `session_id`, tiền tính bằng cent nguyên;
   - sổ riêng cho từng kỳ ngân sách neo theo cửa sổ, warm-up là kỳ −1 (T-03); engine chỉ báo `open_time` của session, phần còn lại là việc của ledger.
6. **`engine.run(cfg, world, policy, rng, log_level, profile) -> RunResult`:**
   - RunResult đủ trường cho mọi mode: `mean_slack`, `promo_on` theo (ô, slot), chi tiêu theo ngày ngân sách, `(score, v, completed)` của mỗi session được phát (cho κ auto);
   - N(π), V(π) chỉ tính ở engine.
7. **Stub chạy được:** ledger nhánh `enforce=false`, `pricing.quote` nhánh all_off, monitor rỗng.
8. **Config:**
   - ~~thêm khóa mới~~ đã thêm ngày 30/09 (T-18): `time.window_min`, `supply.shift_mode`, `throughput.*`, `runner.n_procs`. Về sau chỉ đổi giá trị YAML, không phải sửa `config.py`;
   - bỏ các assert giá trị sẽ còn hiệu chỉnh (ví dụ `grid_radius == 3`) khỏi `test_config.py`.

### Sprint 1 (ngày 2–4)

| 1. Tình | 2. Hoàng |
|---|---|
| T1.1 `budget.py` đầy đủ (enforce, bất biến, reset ngày) + test ledger trong `test_pricing.py` | H1.1 `space.py` + `test_space.py` → **PR sớm** (B1) |
| T1.2 `monitor.py`: công bố snapshot theo slot, lag slot/ngày, assert không nhìn trước + `test_monitor.py` với bộ đếm giả | H1.2 `population.py`, `demand.py` + `test_demand.py`. Đo chi phí `rng_for` cho từng session ngay; nếu chậm thì dùng SESSION_BATCH từ đầu, vì đổi về sau sẽ đổi mọi số ngẫu nhiên |
| T1.3 `tests/fakes.py`, `policies/scores.py` + test | H1.3 `state.py` (SoA, tăng gấp đôi, bộ đếm theo ô), `choice.py` + `test_choice.py` |
| T1.4 `runner.py` khung: `run_id`, chạy nhiều seed (engine truyền dạng `"module:function"` vì Windows dùng spawn), ghi `policy_results`, mode `throughput_curve` trên engine giả; nối `cli.py` (B4) | H1.4 `supply.py`: ca làm tuần hoàn và khởi tạo t = 0 (T-02), chỉ rời khi rảnh, `shift_mode = always_on` (T-08) + phần M8 của `test_supply.py`; in bảng tóm tắt thế giới |
| T1.5 (bỏ, NYC hạ ưu tiên theo T-14; dùng thời gian này cho T1.4) | |

### Sprint 2 (ngày 5–8)

| 1. Tình | 2. Hoàng |
|---|---|
| T2.1 `pricing.py` đầy đủ (giá gốc, voucher, lớp voucher: `cell_state` khi đổi slot, `offer`, giữ ngân sách theo `session_id`, điền trường thí nghiệm) + `policies/fixed.py` → **giữa sprint** (B3) | H2.1 `matching.py` + `test_matching.py` |
| T2.2 `experiment.py` M10 + `test_experiment.py` (cần B1) | H2.2 `trips.py`, `cancel.py` (gọi ledger đúng chỗ) + `test_trips_cancel.py` |
| T2.3 `legacy.py`, `threshold.py`, `policies/experiment.py`, factory + `test_policies.py` (dùng đồ giả) | H2.3 `reposition.py` + phần M9 của `test_supply.py` |
| T2.4 runner: `evaluate`, `gte`, `sweep_theta` (bảng `theta_sweep`), `calibrate_budget`, κ auto, `generate` trên engine giả | H2.4 `engine.py` (10 bước, warm-up/cool-down/Truncated) + 4 test tích hợp |

**Cuối S2: Tích hợp 1 + Gate P2** (cả hai):
- all_off qua lớp voucher cho N, V giống hệt (`==`) khi chạy bằng stub.
- Chạy với all_on/all_off: `smoke_day`, `conservation`, `cooldown`, `driver_state_consistency`, không nhìn trước, A2(a), A2(c).
- Chạy `throughput_curve`; cả hai xem đồ thị.

### Sprint 3 (ngày 9–10)

| 1. Tình | 2. Hoàng |
|---|---|
| T3.1 Tích hợp P4 trên engine thật: bất biến ngân sách 1 ngày (all_on có ngân sách), nhả reserved/committed, reset ngày, `calibrate_budget`, `smoke_day` với mọi chính sách | H3.1 Làm A5 trước, đo với `policy.name=all_on`, vì tối ưu có thể đổi cách rút số và làm lệch kết quả hiệu chỉnh |
| T3.2 `logger.py` đủ bảng, tách observed/hidden/market/meta + `test_logger.py`, `test_no_hidden_leak` trên `generate` 2 ngày | H3.2 P3: CAL + A1, chỉnh các tham số `[assume]` theo thứ tự `tests.md` §4, ghi `decisions.md` |
| T3.3 Khung đánh giá tuần 5: N(π)/V(π) có CI, Qini/AUUC (thô, gộp giá trị trùng) trên dữ liệu 2 ngày | **Gate P3** cuối sprint (B6) |

### Sprint 4 (ngày 11–12)

| 1. Tình | 2. Hoàng |
|---|---|
| T4.1 Ngay sau Gate P3: chạy lại `calibrate_budget`; `generate` 28 ngày cho switchback cụm 1/7/all, `rider_ab`, `gte`, legacy → B7a | H4.1 Đo lại A5 với chính sách mặc định (threshold, κ auto) |
| T4.2 P6: κ auto, A2(b), A3, sweep 12 θ × 10 seed, vẽ N(π_θ) → **Gate P6** | H4.2 Bắt đầu ước lượng trên dữ liệu B7a: τ̂(x) nền đơn giản (để kịp B8), hiệu ứng theo bin `slack_lag`, θ̂ có CI, A4 |
| T4.3 Sau Gate P6: sweep tham chiếu; sinh lại legacy nếu B đổi; tag commit + `config_hash`; `docs/datasets.md` → B7b | H4.3 Review P6/P8 |

### Sprint 5: Phân tích (ngày 12–14, chồng S4)

Chung: chốt định nghĩa ŝ và chỉ số căng cung dùng cho cả θ̂ và θ\*, để so được.

| 1. Tình: đánh giá và phân bổ | 2. Hoàng: ước lượng |
|---|---|
| T5.1 Bảng N(π), V(π) dưới cùng B: all_off, all_on, random, τ̂(x), τ̂(x,s), π_θ̂. Chạy trước với score random/heuristic | H5.1 Ngày đầu: giao score_fn nền + parquet dự đoán (B8) |
| T5.2 Tìm ví dụ Qini cao hơn mà N(π) thấp hơn | H5.2 DR-learner trên `completed` (legacy + lát explore) → τ̂(x); τ̂(x, s) với `slack_lag_*` |
| T5.3 Interference: GTE vs `rider_ab` vs switchback cụm 1/7/all; độ nhạy theo `u_latent` | H5.3 Confounding: ước lượng naive vs explore/switchback; θ̂ vs θ\* |

Code phân tích đặt trong `analysis/`, không trong `sim/`. Không bao giờ nối (join) dữ liệu `hidden/` vào dữ liệu huấn luyện. Thư viện: extras `[analysis]` gồm scikit-learn, lightgbm, scikit-uplift, matplotlib; DR-learner tự viết, không dùng causalml (T-13).

### Sprint 6: Báo cáo và seminar (ngày 14–15)
- Tình: simulator và kiểm định (A1–A5, CAL, dữ liệu), đánh giá chính sách, Qini vs N(π), interference.
- Hoàng: ước lượng, θ̂ vs θ\*, confounding.
- Cả hai: bảng ba nguồn sai số, slides 30 phút, review chéo, dọn code.

### Nếu còn thời gian: P7 NYC (làm sau P8, T-14)
- Tình: 5 file theo spec §10 + script kiểm tra hợp đồng.
- Hoàng: nạp dữ liệu NYC, luật T gần/xa, vùng đệm, lấy mẫu 5–10%, A5 trên NYC.

---

## 4. Bàn giao (phụ thuộc bắt buộc)

Người nhận **kiểm tra trước khi dùng**. Khi giao xong, người giao điền ngày vào cột "Xong".

| ID | Từ → Đến | Bàn giao | Khi | Người nhận kiểm tra | Nếu trễ | Xong |
|---|---|---|---|---|---|---|
| B0 | cả hai | PR hợp đồng + khung | cuối S0 | `pytest -q`; engine stub chạy all_off; tên cột khớp `schema.md` | chưa vào S1 | ☐ |
| B1 | Hoàng → Tình | `space.py` | giữa S1 | `test_space` pass; cụm R = 3 ra [3,3,4,6,7,7,7] | Tình làm T2.3 trước T2.2 | ☐ |
| B2 | Tình → Hoàng | `budget.py` đầy đủ | cuối S1 | test ledger pass; API đúng hợp đồng | Hoàng dùng `enforce=false` | ☐ |
| B3 | Tình → Hoàng | `pricing.py` + `fixed` + `monitor.py` | giữa S2 | all_off cho N, V `==` stub; SnapshotView báo lỗi khi nhìn trước | Hoàng test bằng stub, dời tích hợp 1 | ☐ |
| B4 | Tình → Hoàng | mode `throughput_curve` | cuối S1 | chạy với engine giả, đúng cột `results/throughput_curve` | dời Gate P2 | ☐ |
| B5 | Hoàng → Tình | `engine.run` thật | cuối S2 | 4 test tích hợp pass; RunResult đủ trường | Tình tiếp tục với engine giả | ☐ |
| B6 | Hoàng → Tình | `default.yaml` đã hiệu chỉnh | cuối S3 | A1, A5, CAL đạt; bảng hiệu chỉnh trong `decisions.md`; `config_hash` mới | không chạy P6/P8 | ☐ |
| B7 | Tình → Hoàng | (a) switchback, `rider_ab`, `gte`, legacy; (b) sweep + `datasets.md` | (a) đầu S4, (b) cuối S4 | test schema + no-leak pass trên dữ liệu; `config_hash` khớp `datasets.md` | Hoàng dùng dữ liệu 2 ngày từ T3.2 | ☐ |
| B8 | Hoàng → Tình | score_fn τ̂ + parquet dự đoán | ngày đầu S5 | nạp được trong tiến trình con; tất định; chỉ đọc cột của batch | Tình chạy random/heuristic | ☐ |

---

## 5. Test nào ai viết, chạy đủ từ sprint nào (theo `docs/tests.md`)

| Test | Người | Viết | Chạy đủ khi |
|---|---|---|---|
| M1, M2, M4, M8 | Hoàng | S1 | S1 |
| M5, M6/M7, M9 | Hoàng | S2 | S2 |
| 4 test tích hợp | Hoàng | S2 (chạy trước với stub) | cuối S2 (cần B3) |
| M3 (giá + ledger) | Tình | S1–S2 | S3: bất biến 1 ngày, nhả ngân sách, reset |
| M11 (slack, không nhìn trước, lag ngày) | Tình | S1 | cuối S2 |
| M10 | Tình | S2 | S2 (cần B1) |
| Chính sách | Tình | S2 | S3 (SessionBatch thật), S4 (κ auto) |
| M12, no-leak; M4 "chỉ có trong hidden/"; `smoke_day` mọi chính sách | Tình | S3 | S3 |
| A1, CAL | Hoàng | S3 | S3 |
| A5 | Hoàng | S3 (all_on) | S4 (chính sách mặc định) |
| A2(a)(c) / A2(b), A3, sweep θ | Tình | cuối S2 / S4 | cuối S2 / S4 |
| A4 | Hoàng | S4 | S4–S5 |

---

## 6. Câu hỏi cần chốt, theo hạn

Q1–Q16 đã chốt ngày 30/09 (`docs/decisions.md`, T-01…T-18). Bảng dưới ghi ai bị ảnh hưởng và mentor cần xác nhận trước khi nào.

| Hạn | Quyết định | Ảnh hưởng |
|---|---|---|
| Trước S1 | T-06, T-07 (session_id, `u_score`), T-11 (cột ẩn), T-15 (bộ đếm) | hợp đồng S0, `demand.py`, `monitor.py` |
| Trước S2 | T-02 (ca tuần hoàn), T-08 (`throughput_curve`), T-09/T-10 (utilization, slack) | `supply.py`, `runner.py`, `monitor.py` |
| Trước S3 | T-03 (kỳ ngân sách), T-12 (A2(b)) | `budget.py`, `pricing.py`, `test_acceptance` |
| Trước S4 (mentor xác nhận) | T-13 (thư viện), T-16 (`rider_ab`) | P8, tuần 5 |
| Bất kỳ lúc nào | T-14 (NYC làm sau P8) | P7 |

---

## 7. Khi gate không đạt

- **P2:** Hoàng sửa lõi. Tình tiếp tục với engine giả và unit test. Chưa ai sinh dữ liệu.
- **P3 (A1 không có đoạn giảm):** dừng và báo mentor bằng số liệu, như `plan.md` quy định.
  - Tình thử các núm qua lớp config phủ (`grid_radius`, tốc độ cao điểm, `max_wait`) và chạy chẩn đoán "giữ cầu, giảm xe" của report.
  - Chỉ Hoàng sửa `default.yaml`. Không chạy P6/P8.
- **P6 (đường N(π_θ) phẳng):** mentor quyết mức B và cường độ voucher. Sinh lại legacy và sweep; tag commit trước P8.

---

## 8. Lịch tham chiếu

| Sprint | Ngày | Kết thúc bằng |
|---|---|---|
| S0 | 1 | B0: PR hợp đồng + khung |
| S1 | 2–4 | P1 xong; B1, B2, B4 |
| S2 | 5–8 | Tích hợp 1 + Gate P2 |
| S3 | 9–10 | Gate P3 |
| S4 | 11–12 | Gate P6; dữ liệu P8 |
| S5 | 12–14 | Kết quả phân tích |
| S6 | 14–15 | Báo cáo + seminar |

Tổng cộng 3 tuần (tuần 3–5). Nếu tuần 3 đã bắt đầu: giữ nguyên thứ tự và ưu tiên đường găng của Hoàng (S1 → S2 → S3). P7 là phần cắt đầu tiên.
