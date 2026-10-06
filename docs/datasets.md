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

## B7b (bản H-21, sinh ngày 05/10/2026): sweep θ tham chiếu với κ auto điểm bất động

Bản này thay bản ngày 02/10 (`runs/b7b`, κ từ một lượt pilot, seed pilot riêng cho từng θ). Theo H-21 và T-32: κ auto lặp pilot đến khi chi của pilot ≤ B, mọi θ dùng chung seed pilot 9000, κ giữ trọn nhóm điểm bằng nhau. B không đổi (5.545,80 USD/kỳ) nên **B7a không phải sinh lại**. T-31 (θ\* là tập, chấm θ̂ bằng regret) giữ nguyên; mentor chưa xác nhận T-31.

### Sweep tham chiếu (`runs/b7b_h21/sweep_theta_ref`)

- Chính sách `threshold`, hàm điểm `heuristic_low_freq`, dự báo `persistence`, không hysteresis.
- 16 mốc θ (lớp phủ `config/sweep_reference.yaml`) × 30 seed (0–29) × 1 ngày = 480 lượt; cùng B; κ auto mỗi θ lặp 1–6 lượt pilot (cột `kappa_pilots` của `meta/run_metadata`), không θ nào chạm trần `kappa_max_iter = 10`.
- `config_hash` của lượt: `19f46649271e`; `config_hash(default.yaml)` = `34f3aa436d16` (đổi từ `cb27f5348011` vì thêm khóa `policy.threshold.kappa_max_iter`, T-32); code `8467f83` + thay đổi H-21 (chưa commit lúc sinh, nay là commit `7b6a003`).
- Sinh lại sau khi thêm khóa `policy.threshold.scope` (T-35 f) cho `config_hash` của lượt `11358df900a6` thay vì `19f46649271e`; mọi số N theo θ, tập θ\* và regret trùng từng chữ số (Hoàng kiểm khi nhận, log 05/10). Hash lệch chỉ vì khóa mới có giá trị mặc định.
- Cột cuối so với bản 02/10, ghép cặp theo seed (cùng seed đánh giá nên chỉ khác ở κ).

