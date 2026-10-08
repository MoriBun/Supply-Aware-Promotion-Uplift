# Rà soát và cải thiện dashboard · 07/10/2026

## Hiểu đề tài và nguồn đối chiếu

Đề tài kiểm tra khuyến mãi gọi xe khi cung hữu hạn: voucher có thể tăng yêu cầu đặt xe nhưng không tạo thêm chuyến hoàn thành, đồng thời làm tăng chờ và hủy. Giá trị chính sách ở cấp thị trường là căn cứ đánh giá; Qini hoặc chênh lệch hai nhánh rider không đủ để quyết định rollout.

Đối chiếu `docs/problem_statement.md` (RQ1–RQ3 và nghiệm thu), `docs/spec.md` (§0–§1, D1–D4, §4, §7), `docs/schema.md`, cấu hình mặc định, notebook và nhật ký hiện tại. Khi ký hiệu trong đề bài gốc khác đặc tả, giao diện theo đặc tả cài đặt: **N(π) = chuyến hoàn thành** là chính; **V(π) = lợi nhuận nền tảng** là phụ.

θ* = argmax N(πθ) trên lưới θ, dưới cùng B và nhiều seed. Đây là ngưỡng tối ưu giá trị chính sách trong simulator; không đồng nhất với ngưỡng nơi uplift cá nhân bằng 0. Khi có interference, không khẳng định có ground truth τ ở cấp cá nhân.

## Những vấn đề đã sửa

| Trước khi rà soát | Cập nhật |
|---|---|
| Nội dung giải thích dài xuất hiện trước KPI; các trang có mức ưu tiên gần như nhau | Phân nhóm điều hướng, tiêu đề theo nhiệm vụ; KPI chính xuất hiện trước biểu đồ; phương pháp trong khối có thể mở |
| Biểu đồ dùng chung trục cho số ô tắt và tỷ lệ ŝ | Tổng quan chỉ vẽ số ô tắt trên trục số ô; phân tích ŝ nằm trong trang cung và vùng |
| Nhãn cố định voucher 20%, slot 15 phút | Tổng quan lấy phần trăm voucher, độ dài slot và thông tin ngân sách từ cấu hình; trang sweep lấy độ dài slot từ defaults |
| Tổng chi voucher dễ bị hiểu là sổ cái đầy đủ | Ghi rõ tổng chi, tổng B qua số kỳ; sổ từng kỳ nằm ở trang voucher; chú thích tiền cam kết và đang giữ |
| Không rõ khác biệt giữa thời điểm hoàn thành theo slot và cửa sổ đặt xe của N | Chú thích rõ hai quy ước trên biểu đồ; KPI tiếp tục lấy nguyên số từ engine |
| useApi giữ dữ liệu cũ khi đổi đường dẫn | Gắn trạng thái fetch với path, không hiển thị summary/config/frame của lượt cũ dưới tên lượt mới |
| Kết quả không liên kết trực tiếp với RQ1–RQ3; gallery dùng tên file | Ba thẻ câu hỏi nghiên cứu liên kết các phần bằng chứng; gallery lọc theo 5 notebook và có tiêu đề tiếng Việt |
| GTE discovery đọc cả all_on/all_off chịu ngân sách và seed không ghép được | Chỉ đọc cặp không ngân sách; ghép seed chung; loại bảng trùng (policy, seed) vì không đủ khóa phân biệt kịch bản |
| SE thiếu bị JavaScript coi thành 0 khi vẽ dải | Không vẽ dải tại điểm thiếu SE; giải thích ± SE không phải CI 95% |
| Bỏ chọn hết sweep lại tự chọn mặc định; chuỗi trống bị parse thành θ=0 | Giữ lựa chọn rỗng; loại token rỗng trước khi parse số |
| Bảng click được nhưng thiếu thao tác bàn phím; một số hàng có key cột trùng | Enter/Space chọn hàng, focus rõ, key cột ổn định, nhãn cột có scope |
| Bố cục form/bản đồ đặt inline số cột, ghi đè responsive | Chuyển thành lớp layout, thu về một cột trên màn hình nhỏ |

