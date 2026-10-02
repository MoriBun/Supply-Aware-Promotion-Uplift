# Bộ dữ liệu sinh từ simulator

File này mô tả từng bộ dữ liệu trong `runs/` dùng cho phân tích tuần 5 (mốc P8, bàn giao B7). `runs/` không commit; mọi bộ **tái lập được** từ lệnh ghi ở đây, vì simulator tất định theo (config, seed).

Quy tắc dùng dữ liệu (`docs/schema.md`):
- `observed/` và `market/`: mô hình và chính sách được đọc.
- `hidden/`: ground truth, **chỉ** để đánh giá và debug; không nối vào dữ liệu huấn luyện. `analysis.io.load_run` không bao giờ trả bảng ẩn; muốn đọc phải gọi `analysis.io.load_hidden`.

---

## B7a (T4.1, sinh ngày 02/10/2026)

**Điều kiện chung**
- Code: commit `930875e` (`develop` sau Gate P3). Config: `config/default.yaml` đã hiệu chỉnh, `config_hash = cb27f5348011` (H-17).
- `world_seed = 20260930`, `run_seed = 0` cho mọi bộ `generate`: các thiết kế gặp **cùng 718.749 session** (CRN, T-29), nên so được độ chệch thiết kế trên cùng cầu.
- Cửa sổ: 28 ngày liên tục (`generate.days = 28`), warm-up 60 phút, mỗi ngày một kỳ ngân sách.
- Ngân sách: `B = 5.545,80 USD/kỳ` = 0,3 × chi tiêu của pilot `all_on` không ngân sách (seed 9000, 1 ngày: 18.486,00 USD). Chính sách cũ chịu B; thí nghiệm và GTE không áp ngân sách (D10).
- `config_hash` trong bảng là hash của config **sau khi áp override của lượt** (chính sách, thiết kế, 28 ngày), nên khác hash gốc; nó nằm trong `run_id` và `meta/run_metadata`.

| Thư mục (`runs/b7a/…`) | Chính sách | Ngân sách | Session | Order | N hoàn thành | Tỷ lệ phát | Chi voucher (USD) | V (USD) | MB | `config_hash` |
|---|---|---|---|---|---|---|---|---|---|---|
| `legacy_28d` | legacy (luật slack trễ + ε, nhắm rider theo `u_latent`, explore 5%) | B, chặn 0,1% | 718.749 | 115.232 | 108.410 | 23,2% | 152.342,5 | 350.507,6 | 56,4 | `56fe64fb463b` |
| `switchback_c1_28d` | experiment, `cluster_switchback` cụm 1, `p_on` 0,5, block 60 phút | không | 718.749 | 124.374 | 114.932 | 49,9% | 276.314,9 | 264.272,5 | 55,9 | `0a500f78bb05` |
| `switchback_c7_28d` | experiment, `cluster_switchback` cụm 7 | không | 718.749 | 123.841 | 114.040 | 49,6% | 268.964,4 | 267.106,1 | 55,6 | `bf5ccce8c655` |
| `switchback_all_28d` | experiment, `cluster_switchback` cụm all (toàn hệ) | không | 718.749 | 124.043 | 113.990 | 50,2% | 265.403,5 | 269.473,0 | 54,8 | `60fa66719536` |
| `rider_ab_28d` | experiment, `rider_ab`, `p_on` 0,5 | không | 718.749 | 124.557 | 115.116 | 50,3% | 279.152,0 | 263.081,5 | 55,3 | `1cd6d61dc7d7` |

Số session và order gồm cả warm-up (385 session); N, chi tiêu và V chỉ tính order đặt trong cửa sổ. Không bộ nào có order `Truncated`. Tổng dung lượng `runs/b7a`: 266 MB.

**GTE** (`runs/b7a/gte`, mode `gte`): `all_on` và `all_off` không ngân sách, 10 seed (0–9) × 1 ngày, ghép cặp theo seed.

| | N hoàn thành | Request | V (USD) | Chi voucher (USD) | ETA đón (phút) |
|---|---|---|---|---|---|
| `all_off` | 3.439,6 | 3.644,2 | 15.661,5 | 0 | 3,8 |
| `all_on` | 4.652,5 | 5.178,3 | 3.732,0 | 18.630,5 | 4,9 |
| **GTE = N(all_on) − N(all_off)** | **+1.212,9** (SE 14,2) | | | | |

