# Đề tài thực tập: Supply-Aware Promotion Uplift

**Thời lượng:** 5 tuần · **Nhân sự:** 2 intern · **Dữ liệu:** mô phỏng (không dùng dữ liệu công ty)

---

## 1. Bối cảnh

Nền tảng gọi xe phát voucher để kích cầu. Bộ phận vận hành hiện dùng một bảng
quyết định thủ công: khi thấy *"promotion làm request tăng nhưng supply gap và
ETA xấu đi"*, họ thu hẹp promotion ở zone/time đó.

Quy tắc này hợp lý về trực giác nhưng chưa bao giờ được **ước lượng**. Ngưỡng
đặt bằng kinh nghiệm, và không ai biết chi phí của việc đặt sai ngưỡng.

Đề tài này biến quy tắc thủ công đó thành một chính sách học được từ dữ liệu.

## 2. Vấn đề kỹ thuật

Mô hình uplift tiêu chuẩn ước lượng `τ(x)` — hiệu ứng của voucher lên hành vi
của **một** người, giả định hành vi người khác không đổi (SUTVA).

Trong marketplace, giả định đó sai. Khi cung căng:

- voucher vẫn làm tăng **request** (`τ_request > 0`)
- nhưng không tăng **chuyến hoàn thành** (`τ_completed ≈ 0`), vì số chuyến bị
  chặn bởi công suất tài xế
- và còn gây ngoại ứng âm: ETA dài hơn cho **cả người không nhận voucher**

Cơ chế kinh tế có tên trong literature là *wild goose chase*: khi tài xế rảnh
bị dàn quá mỏng, hệ thống buộc phải ghép những cặp ở xa nhau, thời gian đón
kéo dài, tài xế bị chiếm dụng lâu hơn, số tài xế rảnh lại giảm tiếp. Vòng lặp
dương này có thể làm **throughput giảm dù cầu tăng**.

Hệ quả thực tiễn: **Qini/AUUC trên conversion vẫn đẹp trong khi ROI thật âm.**
Đây là thứ đề tài phải chứng minh được bằng số.

## 3. Câu hỏi nghiên cứu

> **RQ1.** Uplift của voucher lên *chuyến hoàn thành* suy giảm như thế nào theo
> độ căng cung của cell (zone, time)?
>
> **RQ2.** Một chính sách phân bổ voucher **có nhận biết trạng thái cung** tốt
> hơn bao nhiêu so với chính sách chỉ dựa trên `τ` cá nhân, dưới cùng ngân sách?
>
> **RQ3.** Sai số của các phương pháp đánh giá: ước lượng từ dữ liệu
> observational lệch bao nhiêu so với ground truth? A/B cấp user lệch bao nhiêu?

## 4. Vì sao dùng dữ liệu mô phỏng

Ngoài lý do bảo mật, mô phỏng là lựa chọn **đúng về mặt khoa học** cho câu hỏi này:

- Biết chính xác giá trị chính sách thật `V(π)` — chạy lại simulator dưới `π`.
  Trên dữ liệu thật điều này bất khả thi.
- Kiểm soát được mức confounding và mức interference để đo sai số của từng
  phương pháp.
- Tách bạch được ba nguồn sai số (confounding, interference, capacity) mà trong
  dữ liệu thật chúng luôn trộn lẫn.

**Lưu ý quan trọng:** vì SUTVA vỡ, **không tồn tại `τ` ground truth ở cấp cá
nhân**. Ground truth duy nhất hợp lệ là giá trị chính sách `V(π)`. Intern phải
hiểu điểm này trước khi viết dòng code đánh giá nào.

## 5. Dữ liệu

Sinh bằng `marketplace_sim.py`. Chạy `--selfcheck` trước để xác nhận hiện tượng
tồn tại, rồi `--dump` để xuất file.

### 5.1 Bảng `riders` (~1M dòng / 30 ngày)

| Nhóm | Cột | Ghi chú |
|---|---|---|
| Khoá | `zone`, `day`, `hour` | cell định danh |
| Covariate | `freq`, `price_sens`, `tenure`, `is_commuter`, `patience` | đặc trưng rider, pre-treatment |
| Treatment | `treat`, `discount_pct` | voucher 20% hoặc không |
| | `is_explore` | 1 nếu thuộc lát randomized 5% |
| Outcome | `request`, `completed` | hai outcome của funnel |
| **Market state (hợp lệ)** | `eta_lag`, `ucr_lag`, `gap_lag`, `util_lag` | trạng thái cùng (zone,hour) **hôm trước** |
| **Market state (CẤM)** | `realized_eta`, `realized_ucr`, `realized_supply_gap` | đo **sau** khi promotion đã tác động |

