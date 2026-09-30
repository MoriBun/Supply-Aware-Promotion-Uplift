# Supply-Aware Promotion Uplift: simulator gọi xe

Simulator agent-based cho ride-hailing (solo) trên lưới ô lục giác. Dùng để:
- sinh dữ liệu có confounding kiểm soát được;
- đo giá trị thật N(π) (số chuyến hoàn thành) của chính sách voucher dưới cùng ngân sách B;
- tìm ngưỡng căng cung θ\* để tắt khuyến mãi.

## Cài đặt (Python 3.11)

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate            # PowerShell;  Git Bash: source .venv/Scripts/activate
pip install -e ".[dev]"
```

## Lệnh

```bash
pytest -q                          # test nhanh
pytest -q -m slow                  # test nghiệm thu (chậm)
python -m sim run --mode evaluate --config config/default.yaml --set policy.threshold.theta=0.4
python -m sim run --mode gte --config config/default.yaml --config tests/fixtures/tiny.yaml   # nhiều lớp config
```

Các mode: `generate`, `evaluate`, `sweep_theta`, `gte`, `calibrate_budget`, `throughput_curve` (spec §7).

## Tài liệu

| File | Nội dung |
|---|---|
| `CLAUDE.md` | quy tắc làm việc và quy tắc cứng; đọc đầu tiên |
| `docs/Simulation_design_fix.pdf` | báo cáo thiết kế: *vì sao* |
| `docs/spec.md` | đặc tả cài đặt: *làm thế nào*; nguồn sự thật cho code |
| `config/default.yaml` | mọi tham số |
| `docs/schema.md` | định dạng dữ liệu đầu ra |
| `docs/tests.md` | kiểm thử và tiêu chí đạt |
| `docs/plan.md` | các mốc P0–P8 |
| `docs/phan_cong.md` | phân công theo sprint cho Tình và Hoàng: ai làm gì, sở hữu file, điểm bàn giao |
| `docs/decisions.md` | nhật ký quyết định và **câu hỏi mở** |
| `docs/problem_statement.md`, `docs/survey.md` | đề bài gốc, khảo sát tài liệu (nền, không phải nguồn sự thật cho code) |

## Cấu trúc

```
sim/        mã nguồn (spec §3): config, rng, M1–M13, policies/
tests/      pytest; fixtures/tiny.yaml là lớp ghi đè cho test nhanh
config/     default.yaml
docs/       thiết kế, spec, schema, tests, plan, decisions
runs/       output (không commit)
```

## Trạng thái

P0 đã xong: config, RNG có khóa (CRN), CLI rỗng. Sprint hiện tại: **S0**, chốt hợp đồng giao diện giữa hai luồng. Xem `docs/phan_cong.md`.