| θ | N trung bình | SE | V (USD) | Chi voucher (USD) | % (ô, slot) tắt | κ (cũ → mới) | lượt pilot | Kém θ tốt nhất (± SE ghép cặp) | Thuộc tập θ\* | N mới − cũ (± SE) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3.860,3 | 11,0 | 12.378,0 | 5.523,3 | 0 | −2,349 → −2,236 | 4 | 39,5 ± 4,0 | không | 11,9 ± 3,2 |
| 0,1 | 3.884,3 | 11,3 | 12.477,5 | 5.520,7 | 25 | −2,584 → −2,425 | 3 | 15,4 ± 4,3 | không | 6,9 ± 3,5 |
| 0,2 | 3.887,0 | 10,8 | 12.479,8 | 5.523,4 | 27 | −2,589 → −2,469 | 3 | 12,7 ± 3,4 | không | 4,8 ± 3,5 |
| 0,3 | 3.893,2 | 11,0 | 12.522,7 | 5.514,6 | 30 | −2,708 → −2,512 | 6 | 6,5 ± 3,7 | **có** | 8,5 ± 4,4 |
| 0,4 | 3.890,8 | 11,3 | 12.531,5 | 5.495,4 | 31 | −2,708 → −2,563 | 3 | 9,0 ± 4,0 | **có** | 1,0 ± 4,4 |
| 0,5 | 3.894,9 | 10,3 | 12.580,8 | 5.462,6 | 33 | −2,767 → −2,574 | 3 | 4,9 ± 2,7 | **có** | 3,1 ± 4,0 |
| 0,6 | 3.892,2 | 11,0 | 12.573,4 | 5.447,7 | 35 | −2,821 → −2,622 | 5 | 7,5 ± 3,3 | **có** | −0,8 ± 3,6 |
| 0,8 | 3.889,3 | 10,4 | 12.607,6 | 5.390,9 | 37 | −2,951 → −2,687 | 5 | 10,4 ± 3,9 | **có** | −4,2 ± 3,6 |
| 1 | 3.889,9 | 11,5 | 12.581,8 | 5.414,6 | 39 | −2,995 → −2,741 | 3 | 9,9 ± 3,1 | không | −4,5 ± 4,0 |
| 1,25 | 3.890,4 | 11,6 | 12.583,3 | 5.421,9 | 42 | −3,206 → −2,894 | 5 | 9,4 ± 3,3 | **có** | 2,5 ± 4,5 |
| 1,5 | 3.891,8 | 11,6 | 12.579,3 | 5.431,2 | 45 | −3,101 → −2,986 | 4 | 7,9 ± 3,6 | **có** | −9,8 ± 3,7 |
| **2** | **3.899,7** | 10,6 | 12.562,3 | 5.484,6 | 47 | −3,404 → −3,172 | 4 | 0 (tốt nhất) | **có** | 2,3 ± 3,3 |
| 3 | 3.882,3 | 10,4 | 12.674,7 | 5.275,2 | 53 | −3,790 → −3,443 | 5 | 17,5 ± 3,9 | không | −7,3 ± 3,7 |
| 5 | 3.876,9 | 10,8 | 12.516,8 | 5.424,9 | 61 | −4,931 → −4,485 | 3 | 22,9 ± 3,9 | không | −6,4 ± 4,5 |
| 10 | 3.837,2 | 10,0 | 12.539,1 | 5.233,8 | 69 | −∞ → −∞ | 1 | 62,5 ± 4,6 | không | 0,0 ± 0,0 |
| 30 | 3.693,0 | 9,8 | 13.579,8 | 3.436,3 | 75 | −∞ → −∞ | 1 | 206,7 ± 3,8 | không | 0,0 ± 0,0 |

**Đọc bảng:**
- κ mới chặt hơn ở mọi θ có κ hữu hạn; chi tiêu còn 94–99,6% B thay vì luôn chạm 100% (ngân sách không còn cạn trước cuối ngày, Q26). N ở θ = 0 tăng 11,9 ± 3,2; ở đoạn phẳng thay đổi trong khoảng ±10, cùng cỡ nhiễu κ của Q24.
- Đường vẫn có ba đoạn tăng, phẳng, giảm. **Khoảng θ\* = [0,3; 2]**, θ tốt nhất 2 (bản cũ: [0,4; 2], tốt nhất 1,5). Mốc 1 bị loại khỏi tập (kém 9,9 ± 3,1): dùng chung seed pilot chưa xóa hết nhiễu riêng theo θ của κ.
- Regret theo N (± SE ghép cặp): θ = 0: 39,5 ± 4,0 (1,01%; bản cũ 53,3); θ mặc định 0,35 (nội suy): 7,8 ± 3,3 (0,20%); θ = 0,5: 4,9 ± 2,7; θ = 10: 62,5 ± 4,6; θ = 30: 206,7 ± 3,8 (5,30%). Lợi ích của tầng ô nhỏ hơn bản cũ: một phần lợi ích cũ đến từ việc κ cũ làm ngân sách cạn sớm ở θ nhỏ.
- Mốc so sánh (`runs/b7a/gte`, seed 0–9): `all_off` 3.439,6; `all_on` không ngân sách 4.652,5. `all_on` có B (30 seed, `runs/s5/policy_table`): 3.686,7.

File: `results/policy_results.parquet` (480 lượt), `results/theta_sweep.parquet`, `meta/run_metadata.parquet` (κ, số lượt pilot, B của từng lượt).

### Phân tích độ nhạy (`runs/b7b_h21/sens_*`, 16 θ × 10 seed mỗi bộ)