### 5.2 Bảng `cells` (~6k dòng)

Tổng hợp cấp (zone, day, hour): `requests`, `completed`, `eta`, `ucr`,
`supply_gap`, `utilization`, `supply`.

### 5.3 Cạm bẫy được cài sẵn — intern phải tự phát hiện

**(a) Post-treatment conditioning.** Các cột `realized_*` là hậu quả của chính
treatment. Dùng chúng làm feature là collider conditioning và sẽ cho kết quả
sai. Chỉ được dùng `*_lag`. *Bảng quyết định của vận hành hiện đang phạm đúng
lỗi này* — đó là một phát hiện đáng viết vào báo cáo.

**(b) Confounding từ legacy rule.** Quy tắc phát voucher cũ ưu tiên zone hay
thiếu cung (vì ops nhìn "conversion thấp" và tưởng cần kích cầu). Kết quả:

```
Naive observational:   request 0.225 → 0.274 (+21%)
                     completed 0.150 → 0.152 (+1%)     ← gần như bằng 0
Lát randomized:        request 0.213 → 0.302 (+42%)
                     completed 0.133 → 0.192 (+44%)    ← thực ra rất lớn
```

Phân tích ngây thơ sẽ kết luận "voucher không tác động lên chuyến hoàn thành".
Kết luận đó **sai**, và nó sai vì confounding chứ không vì voucher vô dụng.

**(c) Interference.** Lát randomized cho `+44%`, nhưng GTE khi bật cho toàn hệ
chỉ `+20.4%`. A/B cấp user **thổi phồng hơn gấp đôi**. Đây là lý do không được
dùng thiết kế user-split để quyết định rollout.

**(d) Confounder ẩn.** Simulator có biến `u_latent` ảnh hưởng cả treatment lẫn
outcome nhưng **không xuất ra file**. Dùng để kiểm tra sensitivity analysis có
phát hiện được nó không.

## 6. Phạm vi

### Trong phạm vi
- Treatment **nhị phân** (có/không voucher 20%)
- Outcome: `completed` là chính, `request` là phụ để phân rã funnel
- Ước lượng `τ_completed(x, s_lag)` với `s_lag` là trạng thái cung trễ
- Phân bổ dưới ngân sách cố định, so sánh vài chính sách
- Đánh giá bằng `V(π)` thật từ simulator

### Ngoài phạm vi (đừng đụng vào)
- Nhiều mức voucher / continuous dose
- Incentive phía tài xế, reposition, surge
- Reinforcement learning, quyết định tuần tự
- Điều khiển ngân sách real-time
- Deep learning — LightGBM/sklearn là đủ

> Nếu hết tuần 3 mà mọi thứ chạy tốt, stretch goal là mở rộng sang 3 mức
> voucher. Không bắt đầu bằng cái đó.

## 7. Lộ trình 5 tuần

| Tuần | Nội dung | Đầu ra |
|---|---|---|
| **1** | Đọc simulator, chạy selfcheck, EDA. Tái tạo bảng ba cạm bẫy ở mục 5.3 bằng code của mình. Viết hàm tính `V(π)`. | Notebook EDA + hàm `policy_value` có test |
| **2** | Baseline: DR-learner trên `completed`, **không** dùng market state. Đánh giá bằng Qini. Rồi so với `V(π)` thật. | Chứng minh được Qini đẹp mà `V(π)` kém |
| **3** | Supply-aware: thêm `*_lag` vào effect modifier. Ước lượng `τ(x, s)`. Vẽ đường cong uplift theo `util_lag`. Ước lượng ngưỡng tắt promotion. | Đường cong + ngưỡng có CI |
| **4** | Phân bổ ngân sách: greedy theo `τ̂` vs greedy theo `τ̂(x,s)` vs oracle. So `V(π)` cả ba. Sensitivity: `u_latent` ảnh hưởng ra sao. | Bảng so sánh chính sách |
| **5** | Viết báo cáo, dọn code, seminar 30 phút. | Báo cáo + repo + slides |

