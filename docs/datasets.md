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

## B7b (T4.3, sinh ngày 02/10/2026): sweep θ tham chiếu

Theo quyết định T-31 (chốt Q23; quyết định của Tình, **mentor chưa xác nhận**): giữ B = 5.545,80 USD/kỳ nên các bộ B7a ở trên **không phải sinh lại**; sweep tham chiếu dùng lưới θ kéo dài và 30 seed.

### Sweep tham chiếu (`runs/b7b/sweep_theta_ref`)

- Chính sách `threshold`, hàm điểm `heuristic_low_freq`, dự báo `persistence`, không hysteresis.
- 16 mốc θ (lớp phủ `config/sweep_reference.yaml`) × 30 seed (0–29) × 1 ngày = 480 lượt; cùng B; κ auto riêng cho từng θ (pilot seed 9000 + chỉ số θ).
- `config_hash` của lượt: `c27ac66f7c2c` (= `default.yaml` + lớp phủ + `sweep.n_seeds=30`); hash gốc `default.yaml` vẫn `cb27f5348011`; commit `c62800e`.
- 120 lượt chung với sweep 12 θ × 10 seed chạy trước đó (`runs/p6/sweep_theta`) cho N và V giống hệt.

| θ | N trung bình | SE | V (USD) | Chi voucher (USD) | % (ô, slot) tắt | κ | Kém θ tốt nhất (± SE ghép cặp) | Thuộc tập θ\* |
|---|---|---|---|---|---|---|---|---|
| 0 | 3.848,4 | 10,9 | 12.335,3 | 5.545,3 | 0 | −2,35 | 53,3 ± 4,8 | không |
| 0,1 | 3.877,4 | 10,4 | 12.455,1 | 5.545,3 | 25 | −2,58 | 24,2 ± 4,5 | không |
| 0,2 | 3.882,2 | 11,3 | 12.465,2 | 5.545,2 | 27 | −2,59 | 19,5 ± 5,5 | không |
| 0,3 | 3.884,7 | 10,7 | 12.503,1 | 5.545,1 | 30 | −2,71 | 17,0 ± 4,5 | không |
| 0,4 | 3.889,8 | 10,5 | 12.498,2 | 5.545,2 | 31 | −2,71 | 11,9 ± 4,2 | **có** |
| 0,5 | 3.891,8 | 10,2 | 12.508,5 | 5.545,2 | 33 | −2,77 | 9,9 ± 3,9 | **có** |
| 0,6 | 3.893,0 | 10,2 | 12.518,5 | 5.545,2 | 35 | −2,82 | 8,6 ± 4,6 | **có** |
| 0,8 | 3.893,5 | 11,0 | 12.517,5 | 5.545,3 | 38 | −2,95 | 8,2 ± 3,8 | **có** |
| 1,0 | 3.894,3 | 10,2 | 12.536,5 | 5.545,3 | 39 | −3,00 | 7,3 ± 3,4 | **có** |
| 1,25 | 3.887,9 | 9,5 | 12.492,3 | 5.545,4 | 43 | −3,21 | 13,8 ± 2,9 | không (xem Q24) |
| **1,5** | **3.901,7** | 10,3 | 12.535,9 | 5.533,8 | 45 | −3,10 | 0 (tốt nhất) | **có** |
| 2,0 | 3.897,4 | 9,9 | 12.528,1 | 5.545,2 | 47 | −3,40 | 4,2 ± 3,6 | **có** |
| 3,0 | 3.889,5 | 10,7 | 12.471,2 | 5.544,7 | 53 | −3,79 | 12,1 ± 4,0 | không |
| 5,0 | 3.883,2 | 10,8 | 12.450,5 | 5.543,4 | 61 | −4,93 | 18,4 ± 4,4 | không |
| 10 | 3.837,2 | 10,0 | 12.539,1 | 5.233,8 | 69 | −∞ | 64,4 ± 4,8 | không |
| 30 | 3.693,0 | 9,8 | 13.579,8 | 3.436,3 | 75 | −∞ | 208,6 ± 4,3 | không |

**Đọc bảng:**
- Đường N(π_θ) có ba đoạn: tăng (θ từ 0 đến 0,4), phẳng (0,4 đến 2), giảm (từ 3 trở đi, rõ từ 10 khi không tiêu hết B). Cực đại nằm bên trong lưới.
- **Khoảng θ\* = [0,4; 2]**: tập các θ không kém θ tốt nhất ở mức 95% đồng thời (so sánh bội với cái tốt nhất, hiệu ghép cặp theo seed, Bonferroni trên 15 phép so, phân vị t với 29 bậc tự do, hệ số 2,922). Mốc 1,25 nằm trong khoảng nhưng bị loại do nhiễu của κ auto (câu hỏi mở Q24).
- Regret theo N khi dùng θ khác (hiệu ghép cặp, CI 95%): θ = 0 (không cắt ô): +53,3 ± 4,8 (1,37%); θ mặc định 0,35: +14,4 ± 4,1 (0,37%); θ = 0,5: +9,9 ± 3,9 (0,25%); θ = 10: +64,4 ± 4,8 (1,65%); θ = 30: +208,6 ± 4,3 (5,35%).
- Mốc so sánh (`runs/b7a/gte`, seed 0–9): `all_off` 3.439,6; `all_on` không ngân sách 4.652,5. `all_on` có ngân sách B (20 seed, A2(b)): 3.700,4.