| Thư mục | Override | B (USD/kỳ) | N tại θ = 0 | N lớn nhất (θ) | N tại θ = 30 | Khoảng θ\* | Regret của θ = 0 | Lượt pilot (min–max) |
|---|---|---|---|---|---|---|---|---|
| `sens_fraction_0p1` | `budget.fraction=0.1` | 1.848,6 | 3.586 | 3.606,7 (0,6) | 3.581 | [0,1; 10] | +20,9 ± 5,4 (0,58%) | 3–5 |
| `sens_fraction_0p6` | `budget.fraction=0.6` | 11.091,6 | 4.240 | 4.298,3 (0,2) | 3.685 | [0,1; 1] | +58,8 ± 4,9 (1,37%) | 1–5 |
| `sens_voucher_0p3` | `voucher.pct_of_fare=0.3` | 9.076,3 | 3.972 | 4.033,4 (1,5) | 3.775 | [0,1; 3], loại 0,2 | +61,6 ± 8,5 (1,53%) | 1–7 |
| `sens_demand_1p5` | `demand.demand_scale=1.5` | 6.430,7 | 5.489 | 5.650,3 (1,25) | 5.347 | [0,3; 2], loại 0,4; 0,5 | +160,9 ± 15,6 (2,85%) | 1–9 |

- Cả bốn biến thể vẫn có đủ ba đoạn. θ = 0,6 thuộc tập θ\* ở cả năm kịch bản; θ = 0,4 thuộc tập ở bốn kịch bản (bị loại ở `sens_demand_1p5`).
- Lợi ích của tầng ô vẫn tăng theo độ căng (0,58% khi ngân sách rất chặt, 1,01% ở cấu hình chuẩn, 2,85% khi cầu gấp rưỡi) nhưng nhỏ hơn bản cũ (0,50%; 1,37%; 4,10%).

### Lệnh sinh lại (PowerShell)

```powershell
$py = ".venv\Scripts\python.exe"
$ref = @("--config", "config/default.yaml", "--config", "config/sweep_reference.yaml")
& $py -m sim run --mode sweep_theta @ref --set sweep.n_seeds=30 --out runs/b7b_h21/sweep_theta_ref
& $py -m sim run --mode sweep_theta @ref --set budget.fraction=0.1 --out runs/b7b_h21/sens_fraction_0p1
& $py -m sim run --mode sweep_theta @ref --set budget.fraction=0.6 --out runs/b7b_h21/sens_fraction_0p6
& $py -m sim run --mode sweep_theta @ref --set voucher.pct_of_fare=0.3 --out runs/b7b_h21/sens_voucher_0p3
& $py -m sim run --mode sweep_theta @ref --set demand.demand_scale=1.5 --out runs/b7b_h21/sens_demand_1p5
& $py -m analysis.check_dataset runs/b7b_h21/sweep_theta_ref runs/b7b_h21/sens_fraction_0p1 runs/b7b_h21/sens_fraction_0p6 runs/b7b_h21/sens_voucher_0p3 runs/b7b_h21/sens_demand_1p5
```

Thời gian (8 tiến trình, chạy cùng lúc với việc khác): sweep tham chiếu 1.613 giây; mỗi sweep độ nhạy 548–910 giây. `check_dataset` ngày 05/10: cả 5 thư mục OK.

### Dùng cho phân tích tuần 5

```python
import pandas as pd
from analysis.metrics import theta_star_set, theta_star_interval, sweep_regret
runs = pd.read_parquet("runs/b7b_h21/sweep_theta_ref/results/policy_results.parquet")
theta_star_interval(theta_star_set(runs))      # (2.0, 0.3, 2.0)
sweep_regret(runs, theta_hat=0.8)              # regret theo N của một ngưỡng ước lượng θ̂
```

Ước lượng θ̂ được chấm bằng regret theo N, không bằng khoảng cách tới θ\* (T-31).

**Bản cũ** (`runs/b7b`, 02/10, κ một lượt pilot): N lớn nhất 3.901,7 ở θ = 1,5; khoảng θ\* [0,4; 2]; regret θ = 0: 53,3 ± 4,8. Giữ để đối chiếu; xóa được sau khi Hoàng nhận bản H-21. `runs/p6/` cũng xóa được.