**Chia việc:** intern A phụ trách estimation (tuần 2–3), intern B phụ trách
evaluation & allocation (hàm `V(π)`, knapsack, sensitivity). Tuần 1 và 5 làm chung.
Cả hai phải hiểu được toàn bộ pipeline — không được chia thành hai silo.

## 8. Tiêu chí nghiệm thu

Đề tài coi là **thành công** nếu báo cáo trả lời được bằng số:

1. Đường cong `τ_completed` theo độ căng cung, có khoảng tin cậy, và một ngưỡng
   `util*` mà ở trên đó voucher không còn sinh giá trị.
2. Bảng so sánh `V(π)` của ít nhất bốn chính sách: treat-none, treat-all,
   greedy theo `τ̂` không biết cung, greedy theo `τ̂(x,s)`. Dưới cùng ngân sách.
3. **Một ví dụ cụ thể** cho thấy Qini của chính sách B cao hơn chính sách C
   nhưng `V(π)` lại thấp hơn. Đây là kết quả quan trọng nhất của đề tài.
4. Định lượng ba nguồn sai số: confounding, interference, capacity — mỗi cái
   đóng góp bao nhiêu vào khoảng cách giữa ước lượng naive và ground truth.

Đề tài coi là **thất bại** nếu chỉ dừng ở "đã train được model uplift, Qini =
0.xx". Con số Qini một mình không trả lời câu hỏi nào trong mục 3.

## 9. Tài liệu đọc

Phân tầng theo thứ tự. **Không đọc hết** — mỗi mục có ghi rõ đọc phần nào.
Nguyên tắc: đọc abstract + introduction + phần được chỉ định, bỏ qua phần
chứng minh và phần thực nghiệm trừ khi có lý do cụ thể.

### Tầng 0 — đọc ngay buổi đầu (nửa ngày)

**Blake & Coey (2014), "Why Marketplace Experimentation is Harder than It
Seems: The Role of Test-Control Interference", EC '14.**

Đây là bài duy nhất bắt buộc đọc kỹ trước khi làm bất cứ thứ gì. Lý do: nó
phân tích đúng một **chiến dịch email marketing của eBay** — tức là đúng loại
bài toán promotion — và cho thấy bỏ qua interference làm **ước lượng hiệu quả
chiến dịch phóng đại khoảng gấp đôi**. Quan trọng hơn, họ giải thích cơ chế
bằng khung cung–cầu đơn giản: độ chệch lớn hơn khi cung **kém co giãn**, và
mang dấu dương khi cầu co giãn.

Đó chính xác là cơ chế trong simulator của đề tài. Đọc xong bài này thì toàn
bộ phần còn lại của đề tài trở nên dễ hiểu.

### Tầng 1 — nền tảng uplift (tuần 1)

**Künzel, Sekhon, Bickel & Yu (2019), "Metalearners for estimating
heterogeneous treatment effects using machine learning", PNAS 116:4156–4165.**
S/T/X-learner. Ngắn, rõ, là nền cho mọi thứ trong CausalML. Đọc toàn bộ.

**Gutierrez & Gérardy (2017), "Causal Inference and Uplift Modelling: A Review
of the Literature", PMLR 67:1–13.** Bài review đầu tiên nối uplift modeling với
HTE. Dễ đọc, đúng tầm intern. Đọc toàn bộ (13 trang).

**Zhang, Li & Liu (2021), "A Unified Survey of Treatment Effect Heterogeneity
Modelling and Uplift Modelling", ACM Computing Surveys 54(8), arXiv 2007.12769.**
Dùng làm **tự điển tra cứu**, không đọc từ đầu đến cuối. Giá trị chính là nó
thống nhất ký hiệu giữa hai cộng đồng (uplift và HTE) vốn dùng từ khác nhau cho
cùng một thứ — intern sẽ gặp đúng vấn đề này khi đọc các bài khác.

**Chamandy (2016), "Experimentation in a Ridesharing Marketplace", Lyft
Engineering blog.** Ba phần, không phải paper. Viết bởi người vận hành thật,
đúng bối cảnh gọi xe. Đọc để có trực giác trước khi vào phần lý thuyết.

> Nếu intern chưa từng học potential outcomes: Hernán & Robins, *Causal
> Inference: What If*, chương 1–3. Bản PDF miễn phí. Chỉ đọc nếu thiếu nền,
> đừng bắt cả hai đọc nếu đã có.