**B** (`runs/b7a/calibrate_budget`, mode `calibrate_budget`): `budget_B_usd = 5545.80` trong `meta/run_metadata`.

### Mỗi thư mục `generate` có gì

```
observed/riders.parquet      observed/sessions.parquet    observed/orders.parquet
market/slot_snapshots.parquet
hidden/riders_hidden.parquet hidden/sessions_hidden.parquet
results/policy_results.parquet    meta/run_metadata.parquet
```

Ghi chú cho người dùng dữ liệu:
- `legacy_28d` là dữ liệu quan sát có confounding: session nhắm theo rider có `propensity = NaN` (xác suất thật ở `hidden/sessions_hidden.propensity_true`); lát explore (`assign_mechanism = explore`) có `propensity = 0,5` và là phần ngẫu nhiên hóa sạch; ô tắt có `propensity = 0` (T-24).
- Switchback: `cluster_id` 0–36 (cụm 1), 0–6 (cụm 7), 0 (all); `block` tính từ đầu lượt chạy, warm-up là block 0; `in_burnin` đánh dấu 15 phút đầu mỗi block; `propensity = cell_propensity = 0,5` (T-25).
- `rider_ab_28d`: mọi ô bật, `cluster_id = −1`, arm cố định theo rider suốt 28 ngày.
- Kết cục mặc định cho uplift là `completed`: `analysis.io.completed_outcome(sessions, orders)`.

### Lệnh sinh lại (PowerShell, từ thư mục gốc repo)

```powershell
$py = ".venv\Scripts\python.exe"
& $py -m sim run --mode calibrate_budget --config config/default.yaml --out runs/b7a/calibrate_budget
& $py -m sim run --mode generate --config config/default.yaml --set policy.name=legacy --out runs/b7a/legacy_28d
& $py -m sim run --mode generate --config config/default.yaml --set policy.name=experiment --set experiment.cluster_level=1 --out runs/b7a/switchback_c1_28d
& $py -m sim run --mode generate --config config/default.yaml --set policy.name=experiment --set experiment.cluster_level=7 --out runs/b7a/switchback_c7_28d
& $py -m sim run --mode generate --config config/default.yaml --set policy.name=experiment --set experiment.cluster_level=all --out runs/b7a/switchback_all_28d
& $py -m sim run --mode generate --config config/default.yaml --set policy.name=experiment --set experiment.design=rider_ab --out runs/b7a/rider_ab_28d
& $py -m sim run --mode gte --config config/default.yaml --out runs/b7a/gte
```

Mỗi bộ `generate` chạy 4–5 phút trên một lõi (đo: 240–272 giây); chạy song song được vì mỗi lệnh một tiến trình.

### Kiểm tra trước khi dùng (điều kiện nhận B7)

```powershell
& $py -m analysis.check_dataset runs/b7a/legacy_28d runs/b7a/switchback_c1_28d runs/b7a/switchback_c7_28d runs/b7a/switchback_all_28d runs/b7a/rider_ab_28d runs/b7a/gte runs/b7a/calibrate_budget
& $py -m analysis.check_budget runs/b7a/legacy_28d
```

- `check_dataset`: mọi bảng đúng cột và kiểu trên đĩa của `schema.md`; không cột ẩn nào trong `observed/`, `market/`; session, order và results khớp nhau; `config_hash` trong metadata đúng là hash của config đã lưu. Kết quả 02/10: cả 7 thư mục **OK**.
- `check_budget` trên `legacy_28d`: cả 28 kỳ chi ≤ B (lớn nhất 5.545,68 USD), warm-up 91,98 ≤ 231,07 USD; 450 session bị chặn đều có `arm = 0`, `voucher = 0`.
- Sinh lại trên máy khác phải ra đúng các con số trong bảng (session, order, N); khác là sai config hoặc sai phiên bản code.

---

## B7b (T4.3): sweep θ, bản tạm chờ Gate P6

**Chưa chốt.** Gate P6 chưa đạt trên lưới θ mặc định (câu hỏi mở Q23 trong `decisions.md`). Nếu mentor giữ B = 5.545,80 thì sweep dưới đây là sweep tham chiếu và `legacy_28d` không phải sinh lại; nếu B đổi thì sinh lại cả hai.