---

## B8 (H5.1, giao ngày 05/10/2026): hàm điểm τ̂ nền và parquet dự đoán

**Hàm điểm** (`analysis/scores.py`, bảng `analysis/models/tau_x_baseline.json`, có commit):
- `analysis.scores:tau_x_baseline`: hiệu ứng voucher lên `completed`, theo `x_segment` × tercile `x_freq`, ước lượng trên lát explore của `legacy_28d` (H4.2).
- `analysis.scores:tau_per_dollar_baseline`: cùng hiệu ứng chia cho chi phí voucher kỳ vọng của một lượt phát (số chuyến thêm trên 1 USD).
- Dùng: `--set policy.threshold.score_fn=analysis.scores:tau_per_dollar_baseline`. Chỉ đọc `x_freq`, `x_segment` của `SessionBatch`, bỏ qua ŝ, tất định.

**Parquet dự đoán** (`runs/b8/`, không commit): một file cho mỗi bộ B7a, `predictions_<bộ>.parquet`, 718.749 dòng; cột `session_id`, `rider_id`, `in_window`, `tau_x_baseline`, `tau_per_dollar_baseline`. Ghép với dữ liệu bằng `session_id`. Năm file giống nhau vì các bộ dùng chung session (CRN) và điểm chỉ phụ thuộc đặc trưng rider.

Lệnh sinh lại (PowerShell):

```powershell
foreach ($d in "legacy_28d","rider_ab_28d","switchback_c1_28d","switchback_c7_28d","switchback_all_28d") {
  & $py -m analysis.scores predict runs/b7a/$d runs/b8/predictions_$d.parquet
}
```

**Kiểm tra trước khi dùng (điều kiện nhận B8):** `pytest -q tests/test_estimate.py` (có test nạp hàm điểm trong tiến trình con `spawn`, test tất định và test chỉ đọc cột của batch).

**Lưu ý:** bảng τ̂ được ước lượng trên lát explore của `legacy_28d`. Các bộ khác cùng session nhưng khác cách gán voucher, nên kết quả kiểm định trên đó không độc lập hoàn toàn với dữ liệu huấn luyện.

**Bổ sung H5.2 (DR-learner, H-24):** 8 hàm điểm `analysis.uplift:tau_x_dr`, `tau_xs_dr`, `tau_x_dr_per_dollar`, `tau_xs_dr_per_dollar` (mẫu explore) và các bản `..._all` (toàn bộ legacy). Mô hình ở `analysis/models/dr_*` (có commit); fit lại bằng `python -m analysis.uplift fit runs/b7a/legacy_28d`. Cần `pip install -e ".[analysis]"` (LightGBM). Kiểm tra: `pytest -q tests/test_uplift.py`.

---

## Dữ liệu Sprint 5 (05/10/2026, `runs/s5`)