### Tầng 2 — cơ chế thị trường (cuối tuần 1)

**Castillo, Knoepfle & Weyl (2024), "Matching and Pricing in Ride Hailing: Wild
Goose Chases and How to Solve Them", Management Science.**
Chỉ đọc phần mô hình cơ chế. Bỏ qua toàn bộ phần ước lượng cấu trúc và welfare —
đó là kinh tế lượng nặng, không cần cho đề tài. Điều cần rút ra: khi giá quá
thấp so với cầu, **mọi trạng thái cân bằng đều là WGC** dưới giao thức
first-dispatch; tài xế rảnh bị dàn mỏng, buộc ghép những cặp ở xa nhau.

**Yang & Yang (2011), "Equilibrium properties of taxi markets with search
frictions", TR-B 45(4):696–713.** Chỉ đọc mục về hàm Cobb-Douglas. Đây là nền
toán học của "hàm throughput" trong panel A của hình minh hoạ.

> Cảnh báo cần biết: nghiên cứu hiệu chỉnh cho thấy Cobb-Douglas phù hợp với
> thị trường cân bằng và thừa cung, nhưng **mất hiệu lực khi cung bắt đầu thiếu
> hụt** — đúng vùng đề tài quan tâm. Đây là lý do đề tài dùng mô phỏng thay vì
> dạng hàm đóng.

### Tầng 3 — thiết kế thí nghiệm (tuần 2)

**Bojinov, Simchi-Levi & Zhao (2023), "Design and Analysis of Switchback
Experiments", Management Science.** Đọc phần đặt vấn đề và thiết kế. Bỏ phần
optimal design theory.

**Holtz, Lobel, Liskovich & Aral, cluster randomization trên Airbnb,
Management Science.** Đọc để nhớ một con số: độ chệch do interference **có thể
lớn bằng chính GTE**.

### Tầng 4 — công cụ (tuần 2, đọc song song khi code)

- Tài liệu CausalML: `BaseDRRegressor`, module `metrics`, module
  `feature_selection`.
- **Zhao & Harinen (2019), "Uplift Modeling for Multiple Treatments with Cost
  Optimization", DSAA.** Nguồn chuẩn cho Qini và phần cost optimization.

### Không đọc trong 5 tuần

Nói rõ để khỏi mất thời gian: DESCN, EFIN, các bài deep uplift, lý thuyết Double
Machine Learning (Chernozhukov 2018), marginal sensitivity model, partial
identification, decision-focused learning. Tất cả đều liên quan tới bài toán
lớn hơn nhưng **không cần** cho 5 tuần này, và đọc chúng sẽ làm intern lạc
hướng khỏi tiêu chí nghiệm thu ở mục 8.

### Cách đọc

Mỗi bài, viết ba câu vào một file chung: (1) bài này khẳng định điều gì,
(2) giả định nào bị phá vỡ nếu áp vào bài toán của ta, (3) một con số đáng nhớ.
Cuối tuần 1 hai intern trình bày chéo — mỗi người tóm tắt bài của người kia.
Đây là cách nhanh nhất để phát hiện ai đọc mà chưa hiểu.

## 10. Rủi ro đã lường trước

| Rủi ro | Xử lý |
|---|---|
| Intern sa đà vào tuning model | Nhắc lại tiêu chí 3: câu chuyện Qini-vs-`V(π)` mới là sản phẩm |
| Chạy simulator quá chậm | Dùng `--days 15` khi phát triển, 30–60 ngày chỉ cho kết quả cuối |
| Dùng nhầm `realized_*` | Code review tuần 2, grep tên cột |
| Kết luận quá mạnh từ mô phỏng | Mọi phát biểu phải kèm "trong mô phỏng này"; đừng ngoại suy ra con số cho hệ thật |

---

## Phụ lục: bắt đầu

```bash
python marketplace_sim.py --selfcheck --days 10     # xác nhận hiện tượng
python marketplace_sim.py --dump data/sim --days 30 # xuất dữ liệu
```

`SimConfig` có toàn bộ tham số. Đổi `base_supply` để dịch chuyển phân phối độ
căng cung; đổi `explore_frac` để xem cần bao nhiêu randomization mới cứu được
ước lượng. Hai thí nghiệm đó đáng làm trong tuần 4 nếu còn thời gian.