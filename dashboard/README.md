# Dashboard quản trị simulator (`dashboard/`)

Giao diện web để **chạy, xem và giải thích** một lượt mô phỏng của simulator gọi xe: tài xế di chuyển trên lưới lục giác theo từng phút, chính sách π<sub>θ</sub> cắt voucher ở ô căng cung (ŝ < θ), tầng rider phát voucher theo điểm τ̂ ≥ κ trong ngân sách B, và các kết quả thực nghiệm đã lưu trong `runs/` (đường N(π<sub>θ</sub>), bảng chính sách dưới cùng B, throughput, GTE).

Stack: **FastAPI** (Python, cùng `.venv` với simulator) + **React 18 qua htm** (không cần Node, không cần build; thư viện vendor sẵn trong `static/vendor/`, chạy offline). Quyết định: `docs/decisions.md` T-38.

## Cài đặt và chạy

```powershell
.venv\Scripts\activate
pip install -e ".[dashboard]"          # fastapi, uvicorn, httpx
python -m dashboard                    # http://127.0.0.1:8050/  (--port, --host, --reload)
```

Lượt chạy từ dashboard ghi vào `runs/dashboard/<id>/` (không commit, như mọi `runs/`). Khi mở lại server, các lượt đã xong được nạp lại từ đĩa.

## Các trang

| # | Trang | Trả lời câu hỏi | Dữ liệu |
|---|---|---|---|
| 1 | **Tổng quan** | lượt chạy cho N(π), V(π), chi/B, % (ô, slot) bị cắt bao nhiêu; cấu hình nào; chuỗi theo slot | `/api/runs/{id}`, `/summary` |
| 2 | **Mô phỏng** | đặt tham số (chính sách, θ, phạm vi ŝ, hàm điểm, κ, B, voucher, đội xe, cầu, cửa sổ, seed) rồi chạy; tiến độ theo giai đoạn: pilot B → κ auto → mô phỏng → ghi bảng | `POST /api/runs`, `/api/config/validate` |
| 3 | **Bản đồ động** | *animation*: xe rảnh / đi đón / chở khách / dịch chuyển, khách đang chờ, ô bật/tắt voucher (gạch chéo = bị cắt), hiệu ứng phát voucher, chặn ngân sách, ghép xe, hoàn thành, hủy; đồng hồ, tốc độ ×1…×120, thanh thời gian, theo dõi trực tiếp khi đang chạy; sổ ngân sách kỳ hiện tại; bấm ô để xem ŝ so với θ | `/frames` (từng chunk), `/slots` |
| 4 | **Vùng & ngưỡng θ** | ô nào bị cắt lúc nào: bản đồ nhiệt ô × slot (bật/tắt, ŝ dự báo, slack thực), chi tiết một ô, ô bị cắt nhiều nhất, nhật ký bật/tắt | `/slots`, `/summary` |
| 5 | **Phân phát voucher** | ai nhận voucher: theo giờ (phát / bị chặn), phân khúc rider, cơ chế gán, phân bố điểm τ̂ và κ; ngân sách theo thời gian (chi + đặt + giữ ≤ B) | `/summary` |
| 6 | **Kết quả thực nghiệm** | đường N(π<sub>θ</sub>) ± SE của mọi sweep trong `runs/` (chọn tối đa 4, chấm = θ\*), bảng N(π) dưới cùng B (`analysis.policy_table`), throughput A1, GTE, hình của notebook `docs/figures/` | `/api/results/*` |

Link thẳng một lượt: `#/map?run=<id>`.

## Kiến trúc

```
dashboard/
  trace.py      vòng lặp 10 bước giống sim.engine.run + ghi frame mỗi tick (xe, bộ đếm ô, sổ cái, sự kiện) và CellDecision/snapshot mỗi slot
  jobs.py       hàng đợi một luồng nền: load_config → runner.calibrate_budget → runner.kappa_auto → run_traced → logger.write_run / write_results
  summary.py    KPI, chuỗi theo slot, sự kiện bật/tắt, phân phát voucher (từ buffer + trace)
  geometry.py   tọa độ tâm ô, vector hiển thị trên torus (xe đi qua biên hiện ra ở cạnh đối diện)
  results.py    đọc results/*.parquet có sẵn trong runs/ (sweep, policy_table, throughput, gte)
  server.py     FastAPI: /api/* và static; create_app(root, runs_dir) cho test
  static/       index.html, css/app.css, js/{lib,charts,hexmap,pages,app}.js, vendor/ (React, ReactDOM, htm)
```