File: `results/policy_results.parquet` (480 lượt), `results/theta_sweep.parquet`, `meta/run_metadata.parquet` (κ, B của từng lượt), `results/theta_sweep.png`.

### Phân tích độ nhạy (`runs/b7b/sens_*`, 16 θ × 10 seed mỗi bộ)

| Thư mục | Override | B (USD/kỳ) | N tại θ = 0 | N lớn nhất (θ) | N tại θ = 30 | Khoảng θ\* | Regret của θ = 0 |
|---|---|---|---|---|---|---|---|
| `sens_fraction_0p1` | `budget.fraction=0.1` | 1.848,6 | 3.584 | 3.601,9 (0,6) | 3.573 | [0; 10] | +18,0 ± 5,5 (0,50%) |
| `sens_fraction_0p6` | `budget.fraction=0.6` | 11.091,6 | 4.235 | 4.299,0 (0,4) | 3.685 | [0,2; 1] | +64,2 ± 8,2 (1,49%) |
| `sens_voucher_0p3` | `voucher.pct_of_fare=0.3` | 9.076,3 | 3.956 | 4.025,8 (1,5) | 3.775 | [0,3; 5] | +70,3 ± 5,5 (1,75%) |
| `sens_demand_1p5` | `demand.demand_scale=1.5` | 6.430,7 | 5.400 | 5.630,4 (2) | 5.347 | [0,4; 2], loại 0,5; 0,8; 1,0 | +230,9 ± 16,3 (4,10%) |

- Ở cả bốn biến thể đường có đủ ba đoạn tăng, phẳng, giảm trên lưới kéo dài.
- θ = 0,4 và θ = 0,6 thuộc tập θ\* ở cả năm kịch bản (kể cả cấu hình chuẩn): kết luận về ngưỡng bền với mức ngân sách, cường độ voucher và độ căng thị trường.
- Lợi ích của tầng ô tăng theo độ căng (0,5% khi ngân sách rất chặt, 1,4% ở cấu hình chuẩn, 4,1% khi cầu gấp rưỡi); θ\* nhọn dần khi ngân sách lớn hơn.
- Các bộ này là phân tích độ nhạy, không phải cấu hình chính: `fraction` 0,6 làm chính sách cũ hết bị ngân sách ràng buộc, `demand_scale` 1,5 nằm ngoài hiệu chỉnh P3.

### Lệnh sinh lại (PowerShell)

```powershell
$py = ".venv\Scripts\python.exe"
$ref = @("--config", "config/default.yaml", "--config", "config/sweep_reference.yaml")
& $py -m sim run --mode sweep_theta @ref --set sweep.n_seeds=30 --out runs/b7b/sweep_theta_ref
& $py -m sim run --mode sweep_theta @ref --set budget.fraction=0.1 --out runs/b7b/sens_fraction_0p1
& $py -m sim run --mode sweep_theta @ref --set budget.fraction=0.6 --out runs/b7b/sens_fraction_0p6
& $py -m sim run --mode sweep_theta @ref --set voucher.pct_of_fare=0.3 --out runs/b7b/sens_voucher_0p3
& $py -m sim run --mode sweep_theta @ref --set demand.demand_scale=1.5 --out runs/b7b/sens_demand_1p5
# đồ thị, bảng θ* và kiểm tra
& $py -m analysis.plots theta_sweep runs/b7b/sweep_theta_ref --gte runs/b7a/gte
& $py -m analysis.check_dataset runs/b7b/sweep_theta_ref runs/b7b/sens_fraction_0p1 runs/b7b/sens_fraction_0p6 runs/b7b/sens_voucher_0p3 runs/b7b/sens_demand_1p5
```

Thời gian (8 tiến trình): sweep tham chiếu 30 seed 702 giây; mỗi sweep độ nhạy 5 đến 6 phút. `check_dataset` ngày 02/10: cả 5 thư mục OK. Cần `pip install -e ".[analysis]"` để vẽ đồ thị.

### Dùng cho phân tích tuần 5

```python
import pandas as pd
from analysis.metrics import theta_star_set, theta_star_interval, sweep_regret
runs = pd.read_parquet("runs/b7b/sweep_theta_ref/results/policy_results.parquet")
theta_star_interval(theta_star_set(runs))      # (1.5, 0.4, 2.0)
sweep_regret(runs, theta_hat=0.8)              # regret theo N của một ngưỡng ước lượng θ̂
```

Ước lượng θ̂ được chấm bằng regret theo N, không bằng khoảng cách tới θ\* (T-31): trong đoạn phẳng regret gần 0 dù θ̂ lệch xa θ = 1,5.

`runs/p6/` (sweep 12 θ × 10 seed và các sweep chẩn đoán 5 seed dùng để ra quyết định T-31) đã được thay bằng các bộ trên; có thể xóa.

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

