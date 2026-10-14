# Notebook kết quả (Sprint 6, H-27)

| Notebook | Người làm | Nội dung |
|---|---|---|
| `01_simulator_kiem_dinh.ipynb` | Tình | mô hình thị trường, throughput và WGC, A1–A5, CAL, các bộ dữ liệu |
| `02_danh_gia_chinh_sach.ipynb` | Tình | N(π), V(π) dưới cùng B, bậc thang θ\*, Qini so với N |
| `03_interference.ipynb` | Tình | chệch theo thiết kế thí nghiệm, độ nhạy theo `u_latent` |
| `04_uoc_luong_va_theta.ipynb` | Hoàng | DR-learner, chọn ŝ, tác hại theo giờ, θ̂ so với θ\*, regret |
| `05_confounding.ipynb` | Hoàng | so thô, DR, lát explore |

## Cài đặt

`pip install -e ".[analysis]"` (có `ipykernel`). Trong VS Code: mở notebook, chọn kernel là Python của `.venv`.

## Quy ước

- Notebook **chỉ gọi** hàm trong `analysis/`. Phép tính mới viết vào `analysis/*.py` kèm test rồi mới gọi.
- Chỉ chủ notebook sửa notebook đó (file `.ipynb` gần như không gộp tay được).
- Markdown tiếng Việt; comment trong code tiếng Anh.
- Trước khi commit: "Restart & Run All", commit **kèm output** để xem được trên GitHub.
- Hình cho báo cáo và slides: `save_figure(fig, "04_ten_hinh")` ghi `docs/figures/04_ten_hinh.png`; tiền tố là số của notebook.
- `runs/` không commit; thiếu thư mục nào thì sinh lại theo lệnh trong `docs/datasets.md`.

## Ô đầu tiên của mỗi notebook

```python
from analysis.notebook import require_runs, setup
from analysis.plots import save_figure

plt = setup()   # về gốc repo (đường dẫn runs/... như ở dòng lệnh), kiểu hình chung, bảng pandas rộng
# Mọi dữ liệu notebook cần; thiếu thì báo ngay, kèm chỉ dẫn tới docs/datasets.md
sweep_dir, gte_dir = require_runs("runs/s5/sweep_ring1_dr", "runs/b7a/gte")
```