| Thư mục | Lệnh | Dùng cho |
|---|---|---|
| `policy_table` | `python -m analysis.policy_table --config config/default.yaml --n-seeds 30 --out runs/s5/policy_table` | T5.1: 15 chính sách (`DEFAULT_SPECS`, gồm 6 hàm điểm DR và 2 dòng π_θ̂ trên `ring1`) × 30 seed dưới cùng B (T-33, T-35d) |
| `sweep_ring1_heuristic` | `python -m sim run --mode sweep_theta --config config/default.yaml --config config/sweep_reference.yaml --set sweep.n_seeds=30 --set policy.threshold.scope=ring1 --out runs/s5/sweep_ring1_heuristic` | Sweep θ với ŝ `ring1` (H-25), `heuristic_low_freq`; so với B7b (ŝ theo ô) |
| `sweep_ring1_dr` | như trên, thêm `--set policy.threshold.score_fn=analysis.uplift:tau_x_dr_all_per_dollar` | Sweep θ với ŝ `ring1` và hàm điểm học được (H-22 ii); regret của θ̂ (A), (B) của H5.3 |
| `sweep_cell_dr` | như `sweep_ring1_dr` nhưng bỏ `--set policy.threshold.scope=ring1` | Sweep θ với ŝ theo ô và hàm điểm học được (H-22 ii) |
| `sweep_ring1_random` | như `sweep_ring1_dr` nhưng `--set policy.threshold.score_fn=random` (Hoàng, 05/10) | H5.3: regret của θ̂ (B) với tầng rider rải đều (H-26). θ tốt nhất 3 (3.884,5), tập θ* {3}; N(θ = 0) 3.807,0 trùng dòng `random` của T5.1; θ = 5 trùng `sweep_ring1_dr` (3.849,2, κ = −∞); 6 phút, 16 tiến trình |
| `qini_vs_value` | `python -m analysis.qini_vs_value --data runs/b7a/rider_ab_28d --table runs/s5/policy_table --outcome completed --out runs/s5/qini_vs_value` (và `--outcome requested`) | T5.2 (T-33). Từ 05/10 tối, `--outcome completed` ghi thêm `results/offer_efficiency.parquet` (T-36); chạy lại lệnh trên nếu thư mục thiếu file này (khoảng 6 phút) |
| `interference` | `python -m analysis.interference designs --gte runs/b7a/gte runs/b7a/rider_ab_28d runs/b7a/switchback_c1_28d runs/b7a/switchback_c7_28d runs/b7a/switchback_all_28d --out runs/s5/interference` (và `--outcome requested`); `python -m analysis.interference confounding runs/s5/legacy_gu_0_28d runs/s5/legacy_gu_0p5_28d runs/b7a/legacy_28d runs/s5/legacy_gu_2_28d --out runs/s5/interference` | T5.3 (T-34) |
| `legacy_gu_0_28d`, `legacy_gu_0p5_28d`, `legacy_gu_2_28d` | `python -m sim run --mode generate --config config/default.yaml --set policy.name=legacy --set policy.legacy.target_g_u=<0 / 0.5 / 2> --out runs/s5/legacy_gu_<0 / 0p5 / 2>_28d` | T5.3: độ nhạy theo `u_latent`; cùng `run_seed = 0` nên cùng 718.749 session với `legacy_28d` (`target_g_u` = 1) |

Ba bộ legacy mới (`config_hash` `2da8ea13c0e0` / `7306ebc20b78` / `5b6a3ba4079b`, code `8467f83` + H-21): N hoàn thành 105.941 / 106.911 / 108.177; tỷ lệ phát 22,0% / 22,2% / 22,2%; bị chặn ngân sách 0% / 0% / 2,9%; không order Truncated; `check_dataset` OK.

Máy 16 GB RAM (Hoàng, 05/10): `policy_table` với mặc định một tiến trình mỗi lõi (16) hết bộ nhớ ảo khi các tiến trình cùng nạp LightGBM; chạy với `--set runner.n_procs=6` (khoảng 10 phút) và `$env:PYTHONIOENCODING = "utf-8"` nếu chuyển hướng output (H-28 e). Bảng sinh lại trên máy Hoàng trùng từng số với bảng của Tình (N của 15 chính sách); ba bộ `legacy_gu_*` sinh lại trùng N hoàn thành 105.941 / 106.911 / 108.177.

### Sweep θ theo phạm vi ŝ và hàm điểm (vòng 2, code `ed64f62` + thay đổi chưa commit)

Cùng lưới 16 θ, cùng 30 seed, cùng B = 5.545,80 USD/kỳ với B7b (`runs/b7b_h21/sweep_theta_ref`, ŝ theo ô, `heuristic_low_freq`), nên ghép cặp được theo seed. `config_hash` của lượt: `89c0a9869ced` (`ring1`, heuristic), `c54d6db7563e` (`ring1`, DR), `0fa4fa60e36c` (ô, DR); `check_dataset` OK cả 3 và `policy_table`. Mỗi θ cần 1–6 lượt pilot κ, không chạm `kappa_max_iter`. Hàm điểm DR = `analysis.uplift:tau_x_dr_all_per_dollar`.

