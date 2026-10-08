# Supply-Aware Promotion Uplift: simulator gọi xe

Simulator agent-based cho ride-hailing (solo, không đi chung) trên lưới ô lục giác, phục vụ **Supply-Aware Promotion Impact Framework**. Dùng để:

- sinh dữ liệu có confounding kiểm soát được (chính sách cũ nhắm khách theo biến ẩn);
- đo giá trị thật **N(π) = số chuyến hoàn thành** của một chính sách voucher dưới cùng ngân sách B (lợi nhuận V(π) là chỉ tiêu phụ);
- tìm ngưỡng căng cung **θ\*** để tắt khuyến mãi theo ô và theo khung giờ 15 phút.

Simulator tất định theo (config, seed): cùng `config_hash` và cùng seed cho ra cùng kết quả; đổi chính sách không làm đổi số ngẫu nhiên của bất kỳ session nào (CRN).

## Mục lục

1. [Yêu cầu](#1-yêu-cầu)
2. [Cài đặt](#2-cài-đặt)
3. [Chạy simulator](#3-chạy-simulator)
4. [Kết quả đầu ra](#4-kết-quả-đầu-ra)
5. [Kiểm thử](#5-kiểm-thử)
6. [Dashboard quản trị](#6-dashboard-quản-trị)
7. [Phân tích và notebook](#7-phân-tích-và-notebook)
8. [Cấu trúc thư mục](#8-cấu-trúc-thư-mục)
9. [Tài liệu](#9-tài-liệu)
10. [Quy tắc làm việc](#10-quy-tắc-làm-việc)
11. [Trạng thái](#11-trạng-thái)

## 1. Yêu cầu

| Thành phần                    | Phiên bản           | Ghi chú                                                     |
| ------------------------------- | --------------------- | ------------------------------------------------------------ |
| Python                          | **3.11**        | `requires-python >= 3.11`                                  |
| numpy, pandas, pyarrow, pyyaml  | xem`pyproject.toml` | phụ thuộc lõi của`sim/`                                |
| pytest                          | ≥ 8                  | extra`dev`                                                 |
| matplotlib, lightgbm, ipykernel |                       | extra`analysis`, chỉ cho `analysis/` và `notebooks/` |
| fastapi, uvicorn, httpx         |                       | extra`dashboard`, chỉ cho `dashboard/`                  |

Không cần Node: dashboard dùng React qua `htm`, thư viện đã vendor sẵn trong `dashboard/static/vendor/`. `sim/` không bao giờ import từ `analysis/` hay `dashboard/`.

## 2. Cài đặt

### Windows (PowerShell)

```powershell
git clone <url-repo> Supply-Aware-Promotion-Uplift
cd Supply-Aware-Promotion-Uplift
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### Git Bash / Linux / macOS

```bash
python3.11 -m venv .venv
source .venv/Scripts/activate      # Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### Cài thêm theo nhu cầu

```bash
pip install -e ".[dev,analysis]"              # chạy analysis/ và notebooks/
pip install -e ".[dev,dashboard]"             # chạy dashboard/
pip install -e ".[dev,analysis,dashboard]"    # đủ cả
```

### Kiểm tra cài đặt

```bash
python -m sim run --mode evaluate --config config/default.yaml --config tests/fixtures/tiny.yaml --out runs/smoke
pytest -q
```

Lệnh đầu chạy một lượt nhỏ (7 ô, 10 xe, cửa sổ 2 giờ) trong vài giây và in `N_mean`, `V_mean`, `spent_mean`. Lệnh sau phải báo toàn bộ test nhanh pass.

## 3. Chạy simulator

Cú pháp chung (spec §7, §9):

```bash
python -m sim run --mode <mode> --config config/default.yaml [--config overlay.yaml ...] [--set key.sub=value ...] [--out DIR] [--log-level minimal|full] [--profile]
```

| Tham số             | Ý nghĩa                                                                                                                     |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `--mode`           | một trong các mode ở bảng dưới                                                                                          |
| `--config`         | file YAML; lặp lại để chồng lớp, file sau ghi đè file trước. File đầu luôn là`config/default.yaml`            |
| `--set a.b=c`      | ghi đè một khóa, giá trị được parse như YAML (`--set policy.threshold.theta=0.4`, `--set budget.enforce=false`) |
| `--out`            | thư mục kết quả; mặc định`runs/<mode>-<config_hash>`                                                                 |
| `--log-level full` | ghi thêm bảng session và order trong`evaluate`, `sweep_theta`, `gte`                                                 |
| `--profile`        | in thời gian từng bước của engine mỗi tick                                                                              |

### Các mode

| Mode                 | Làm gì                                                                                             | Bảng kết quả chính                               |
| -------------------- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| `generate`         | chạy một chính sách dài ngày, ghi đủ`observed/`, `market/`, `hidden/` để phân tích | `results/policy_results` + dữ liệu session/order |
| `evaluate`         | chạy một chính sách với nhiều seed, báo N(π), V(π), chi voucher                             | `results/policy_results`                           |
| `sweep_theta`      | quét lưới θ cho π<sub>θ</sub>, cùng B và cùng seed, tìm θ\* = argmax N(π<sub>θ</sub>)   | `results/theta_sweep`                              |
| `gte`              | hiệu ứng toàn hệ GTE = N(all_on) − N(all_off), không ngân sách, ghép cặp theo seed         | `results/policy_results`                           |
| `calibrate_budget` | tính ngân sách B = tỷ lệ × chi tiêu của pilot`all_on` không ngân sách                   | `meta/run_metadata` (`budget_B_usd`)             |
| `throughput_curve` | đường throughput theo mức cầu (nghiệm thu A1, gate P2/P3)                                      | `results/throughput_curve`                         |

### Ví dụ

```bash
# Đánh giá pi_theta với theta = 0.4, 5 seed, giữ bảng session/order
python -m sim run --mode evaluate --config config/default.yaml --set policy.threshold.theta=0.4 --set sweep.n_seeds=5 --log-level full --out runs/eval_theta04

# Đánh giá chính sách cũ (legacy) dưới ngân sách
python -m sim run --mode evaluate --config config/default.yaml --set policy.name=legacy --out runs/eval_legacy

# Quét theta với lưới tham chiếu kéo dài tới 30 (config/sweep_reference.yaml)
python -m sim run --mode sweep_theta --config config/default.yaml --config config/sweep_reference.yaml --out runs/sweep_ref

# GTE 10 seed, một ngày
python -m sim run --mode gte --config config/default.yaml --out runs/gte

# Hiệu chỉnh ngân sách
python -m sim run --mode calibrate_budget --config config/default.yaml --out runs/cal

# Sinh dữ liệu 28 ngày từ thiết kế switchback cụm 1 (xem docs/datasets.md cho các bộ chuẩn)
python -m sim run --mode generate --config config/default.yaml --set policy.name=experiment --set experiment.design=cluster_switchback --set generate.days=28 --out runs/sw_c1_28d
```

Chính sách có sẵn (`policy.name`): `all_on`, `all_off`, `legacy`, `threshold` (π<sub>θ</sub>: tầng ô theo slack dự báo so với θ, tầng rider theo điểm τ̂ ≥ κ), `experiment` (áp thiết kế của M10: switchback theo cụm, A/B theo rider). Mọi tham số nằm trong `config/default.yaml` kèm chú thích nguồn; không hard-code trong code.

Hiệu năng mục tiêu: ≤ 30 giây cho một ngày mô phỏng với cấu hình mặc định (37 ô, 240 xe). Các mode nhiều seed chạy song song bằng `multiprocessing` kiểu `spawn`.

## 4. Kết quả đầu ra

Mỗi lượt chạy ghi một thư mục theo `docs/schema.md`:

```
runs/<out>/
  meta/run_metadata.parquet        config_hash, seed, mode, budget_B_usd, phiên bản
  observed/riders.parquet          dữ liệu quan sát được: mô hình và chính sách được đọc
  observed/sessions.parquet
  observed/orders.parquet
  market/slot_snapshots.parquet    I, E, O, W, slack, utilization theo (ô, slot)
  hidden/riders_hidden.parquet     ground truth (u_latent, propensity_true, ...): CHỈ để đánh giá
  hidden/sessions_hidden.parquet
  results/policy_results.parquet   một dòng mỗi (chính sách, seed): N_completed, V_profit_usd, voucher_spent_usd
  results/theta_sweep.parquet      chỉ sweep_theta
  results/throughput_curve.parquet chỉ throughput_curve
```

`runs/` không commit. Các bộ dữ liệu chuẩn cho phân tích (B7a, B7b, s5, h53...) cùng lệnh tái lập ghi trong `docs/datasets.md`. Kiểm tra một bộ vừa sinh:

```bash
python -m analysis.check_dataset runs/<out>          # schema, rò biến ẩn, tổng hợp
python -m analysis.check_budget runs/<out>           # bất biến spent + committed + reserved <= B
```

## 5. Kiểm thử

```bash
pytest -q                     # test nhanh (mặc định bỏ qua test đánh dấu slow)
pytest -q -m slow             # test nghiệm thu A1–A5, CAL (chậm, vài phút)
pytest -q tests/test_dashboard.py
pytest -q tests/test_policies.py -k threshold
```

- Test nhanh dùng lớp ghi đè `tests/fixtures/tiny.yaml` (7 ô, 10 xe, cửa sổ 2 giờ) chồng lên `config/default.yaml`.
- `tests/fakes.py` chứa đồ giả dùng chung giữa hai luồng.
- Tiêu chí đạt của từng test nghiệm thu ở `docs/tests.md`. Không nới tiêu chí hay sửa test cho pass; không đạt thì báo số liệu và ghi `docs/log.md`.
- Nếu Windows báo lỗi quyền ở thư mục tạm mặc định của pytest, thêm `--basetemp="$LOCALAPPDATA/Temp/pytest-sim"`.

## 6. Dashboard quản trị

Giao diện web để chạy, xem animation và giải thích một lượt mô phỏng, quét θ có tiến độ theo từng seed, và xem kết quả thực nghiệm đã lưu trong `runs/`.

```bash
pip install -e ".[dashboard]"
python -m dashboard                 # http://127.0.0.1:8050/   (--port, --host, --reload)
```

Lượt chạy từ dashboard ghi vào `runs/dashboard/<id>/` đúng schema như CLI, cộng thêm frame từng tick. Phải chạy bằng `python -m dashboard` (pool tiến trình `spawn`), không chạy từ REPL. Chi tiết trang, API và kiến trúc: `dashboard/README.md`; hướng dẫn sử dụng: `dashboard/huongdan.md`.

## 7. Phân tích và notebook

`analysis/` chứa toàn bộ tính toán tuần 5 trở đi (metric, bảng chính sách dưới cùng B, DR-learner, θ̂, interference, confounding). Notebook chỉ gọi hàm trong `analysis/`.

```bash
pip install -e ".[analysis]"

python -m analysis.policy_table --config config/default.yaml --out runs/s5/policy_table
python -m analysis.plots theta_sweep runs/sweep_ref --gte runs/gte
python -m analysis.plots throughput runs/<throughput run>
python -m analysis.tension runs/h53/all_off_3d
python -m analysis.interference designs --gte runs/b7a/gte runs/b7a/rider_ab_28d runs/b7a/switchback_c1_28d
```

| Notebook                                   | Nội dung                                                            |
| ------------------------------------------ | -------------------------------------------------------------------- |
| `notebooks/01_simulator_kiem_dinh.ipynb` | mô hình thị trường, throughput, A1–A5, CAL, các bộ dữ liệu |
| `notebooks/02_danh_gia_chinh_sach.ipynb` | N(π), V(π) dưới cùng B, bậc thang θ\*, Qini so với N         |
| `notebooks/03_interference.ipynb`        | chệch theo thiết kế thí nghiệm, độ nhạy theo`u_latent`     |
| `notebooks/04_uoc_luong_va_theta.ipynb`  | DR-learner, chọn ŝ, tác hại theo giờ, θ̂ so với θ\*, regret |
| `notebooks/05_confounding.ipynb`         | so thô, DR, lát explore                                            |

Mở notebook trong VS Code với kernel là Python của `.venv`. Hình xuất cho báo cáo nằm ở `docs/figures/`. Quy ước chi tiết: `notebooks/README.md`.

## 8. Cấu trúc thư mục

```
Supply-Aware-Promotion-Uplift/
├── CLAUDE.md                     quy tắc làm việc và quy tắc cứng; đọc đầu tiên
├── README.md
├── pyproject.toml                gói supply-aware-sim; extras dev / analysis / dashboard; cấu hình pytest
├── config/
│   ├── default.yaml              MỌI tham số, mỗi khóa có chú thích nguồn [report]/[data]/[paper]/[assume]
│   └── sweep_reference.yaml      lớp phủ: lưới θ kéo dài tới 30 cho sweep tham chiếu (T-31)
├── sim/                          mã nguồn simulator (spec §3); không import analysis/ hay dashboard/
│   ├── __main__.py, cli.py       python -m sim run ...
│   ├── config.py                 nạp YAML nhiều lớp, --set, config_hash
│   ├── rng.py                    luồng ngẫu nhiên có khóa (CRN): rng_for(stream, *key)
│   ├── space.py                  M1  lưới lục giác, torus, ma trận khoảng cách, ETA đón
│   ├── population.py             sinh thế giới từ world_seed: trọng số ô, rider, ca tài xế
│   ├── demand.py                 M2  session Poisson theo (ô, tick), số rút sẵn
│   ├── pricing.py                M3  giá cước, giá trị voucher, tầng voucher
│   ├── choice.py                 M4  logit đặt xe và xác suất ground truth
│   ├── matching.py               M5  ghép FIFO, cùng ô trước rồi mở rộng vành
│   ├── trips.py                  M6  đón, trả, thanh toán
│   ├── cancel.py                 M7  bỏ cuộc sau max_wait, hủy khi xe đang đến
│   ├── supply.py                 M8  ca làm việc, rời chỉ khi rảnh; độc lập với chính sách
│   ├── reposition.py             M9  dịch chuyển xe rảnh lâu theo trọng số tĩnh
│   ├── experiment.py             M10 thiết kế thí nghiệm: cụm, switchback, A/B rider
│   ├── monitor.py                M11 I, E, O, W, slack theo (ô, slot); SnapshotView không nhìn trước
│   ├── logger.py                 M12 ghi Parquet theo docs/schema.md
│   ├── runner.py                 M13 run id, nhiều seed song song, 6 mode chạy
│   ├── budget.py                 sổ cái voucher: spent + committed + reserved <= B
│   ├── engine.py                 vòng lặp tick 10 bước, warm-up / cửa sổ / cool-down, RunResult
│   ├── state.py                  trạng thái struct-of-arrays (xe, order, session)
│   └── policies/
│       ├── base.py               giao diện Policy, SessionBatch, LegacyHiddenView
│       ├── fixed.py              all_on / all_off
│       ├── legacy.py             chính sách cũ: luật slack trễ + ε, nhắm rider theo u_latent
│       ├── threshold.py          π_θ: tầng ô (slack dự báo so với θ, trễ) + tầng rider (điểm >= κ)
│       ├── scores.py             hàm điểm cho tầng rider
│       └── experiment.py         áp phân bổ của M10
├── analysis/                     phân tích tuần 5+; notebook chỉ gọi hàm ở đây
│   ├── io.py                     đọc thư mục run (load_run không bao giờ trả bảng ẩn)
│   ├── metrics.py                giá trị chính sách + CI, hiệu ghép cặp, Qini / AUUC, tập θ*
│   ├── policy_table.py           N(π), V(π) của nhiều chính sách dưới cùng B
│   ├── scores.py, uplift.py      điểm uplift, DR-learner
│   ├── theta.py, tension.py      θ̂ từ dữ liệu thí nghiệm; chọn chỉ báo căng cung ŝ
│   ├── estimate.py               hiệu ứng voucher theo mức căng cung, đổi dấu (A4)
│   ├── interference.py           chệch theo thiết kế và confounding ẩn so với ground truth
│   ├── confounding.py            confounding do chính sách cũ nhắm khách
│   ├── qini_vs_value.py          Qini so với giá trị chính sách
│   ├── validation.py, figures.py, plots.py, notebook.py   số kiểm định, hình notebook, hình gate
│   ├── check_dataset.py, check_budget.py                   kiểm tra bộ dữ liệu, kiểm toán ngân sách
│   ├── tlc_hourly.py             đối chiếu với NYC TLC theo giờ
│   └── models/                   mô hình DR đã học (json, txt)
├── dashboard/                    FastAPI + React (htm), không cần Node (T-38)
│   ├── __main__.py, server.py    python -m dashboard; /api/* và static
│   ├── trace.py                  chép vòng lặp engine.run + ghi frame mỗi tick
│   ├── sweep.py, jobs.py         quét θ có tiến độ; hàng đợi nền
│   ├── summary.py, results.py, geometry.py
│   ├── static/                   index.html, css/, js/, vendor/ (React, ReactDOM, htm), brand/
│   ├── README.md                 trang, API, kiến trúc
│   └── huongdan.md               hướng dẫn sử dụng
├── notebooks/                    5 notebook kết quả + README.md
├── tests/                        pytest; fixtures/tiny.yaml lớp ghi đè cho test nhanh; fakes.py đồ giả chung
├── docs/                         thiết kế, spec, schema, tests, plan, phan_cong, decisions, log, datasets, figures/
└── runs/                         output (không commit); tái lập theo docs/datasets.md
```

## 9. Tài liệu

Đọc theo thứ tự:

| File                                                                     | Nội dung                                                                           |
| ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| `CLAUDE.md`                                                            | quy tắc làm việc và quy tắc cứng                                              |
| `docs/Simulation_design_fix.pdf`                                       | báo cáo thiết kế:*vì sao*                                                    |
| `docs/spec.md`                                                         | đặc tả cài đặt:*làm thế nào*; **nguồn sự thật cho code**        |
| `config/default.yaml`                                                  | mọi tham số                                                                       |
| `docs/schema.md`                                                       | định dạng dữ liệu đầu ra, danh sách cột ẩn                                |
| `docs/tests.md`                                                        | kiểm thử và tiêu chí đạt                                                     |
| `docs/plan.md`                                                         | các mốc P0–P8                                                                    |
| `docs/phan_cong.md`                                                    | phân công theo sprint cho Tình và Hoàng, sở hữu file, điểm bàn giao       |
| `docs/decisions.md`                                                    | nhật ký quyết định, mọi lệch khỏi spec,**câu hỏi mở**              |
| `docs/log.md`                                                          | nhật ký công việc từng người:**nguồn sự thật về tiến độ**       |
| `docs/datasets.md`                                                     | các bộ dữ liệu trong`runs/` và lệnh tái lập                               |
| `docs/bao_cao_phuong_phap_v1.md`                                       | báo cáo phương pháp bản 1                                                     |
| `docs/dashboard_review.md`                                             | rà soát nội dung dashboard                                                       |
| `docs/problem_statement.md`, `docs/survey.md`, `docs/BaoCao_*.pdf` | đề bài gốc, khảo sát, báo cáo nền (không phải nguồn sự thật cho code) |