### Sweep tham chiếu (`runs/p6/sweep_theta`, sinh ngày 02/10/2026)

`python -m sim run --mode sweep_theta --config config/default.yaml --out runs/p6/sweep_theta` (271 giây, 8 tiến trình). Chính sách `threshold`, hàm điểm `heuristic_low_freq`, dự báo `persistence`, không hysteresis; 12 θ × 10 seed (0–9) × 1 ngày; cùng B = 5.545,80 USD/kỳ; κ auto riêng cho từng θ (pilot seed 9000 + chỉ số θ). `config_hash = cb27f5348011`, commit `930875e`.

| θ | N trung bình | SE | V trung bình (USD) | Chi voucher (USD) | % (ô, slot) tắt | κ |
|---|---|---|---|---|---|---|
| 0 | 3.844,6 | 19,7 | 12.321,0 | 5.545,2 | 0 | −2,349 |
| 0,1 | 3.877,0 | 19,3 | 12.483,1 | 5.545,2 | 24,8 | −2,584 |
| 0,2 | 3.883,0 | 23,4 | 12.489,7 | 5.545,2 | 27,2 | −2,589 |
| 0,3 | 3.883,7 | 18,8 | 12.499,0 | 5.545,1 | 30,0 | −2,708 |
| 0,4 | 3.888,1 | 20,4 | 12.506,2 | 5.545,2 | 31,4 | −2,708 |
| 0,5 | 3.890,0 | 17,4 | 12.503,3 | 5.545,1 | 32,8 | −2,767 |
| 0,6 | 3.892,6 | 18,4 | 12.534,1 | 5.545,2 | 34,7 | −2,821 |
| 0,8 | 3.892,5 | 19,2 | 12.525,8 | 5.545,1 | 37,4 | −2,951 |
| 1,0 | 3.892,7 | 17,6 | 12.535,8 | 5.545,3 | 38,9 | −2,995 |
| 1,25 | 3.888,4 | 15,8 | 12.503,6 | 5.545,5 | 42,6 | −3,206 |
| 1,5 | 3.899,3 | 15,6 | 12.547,8 | 5.525,1 | 44,9 | −3,101 |
| 2,0 | 3.893,8 | 17,7 | 12.519,4 | 5.545,1 | 47,8 | −3,404 |

Mốc so sánh (cùng seed 0–9, `runs/b7a/gte`): `all_off` 3.439,6; `all_on` không ngân sách 4.652,5. `all_on` có ngân sách B (20 seed, đo ở A2(b)): 3.700,4.

File: `results/policy_results.parquet` (120 lượt), `results/theta_sweep.parquet`, `meta/run_metadata.parquet` (κ của từng lượt), `results/theta_sweep.png` (vẽ bằng `python -m analysis.plots theta_sweep runs/p6/sweep_theta --gte runs/b7a/gte`).

### Sweep chẩn đoán cho Gate P6 (`runs/p6/sens_*`, 5 seed mỗi bộ)

Lệnh: như trên, thêm `--set sweep.n_seeds=5` và override ghi ở cột đầu.

| Thư mục | Override | B (USD/kỳ) | N tại θ = 0 | N lớn nhất (θ) | N tại θ cuối lưới | Dạng đường |
|---|---|---|---|---|---|---|
| `sens_fraction_0p1` | `budget.fraction=0.1` | 1.848,6 | 3.576 | 3.595 (1,25) | 3.589 | phẳng |
| `sens_fraction_0p6` | `budget.fraction=0.6` | 11.091,6 | 4.228 | 4.283 (0,4) | 4.187 | cực đại bên trong, giảm khi θ ≥ 1,25 |
| `sens_voucher_0p3` | `voucher.pct_of_fare=0.3` | 9.076,3 | 3.940 | 4.014 (1,5) | 4.012 | tăng một bậc rồi phẳng |
| `sens_demand_1p5` | `demand.demand_scale=1.5` | 6.430,7 | 5.381 | 5.623 (2) | 5.623 | tăng đều tới mép lưới |
| `sens_theta_wide` | `sweep.theta_grid=[0, 1, 2, 3, 5, 10, 30]` | 5.545,8 | 3.834 | 3.885 (2) | 3.694 (θ = 30) | phẳng tới θ = 5, giảm từ θ = 10 |

Các sweep này chỉ để chẩn đoán, không phải dữ liệu bàn giao.