| Sweep | θ tốt nhất | N(θ tốt nhất) | Bao tập θ\* | θ trong bao bị loại | N(θ = 0) | Regret θ = 0 |
|---|---|---|---|---|---|---|
| ô, heuristic (B7b) | 2 | 3.899,7 | [0,3; 2] | 1 | 3.860,3 | 39,5 ± 4,0 (1,01%) |
| `ring1`, heuristic | 3 | 3.915,7 | [1,5; 3] | 2 | 3.860,3 | 55,4 ± 4,7 (1,42%) |
| ô, DR/USD | 0,4 | 4.006,6 | [0,1; 0,6] | không | 3.989,9 | 16,6 ± 5,7 (0,42%) |
| `ring1`, DR/USD | 1 | 4.017,4 | [0,2; 1,5] | không | 3.989,9 | 27,4 ± 4,1 (0,68%) |

N theo θ (chi / B, % (ô, slot) tắt); **đậm** = thuộc tập θ\*:

| θ | ô, heuristic | `ring1`, heuristic | ô, DR/USD | `ring1`, DR/USD |
|---|---|---|---|---|
| 0 | 3.860,3 (0,996; 0) | 3.860,3 (0,996; 0) | 3.989,9 (0,988; 0) | 3.989,9 (0,988; 0) |
| 0,1 | 3.884,3 (0,995; 25) | 3.871,4 (0,992; 6) | **3.999,2** (0,986; 25) | 4.002,1 (0,983; 6) |
| 0,2 | 3.887,0 (0,996; 27) | 3.881,2 (0,991; 8) | **4.004,6** (0,986; 27) | **4.010,3** (0,988; 9) |
| 0,3 | **3.893,2** (0,994; 30) | 3.889,2 (0,990; 11) | **4.005,3** (0,974; 30) | **4.014,2** (0,983; 11) |
| 0,4 | **3.890,8** (0,991; 31) | 3.894,6 (0,991; 13) | **4.006,6** (0,985; 32) | **4.012,9** (0,973; 13) |
| 0,5 | **3.894,9** (0,985; 33) | 3.893,0 (0,993; 14) | **4.000,3** (0,990; 33) | **4.014,0** (0,966; 15) |
| 0,6 | **3.892,2** (0,982; 35) | 3.896,4 (0,993; 16) | **3.997,4** (0,974; 35) | **4.014,1** (0,971; 17) |
| 0,8 | **3.889,3** (0,972; 37) | 3.895,8 (0,981; 20) | 3.990,2 (0,968; 38) | **4.015,5** (0,965; 20) |
| 1 | 3.889,9 (0,976; 39) | 3.902,8 (0,989; 23) | 3.989,1 (0,972; 39) | **4.017,4** (0,973; 23) |
| 1,25 | **3.890,4** (0,978; 42) | 3.900,0 (0,981; 27) | 3.980,5 (0,968; 43) | **4.009,3** (0,967; 28) |
| 1,5 | **3.891,8** (0,979; 45) | **3.908,0** (0,980; 31) | 3.976,2 (0,983; 45) | **4.015,7** (0,970; 32) |
| 2 | **3.899,7** (0,989; 47) | 3.901,9 (0,969; 38) | 3.964,1 (0,965; 48) | 4.006,0 (0,995; 40) |
| 3 | 3.882,3 (0,951; 53) | **3.915,7** (0,988; 52) | 3.940,6 (0,924; 54) | 3.972,4 (0,981; 53) |
| 5 | 3.876,9 (0,978; 61) | 3.849,2 (0,890; 70) | 3.919,4 (0,974; 61) | 3.849,2 (0,890; 70) |
| 10 | 3.837,2 (0,944; 69) | 3.597,2 (0,324; 86) | 3.837,2 (0,944; 69) | 3.597,2 (0,324; 86) |
| 30 | 3.693,0 (0,620; 75) | 3.443,5 (0; 100) | 3.693,0 (0,620; 75) | 3.443,5 (0; 100) |