Thiết kế dùng sidebar xanh đậm, điểm nhấn teal, thẻ trắng, thang chữ và khoảng cách thống nhất; hỗ trợ sáng/tối/tự động, reduced motion, trạng thái rỗng, lỗi API và thử lại. React/htm và các thư viện vendor hiện tại được giữ; không thêm dependency.

## Đề xuất trình bày khi demo / báo cáo

1. **Tổng quan:** nêu câu hỏi “voucher có tạo thêm chuyến khi thiếu tài xế?”, chọn một lượt, đọc N, tỷ lệ hoàn thành, ETA và chi tiêu.
2. **Bản đồ và cung:** quan sát tài xế, vùng tắt/bật, so ŝ từ snapshot trễ với θ; giải thích cùng θ nhưng khác trạng thái vùng/giờ.
3. **Voucher:** kiểm tra ai nhận, ngưỡng κ, số bị chặn và sổ ngân sách từng kỳ. Nhắc các tỷ lệ hai nhánh là mô tả.
4. **Tìm θ*:** dùng nhiều seed, trình bày N(θ) ± SE và tập θ*. Lượt đơn chỉ là một điểm trên đường này.
5. **Kết quả:** RQ2 đọc bảng policy_table trong cùng thí nghiệm; đối chiếu hình Qini–N. RQ3 đọc GTE và hình interference/confounding.

## Phần cần bổ sung để hoàn chỉnh kết quả nghiên cứu

Các phần dưới là đề xuất nghiên cứu tiếp theo, không phải kết quả đã được dashboard tự tính:

- **RQ1:** bổ sung bảng/đường τ_completed theo trạng thái cung trễ và CI của ngưỡng ước lượng. Sweep N(θ) không thay thế đường này.
- **RQ2:** khi so sánh trực tiếp, giữ cùng ngân sách, cửa sổ, đội xe, cầu và seed. Overlay nhiều sweep trên dashboard phục vụ khám phá; chưa tự kiểm chứng tính tương đương cấu hình.
- **Qini–N:** gallery đã có hình notebook `02_qini_va_n.png`; nên xuất thêm bảng cấu trúc chứa Qini, N, SE, cấu hình và chính sách để lọc/tìm ví dụ đảo thứ hạng ngay trong dashboard.
- **RQ3:** xuất bảng chung về confounding, interference và capacity, kèm định nghĩa từng estimand, đơn vị và khoảng bất định. Hiện các kết quả chi tiết nằm trong hình notebook; không cộng tùy tiện các độ chệch khác đơn vị/thiết kế.
- **Tái lập:** thêm bản xuất báo cáo tổng hợp có config hash, seed, B, cửa sổ, phiên bản dữ liệu; dashboard hiện giữ metadata và bảng kết quả gốc.

Nhãn **“Có dữ liệu”** trên thẻ nghiên cứu chỉ xác nhận artifact tồn tại. Không khẳng định đã trả lời đầy đủ RQ hoặc đạt nghiệm thu. Kết luận định lượng chỉ áp dụng trong mô phỏng này.

## Kiểm chứng

- `tests/test_dashboard.py`: 6 passed, gồm tracer trùng engine, frame/budget nhất quán, geometry, API tiny, API sweep và hồi quy GTE.
- JavaScript: kiểm tra cú pháp tất cả module bằng Node.
- Trình duyệt: kiểm tra đủ 7 trang, tìm kiếm, chọn dòng bằng Enter, lọc hình Confounding, đổi lượt; kiểm tra bố cục desktop và mobile, sáng/tối.
- Không đổi thuật toán mô phỏng, tham số thị trường mặc định hoặc dữ liệu nghiên cứu đã lưu.

Lưu ý chạy test trên máy này: thư mục Temp mặc định của pytest bị WinError 5. Dùng `--basetemp` là một thư mục mới trong `.pytest_cache/` để tránh lỗi quyền và tránh đưa dữ liệu test vào `runs/` (dashboard tự tìm kết quả trong cây `runs/`).