Quy tắc giữ nguyên với simulator:
- `sim/` **không** import từ `dashboard/`; dashboard chỉ dùng các factory công khai (`build_world`, `make_policy`, `runner.*`, `logger.*`).
- `trace.py` **không sửa** `engine.py` (file của Hoàng): nó chép vòng lặp và chỉ đọc trạng thái. `tests/test_dashboard.py::test_traced_run_matches_engine` kiểm hai vòng lặp cho cùng `RunResult` và cùng bảng session/order. Đổi thứ tự bước trong `engine.run` thì sửa `trace.py` theo.
- Mọi số ngẫu nhiên, ngân sách, CRN, không-nhìn-trước y như chạy bằng CLI: một lượt dashboard = `evaluate` một seed với `log_level=full`, cộng frame.
- Bảng ghi ra đúng `docs/schema.md` (`observed/`, `market/`, `hidden/`, `results/policy_results`, `meta/run_metadata`, `mode = dashboard`); thêm `dashboard/{trace.npz, slots.npz, meta.json, geometry.json, summary.json}`.

Frame (mỗi tick): `status`, `cell` (ô hiện tại hoặc ô đích khi đang đi), `origin` (ô xuất phát), `move_start`, `busy_until` của từng xe → front end nội suy vị trí giữa hai tâm ô; `idle/enroute/ontrip/waiting` theo ô; bộ đếm cộng dồn order theo trạng thái, session/offer/blocked/request; sổ cái kỳ hiện tại (cent); danh sách sự kiện `(loại, ô, ô2)`.

## API

| Method | Đường dẫn | Nội dung |
|---|---|---|
| GET | `/api/config/defaults` | `config/default.yaml`, danh sách hàm điểm, preset |
| POST | `/api/config/validate` | `{overrides:[...], layers:[...]}` → hash, số ô, cửa sổ hoặc lỗi `--set` |
| GET/POST | `/api/runs` | danh sách / xếp hàng một lượt (`name, overrides, layers, budget_usd?, kappa?`) |
| GET | `/api/runs/{id}` | trạng thái, tiến độ, log, cấu hình, hình học lưới, KPI |
| GET | `/api/runs/{id}/frames?start=&count=` | frame theo chunk (tối đa 2000) |
| GET | `/api/runs/{id}/slots` | ma trận ô × slot: `promo_on, s_hat, slack, idle_avg, …` |
| GET | `/api/runs/{id}/summary` | KPI, chuỗi theo slot, sự kiện bật/tắt, phân phát |
| GET | `/api/results/{sweeps,policy_tables,throughput,gte,evaluations,figures}` | kết quả đã lưu trong `runs/`, hình `docs/figures/` |

## Test

```powershell
pytest -q tests/test_dashboard.py
```

4 test: tracer trùng engine (RunResult, session, order), frame nhất quán với bộ đếm và bất biến ngân sách theo tick, vector torus, API chạy trọn một lượt tiny rồi nạp lại từ đĩa.

## Giới hạn và việc có thể làm tiếp

- Mô phỏng chạy trong một luồng nền của tiến trình server (GIL): trong lúc chạy, API phản hồi chậm hơn một chút; các lượt xếp hàng chạy tuần tự. Mặc định 1 ngày × 240 xe mất ≈ 1–2 phút gồm pilot B và κ auto.
- Frame giữ trong bộ nhớ của server trong phiên; lượt dài nhiều ngày sẽ nặng (≈ 5 MB/ngày với 240 xe).
- Giao diện viết bằng htm (template literal) để không cần Node. Muốn JSX/TypeScript: tạo dự án Vite trong `dashboard/web/`, chuyển từng file trong `static/js/` (mỗi file đã là một module ES), build ra `static/`.