- **Hai cách đo ŝ, so ở θ tốt nhất của mỗi sweep (ghép cặp):** `ring1` − ô: heuristic +16,0 ± 3,2; DR/USD +10,8 ± 4,4. Cả hai phía đều chọn "tốt nhất" trên chính các seed này (winner's curse, báo cáo §10.3), nên hiệu này chỉ là chỉ dấu. Cùng θ thì không so được, vì θ đo trên hai thang khác nhau: `ring1` tắt ít (ô, slot) hơn ở θ nhỏ và nhiều hơn ở θ lớn.
- **H-22 (ii), dự đoán "điểm càng tốt thì θ\* càng gần 0": đúng trên cả hai cách đo.** Với DR/USD thay heuristic, bao θ\* dời từ [0,3; 2] về [0,1; 0,6] (ô) và từ [1,5; 3] về [0,2; 1,5] (`ring1`); regret của θ = 0 giảm từ 39,5 xuống 16,6 (ô) và từ 55,4 xuống 27,4 (`ring1`). θ = 0 vẫn chưa thuộc tập θ\* ở cả bốn sweep. DR/USD hơn heuristic ở θ tốt nhất +106,8 ± 4,7 (ô).
- **Regret của θ̂ (H5.3) trên các sweep `ring1`:** θ̂ (A) = 0,25: 5,1 ± 3,1 [−1,3; 11,5] (0,13%) với DR/USD; 30,5 ± 4,2 (0,78%) với heuristic. θ̂ (B) = 5: 168,2 ± 5,3 [157,4; 178,9] (4,19%) với DR/USD; 66,5 ± 3,9 (1,70%) với heuristic. Ở θ = 5 trên `ring1`, 70% (ô, slot) tắt, κ = −∞ (phát cho mọi session của ô còn bật) mà vẫn chỉ chi 0,890 × B: tầng ô cắt nhiều hơn mức ngân sách cần.
- **Với `ring1`, θ > `monitor.slack_cap` (10) là `all_off`.** `ring1` cắt +∞ ở `slack_cap` (H-25a), còn ŝ theo ô với `forecast: persistence` giữ +∞ (ô bật, T-23b). Vì vậy ở θ = 30, `ring1` tắt 100% và N = 3.443,5 (≈ `all_off` 3.440,1), còn ô vẫn bật 25% (ô có xe rảnh mà không xe nào đi đón). Chỉ điểm θ = 30 bị ảnh hưởng; tập θ\* không đổi.
- Kiểm chéo: π_θ θ = 0,5 heuristic của `policy_table` = 3.894,9, trùng điểm θ = 0,5 của B7b; π_θ̂ (B) `ring1` = 3.849,2, trùng θ = 5 của `sweep_ring1_dr`. Lượt chạy ~15–18 phút mỗi sweep (480 lượt + pilot κ).

## Dữ liệu H5.3 (05/10/2026, `runs/h53`)

Dùng cho chọn ŝ (H-25) và tác hại theo giờ; notebook `04_uoc_luong_va_theta` đọc cả ba. Đều là `evaluate` 5 seed (0–4) với `--log-level full` (cần bảng session, order, snapshot của từng lượt).

| Thư mục | Lệnh | Dùng cho |
|---|---|---|
| `all_off_3d` | `python -m sim run --mode evaluate --config config/default.yaml --set policy.name=all_off --set time.window_min=4320 --set sweep.n_seeds=5 --log-level full --out runs/h53/all_off_3d` | Chọn ŝ: `python -m analysis.tension runs/h53/all_off_3d` (bảng 7 ứng viên); cửa sổ 3 ngày để `cell_ar` có lag ngày |
| `hourly_all_on`, `hourly_all_off` | `python -m sim run --mode evaluate --config config/default.yaml --set policy.name=<all_on / all_off> --set budget.enforce=false --set sweep.n_seeds=5 --log-level full --out runs/h53/hourly_<all_on / all_off>` | Tác hại theo giờ: phát voucher cho mọi khách trừ không phát, không ngân sách, ghép cặp theo seed (`analysis.theta.on_off_by_hour_runs`) |

Kiểm tra: `on_off_by_hour_runs` cho cả ngày +1.198,8 chuyến, 7h −15,4 ± 2,1 (log H5.3).

---

## Dữ liệu Sprint 6 (05/10/2026, `runs/s6`): kiểm định cho notebook 01

Notebook kết quả chỉ đọc dữ liệu, không chạy mô phỏng (H-27). Các thư mục dưới đây cho notebook `01_simulator_kiem_dinh` các số A1, A3, A5 và CAL; A2 (b) dùng `runs/s5/policy_table` và `runs/b7b_h21/sweep_theta_ref`, A4 dùng `runs/b7a/switchback_c7_28d`. Sinh bằng code `52f99a5` (`sim/` không đổi trong S6), `config_hash(default.yaml)` = `92b7d13adc39`.

| Thư mục | Lệnh (`python -m sim run --config config/default.yaml ...`) | Dùng cho | `config_hash` | Thời gian |
|---|---|---|---|---|
| `a5_evaluate_1proc` | `--mode evaluate --set sweep.n_seeds=3 --set runner.n_procs=1 --out runs/s6/a5_evaluate_1proc` | A5: thời gian engine 1 ngày, 1 tiến trình, log tối thiểu (chạy riêng, máy không bận) | `dca3cafc1f50` | 44 s |
| `throughput` | `--mode throughput_curve --out runs/s6/throughput` | A1: 16 mức cầu × 3 seed | — (mode chỉ ghi `results/`, spec §7) | 152 s |
| `gte_full_5` | `--mode gte --set gte.n_seeds=5 --log-level full --out runs/s6/gte_full_5` | CAL: log đầy đủ của all_off 5 seed (cùng các job của test chậm CAL); kèm all_on | `06a9d1599ace` | 25 s |
| `a3_h0` | `--mode evaluate --set sweep.n_seeds=5 --out runs/s6/a3_h0` | A3: π_θ θ = 0,35, h = 0 | `feb7327a82e5` | 36 s |
| `a3_h01` | như trên, thêm `--set policy.threshold.hysteresis_h=0.1`, `--out runs/s6/a3_h01` | A3: h = 0,1 | `a37ada11e9eb` | 42 s |

`check_dataset`: OK cả 4 thư mục có `meta/`; `throughput` báo thiếu `meta/run_metadata` vì mode `throughput_curve` chỉ ghi `results/throughput_curve.parquet` (đúng spec §7), không phải lỗi dữ liệu.

Số chính (chi tiết trong notebook 01):
- A1 đạt 4/4: đỉnh 781,2 chuyến/giờ ở mức 3,25 (trùng gate P3, log H3.2); mức cầu lớn nhất 0,845 × đỉnh; slack lớn nhất sau đỉnh 0,095; bước ETA lớn nhất 1,871 phút.
- CAL 5/5 trong khoảng: P(đặt) 0,1535; tăng request +50,6%; giá trung bình 19,03 USD; (ô, slot) căng 27,9%, dư 63,3%. `tests/test_validation.py` kiểm rằng tính từ bảng đã lưu bằng đúng số test chậm tính trong bộ nhớ (cùng seed).
- A2 (b): Var(hiệu, CRN) / Var(hiệu, seed độc lập) = 0,171 trên 30 seed, 0,135 trên 20 seed (ngưỡng 0,5; T-37).
- A3: trung vị 25,6 lần/ô/ngày (h = 0), 25,0 (h = 0,1); N không đổi (3.884,6 và 3.883,0).
- A4: 0 lần đổi dấu (trùng H4.2).
- A5: trung vị 5,75 giây / ngày mô phỏng (ngưỡng 30).
