# Phương pháp luận simulator gọi xe — báo cáo phiên bản 1

Supply-Aware Promotion Impact Framework · Nhóm: Phan Văn Tình, Nguyễn Huy Hoàng · Mentor: Nguyễn Bảo Long

---

## 0. Về tài liệu này

| | |
|---|---|
| Phiên bản | 1, ngày 05/10/2026, viết sau Sprint 4 |
| Trạng thái code | `develop1` ở `8467f83` (đã gồm H-21…H-23 của Hoàng) cộng H-21, `ring1` (H-25) và S5 (chưa commit); `config/default.yaml` đã hiệu chỉnh (H-17), `config_hash = 92b7d13adc39` (trước khi thêm hai khóa `kappa_max_iter` và `scope`: `cb27f5348011`; hành vi mặc định không đổi) |
| Người đọc | nhóm và mentor; đọc để hiểu vì sao simulator được xây như vậy và vì sao tin được con số nó cho ra |
| Quan hệ với tài liệu khác | `docs/spec.md` là nguồn sự thật cho code; báo cáo thiết kế `docs/Simulation_design_fix.pdf` nói ý đồ. Tài liệu này giải thích nền tảng toán, kinh tế và thống kê đằng sau từng lựa chọn, gom bằng chứng kiểm định, và liệt kê chỗ phương pháp còn yếu. Khi lệch nhau: spec và `docs/decisions.md` thắng. |

Cách đọc:
- Chưa quen suy luận nhân quả trên thị trường hai phía: đọc §1 và §2 trước.
- Muốn biết simulator làm gì: §3 đến §6.
- Muốn biết dùng simulator ra đáp án thế nào và vì sao tin được: §7 đến §9.
- Muốn biết phương pháp còn yếu ở đâu: §10.

Quy ước số liệu: con số **đo được** chép từ `docs/log.md`, `docs/decisions.md`, `docs/datasets.md` (ghi rõ nguồn). Con số **minh họa** tính trực tiếp từ `default.yaml` qua `sim.population.build_world`, dùng để có cảm giác về độ lớn, không phải kết quả.

---

## 1. Bài toán và đại lượng cần đo

### 1.1 Bối cảnh

Nền tảng gọi xe phát voucher (20% giá) để kích cầu theo vùng và khung giờ. Bộ phận vận hành dùng một quy tắc kinh nghiệm: khi thấy khuyến mãi làm request tăng nhưng thiếu xe và ETA xấu đi thì thu hẹp khuyến mãi ở vùng–giờ đó. Ngưỡng đặt theo cảm giác, chưa ai đo chi phí khi đặt sai.

Đề tài có hai mục tiêu:
1. Đo giá trị ròng của khuyến mãi theo vùng và giờ, có tính phần lan sang người khác và ô khác (spillover).
2. Tìm ngưỡng căng cung θ\* để tắt khuyến mãi, thay cho ngưỡng đặt theo kinh nghiệm.

### 1.2 Vì sao mô hình uplift tiêu chuẩn trả lời sai

Mô hình uplift ước lượng $\tau(x) = \mathbb E[Y(1) - Y(0) \mid X = x]$ cho từng người, với giả định ngầm: việc người khác có voucher hay không không ảnh hưởng tới kết cục của người này (SUTVA, §2.1). Trên thị trường gọi xe giả định này sai, và có thêm hai vấn đề đo lường:

| Cơ chế | Diễn ra thế nào | Hệ quả cho đo lường |
|---|---|---|
| Tranh chấp cung (interference) | Mọi rider dùng chung một đội xe hữu hạn. Một đơn được ghép làm bớt xe cho đơn khác, kể cả ở ô kề. | So người có voucher với người không có trong cùng thị trường sẽ phóng đại hiệu ứng. |
| Giới hạn công suất | Khi thiếu xe, voucher vẫn tăng request nhưng request không thành chuyến (bỏ chờ, hủy). | Uplift trên request khác uplift trên chuyến hoàn thành. |
| Wild goose chase (WGC) | Xe rảnh thưa thì phải ghép cặp ở xa; mỗi chuyến chiếm xe lâu hơn; số xe rảnh lại giảm tiếp. | Số chuyến hoàn thành có thể **giảm** khi cầu tăng (§2.2). |
| Gây nhiễu (confounding) | Dữ liệu lịch sử sinh ra từ một quy tắc nhắm có chủ đích theo trạng thái thị trường và theo đặc điểm rider. | So thô nhóm có và không có voucher lẫn hiệu ứng chọn (§2.6). |

Hệ quả thực tiễn mà đề tài phải chứng minh bằng số: **Qini/AUUC trên conversion có thể đẹp trong khi giá trị chính sách thật kém.**

### 1.3 Câu hỏi nghiên cứu

- **RQ1.** Uplift của voucher lên *chuyến hoàn thành* suy giảm thế nào theo độ căng cung của (ô, khung giờ)?
- **RQ2.** Chính sách phân bổ voucher có nhận biết trạng thái cung tốt hơn bao nhiêu so với chính sách chỉ dựa trên τ cá nhân, dưới cùng ngân sách?
- **RQ3.** Ước lượng từ dữ liệu quan sát lệch bao nhiêu so với ground truth? A/B theo rider lệch bao nhiêu?

### 1.4 Vì sao phải dùng mô phỏng

Trên dữ liệu thật không bao giờ quan sát được cùng một (ô, slot) dưới cả hai trạng thái bật và tắt khuyến mãi, nên không có đáp án để kiểm tra phương pháp. Simulator cho phép:
- **Chạy lại cùng một thế giới** dưới nhiều chính sách, với cùng số ngẫu nhiên (§6). Hiệu giữa hai lượt chạy là phản thực đúng nghĩa.
- **Kiểm soát** mức gây nhiễu và mức tranh chấp cung, để đo sai số của từng phương pháp.
- **Tách** ba nguồn sai số (gây nhiễu, tranh chấp cung, công suất), vốn luôn trộn lẫn trong dữ liệu thật.

Đổi lại, mọi kết luận chỉ đúng "trong mô phỏng này"; con số tuyệt đối (USD, số xe) là quy ước (§10).

> **Nguyên tắc quan trọng nhất.** Vì SUTVA vỡ, **không tồn tại "τ thật" của từng cá nhân**. Đáp án duy nhất hợp lệ là giá trị của một chính sách khi áp cho cả hệ thống. Mọi đánh giá trong đề tài quy về N(π).

### 1.5 Đại lượng mục tiêu

Gọi $C(\pi)$ là tập chuyến hoàn thành của các đơn đặt trong cửa sổ đánh giá khi áp chính sách voucher $\pi$. Chuyến $j$ có giá gốc $p_j$, voucher $v_j$, tiền trả tài xế $w_j$:

$$
N(\pi) = \mathbb E\,\lvert C(\pi)\rvert, \qquad
V(\pi) = \mathbb E \sum_{j \in C(\pi)} (p_j - v_j - w_j),
$$

với ràng buộc ngân sách cho từng kỳ ngân sách $d$ (một ngày, §3.2):

$$
\sum_{j \in C(\pi),\ j \in d} v_j \;\le\; B .
$$

Kỳ vọng lấy trên seed của lượt chạy (ngẫu nhiên của cầu và hành vi) với thế giới cố định (§6.5).

**Vì sao N là chỉ tiêu chính, V là phụ (D1).** Với hoa hồng $c = 0{,}24$ và voucher $r = 0{,}20$ giá gốc, một chuyến không voucher đem về cho nền tảng $c\,p$; chuyến có voucher chỉ còn $(c - r)\,p$. Phát voucher cho một nhóm session có tỷ lệ hoàn thành $q_0$ (không voucher) và $q_1$ (có voucher) chỉ làm V tăng khi

$$
q_1 (c - r) \;\ge\; q_0\, c
\quad\Longleftrightarrow\quad
\frac{q_1}{q_0} \;\ge\; \frac{c}{c - r} = \frac{0{,}24}{0{,}04} = 6 .
$$

Voucher phải làm số chuyến tăng **gấp 6 lần** mới có lời ngắn hạn, trong khi hiệu ứng toàn hệ đo được chỉ khoảng +35% (GTE, §9). Theo V, ngưỡng tối ưu luôn là "không bật". Câu hỏi chỉ có nghĩa khi chi phí voucher bị cố định bằng B và các chính sách so nhau bằng số chuyến. Lượt GTE xác nhận: V giảm từ 15.661,5 xuống 3.732,0 USD/ngày khi bật toàn bộ (`datasets.md`, B7a).

**Ngưỡng đúng (D2).** Gọi $\pi_\theta$ là chính sách tắt khuyến mãi ở các ô có slack dự báo dưới θ và dùng ngân sách cho các ô còn lại (§5.4):

$$
\theta^* = \arg\max_{\theta \in \Theta} N(\pi_\theta).
$$

Ba điểm cần nhớ:
- $\pi_\theta$ áp cho **mọi ô cùng lúc**, N tính trên **toàn hệ**. Vì vậy $N(\pi_\theta)$ đã gồm thiệt hại lan sang ô kề và slot sau, và lợi ích của việc dồn ngân sách sang ô dư cung.
- Định nghĩa không giả định hiệu ứng đơn điệu theo độ căng; tính đơn điệu được kiểm riêng (A4, §8.2).
- Ngưỡng $\hat\theta$ ước lượng từ dữ liệu được chấm bằng **regret** $N(\pi_{\theta^*}) - N(\pi_{\hat\theta})$, không bằng $\lvert \hat\theta - \theta^* \rvert$ (T-31, §2.9).

---

## 2. Nền tảng lý thuyết

Phần này gom các kiến thức mà simulator dựa vào. Mỗi mục kết thúc bằng chỗ kiến thức đó xuất hiện trong simulator.

### 2.1 Kết cục tiềm năng khi SUTVA vỡ

Gọi $Z = (Z_1, \dots, Z_n) \in \{0,1\}^n$ là vector gán voucher cho mọi session, $Y_i(Z)$ là kết cục (hoàn thành chuyến hay không) của session $i$ dưới cách gán đó.

- **SUTVA** nói $Y_i(Z) = Y_i(Z_i)$: kết cục của $i$ chỉ phụ thuộc voucher của chính $i$. Khi đó $\tau_i = Y_i(1) - Y_i(0)$ có nghĩa, và mô hình uplift ước lượng $\mathbb E[\tau_i \mid X_i]$.
- **Trên thị trường gọi xe** $Y_i$ phụ thuộc $Z_{-i}$ qua số xe rảnh. "Hiệu ứng lên $i$" là $Y_i(1, Z_{-i}) - Y_i(0, Z_{-i})$: nó đổi theo cách gán cho người khác. Không có một con số $\tau_i$ duy nhất, nên không có ground truth cấp cá nhân.

**Ví dụ hai rider, một xe.** Một ô có đúng một xe rảnh, hai rider A và B cùng mở app. Có voucher thì rider chắc chắn đặt; không voucher thì đặt với xác suất $q$. Cả hai cùng đặt thì mỗi người lấy được xe với xác suất 1/2.

| Cách gán | Số chuyến kỳ vọng |
|---|---|
| Không ai có voucher | $1 - (1-q)^2$ |
| Cả hai có voucher | $1$ |
| **Hiệu ứng toàn hệ (GTE)** | $(1-q)^2$ |
| A/B: A có, B không | A hoàn thành $1 - q/2$; B hoàn thành $q/2$; hiệu $1 - q$ mỗi người, quy ra hai người là $2(1-q)$ |

Với $q = 0{,}5$: GTE = 0,25 chuyến, A/B báo 1 chuyến, tức **phóng đại 4 lần**. Người có voucher "lấy" xe của người không có, và thí nghiệm đếm phần lấy được đó là hiệu ứng. Chênh lệch càng lớn khi cung càng kém co giãn (ở đây cung cố định bằng 1 xe), đúng kết luận của Blake & Coey (2014).

**Các đại lượng có nghĩa trong simulator:**
- Giá trị chính sách $N(\pi)$, $V(\pi)$ (§1.5).
- **GTE** (global treatment effect) $= N(\text{all\_on}) - N(\text{all\_off})$, cả hai **không** áp ngân sách (D10).
- **Độ chệch của một thiết kế thí nghiệm** $d$: $\text{Bias}_d = \hat\tau_d - \text{GTE}$, cùng chỉ số (chuyến hoàn thành/ngày), cùng cửa sổ, cùng cách chuẩn hóa (Johari et al. 2022, 2026).
- `direct_request_effect_fixed_market` $= P(\text{đặt} \mid \text{có voucher}) - P(\text{đặt} \mid \text{không})$ tính **trong cùng bối cảnh** của session (cùng giá, cùng ETA báo). Đây là hiệu ứng trực tiếp lên request khi giữ thị trường cố định, chỉ để kiểm tra mô hình hành vi; **không** dùng để chấm mô hình uplift. Cột này nằm trong `hidden/`.

Trong simulator: `engine.run` tính N, V; mode `gte` tính GTE (§7).

### 2.2 Vận hành đội xe: định luật Little, slack và wild goose chase

Mỗi tài xế online ở một trong bốn trạng thái: rảnh ($I$), đang đi đón ($E$), đang chở ($O$), đang điều chuyển ($R$), với $L = I + E + O + R$.

Ở trạng thái dừng, gọi $\mu$ là số chuyến được ghép mỗi phút, $\bar\eta$ thời gian đón trung bình, $\bar\tau$ thời gian chở trung bình. Định luật Little (số đang ở trong một giai đoạn = tốc độ vào × thời gian ở lại) cho $E = \mu \bar\eta$ và $O = \mu \bar\tau$, nên

$$
\mu = \frac{L - I - R}{\bar\eta(I) + \bar\tau},
\qquad
\text{slack} = \frac{I}{E} = \frac{I}{\mu\,\bar\eta}.
$$

Thời gian đón $\bar\eta$ giảm khi mật độ xe rảnh tăng (§2.3). Xét hàm throughput $f(I) = (L - I)/(\bar\eta(I) + \bar\tau)$:
- $f(L) = 0$: không ai bận thì không có chuyến.
- Khi $I \to 0$, $\bar\eta(I)$ tăng mạnh (phải lấy xe ở xa), nên $f$ giảm.
- Do đó $f$ có cực đại tại một $I^*$ ở giữa.

Cầu tăng đẩy $I$ xuống. Khi $I$ còn lớn hơn $I^*$, cầu tăng làm số chuyến tăng. Khi $I$ đã nhỏ hơn $I^*$, thêm cầu làm **giảm** số chuyến: xe dành thời gian chạy tới những điểm đón xa thay vì chở khách. Đây là **wild goose chase** (Castillo, Knoepfle & Weyl 2025), và đường cung của thị trường "cong ngược". Castillo et al. chỉ ra WGC xuất hiện khi slack xuống dưới khoảng 0,25–0,45, và tỷ lệ hủy tăng mạnh gần ngưỡng đó. Hủy trong lúc đi đón làm tình hình xấu thêm, vì xe mất phần thời gian đã chạy.

Trong simulator:
- Thời gian đón bị chặn trên bởi đường kính lưới (xa nhất 3 vành, 22,5 phút lúc cao điểm, §4.1) và rider bỏ chờ sau `max_wait`. Vì vậy throughput không sụp về 0 mà giảm rồi đi ngang. A1 đo được đỉnh 781,2 chuyến/giờ ở `demand_scale` 3,25, rồi giảm còn 659,8 (= 0,845 × đỉnh) ở mức 4,0, với slack ≤ 0,095 ở vùng giảm (H-17, §8.2).
- Ý nghĩa cho khuyến mãi: voucher là một cú tăng cầu cục bộ. Ở ô đã vào vùng WGC, voucher làm giảm số chuyến; ở ô gần vùng đó, phần request tăng thêm phần lớn thành bỏ chờ hoặc hủy. Đó là lý do cần một ngưỡng để tắt.
- Ba quy tắc cứng giữ cho hiện tượng không bị mất: không giảm `max_pickup_eta_min`, không giới hạn tìm xe ở vành 1, không bỏ hủy trong lúc đi đón (CLAUDE.md, quy tắc 6). Giới hạn bán kính đón chính là cách Castillo et al. đề xuất để *loại bỏ* WGC, nên dùng nó trong simulator sẽ xóa đúng thứ cần đo.

Trong code: `monitor.py` (slack), `matching.py` (ghép xe gần nhất), `runner.py` mode `throughput_curve`.

### 2.3 Khoảng cách tới xe gần nhất

Nếu các xe rảnh nằm như một quá trình điểm Poisson với mật độ $\rho$ xe/km² trên mặt phẳng, khoảng cách $D$ từ một điểm bất kỳ tới xe gần nhất thỏa

$$
P(D > r) = e^{-\rho \pi r^2}
\quad\Rightarrow\quad
\mathbb E[D] = \int_0^\infty e^{-\rho\pi r^2}\,dr = \frac{1}{2\sqrt{\rho}} .
$$

Với $I$ xe rảnh trong một ô diện tích $A$, $\rho = I/A$ nên $\mathbb E[D] = 0{,}5\sqrt{A/I}$. Đây là nguồn của `nn_const = 0,5` và `eta_gamma = 0,5` trong công thức ETA trong ô (§4.1). Báo cáo thiết kế để $\gamma$ là tham số để có thể kiểm độ nhạy (Castillo et al. dùng dạng $c\,(A/I)^\gamma$).

Giả định ngầm: các xe rảnh và rider phân bố đều trong ô; mọi xe rảnh trong cùng ô coi như tương đương (cùng ETA), nên chọn xe nào trong ô chỉ là phá hòa.

### 2.4 Mô hình lựa chọn nhị phân logit

Rider $i$ trong session $s$ đặt xe khi lợi ích của việc đặt lớn hơn không đặt. Nếu phần ngẫu nhiên của chênh lệch lợi ích có phân phối logistic thì

$$
P_{is} = \sigma(\ell_{is}), \qquad
\ell_{is} = \alpha_i + \beta^{p}_i (p_s - v_s) + \beta^{\eta}_i \eta_s + \delta_i \mathbf 1[v_s > 0],
\qquad \sigma(x) = \frac{1}{1 + e^{-x}},
$$

với $\beta^p_i, \beta^\eta_i < 0$ là độ nhạy với giá thực trả và ETA báo, $\delta_i$ là phản ứng riêng với việc *có* khuyến mãi (ngoài phần giảm giá). Dạng này theo Johari et al. (2026).

Voucher dịch logit một lượng $\Delta_{is} = -\beta^p_i v_s + \delta_i > 0$, **không phụ thuộc ETA**. Nhưng hiệu ứng lên xác suất thì có:

$$
P^{(1)} - P^{(0)} = \sigma(\ell + \Delta) - \sigma(\ell) \;\approx\; \sigma(\ell)\,(1 - \sigma(\ell))\,\Delta .
$$

Ở vùng $P < 0{,}5$ (xác suất đặt khoảng 15%), $\sigma(1-\sigma)$ tăng theo $\ell$. ETA báo dài hơn làm $\ell$ nhỏ hơn nên **số request tăng thêm nhỏ hơn**, dù tỷ lệ tương đối có thể không giảm. Ví dụ minh họa: session có $P^{(0)} = 15\%$ ở ETA 4 phút, $\Delta = 0{,}70$ (Δ của rider có hệ số bằng trung bình quần thể: $\beta^p \approx -0{,}113$/USD, voucher 3,8 USD, $\delta \approx 0{,}274$):

| ETA báo | $P^{(0)}$ | $P^{(1)}$ | Request tăng thêm |
|---|---|---|---|
| 4 phút | 15,0% | 26,2% | +11,2 điểm (+75%) |
| 12 phút ($\beta^\eta \approx -0{,}10$/phút) | 7,3% | 13,8% | +6,4 điểm (+87%) |

Như vậy độ căng cung làm giảm hiệu quả voucher qua **ba kênh** mà simulator mô hình riêng rẽ:
1. **Kênh hành vi:** ETA báo dài làm ít request tăng thêm (M4).
2. **Kênh công suất:** request tăng thêm không thành chuyến vì bỏ chờ, hủy (M5, M7).
3. **Kênh ngoại ứng:** request tăng thêm làm ETA của mọi người khác dài ra, và trong vùng WGC làm giảm số chuyến (§2.2).

Hệ số khác nhau giữa các rider (§4.2), nên uplift khác nhau và việc xếp hạng rider có nghĩa. Con số hiệu chỉnh trên toàn quần thể, đo trên session ở ô dư cung: P(đặt) không voucher 15,35%, request tăng +50,6% khi có voucher (H-17). Bảng trên chỉ minh họa cho một rider; con số của quần thể khác vì hệ số và xác suất nền khác nhau giữa các rider, và nó là tỷ số của hai trung bình chứ không phải trung bình của các tỷ số.

### 2.5 Hủy đơn: hazard và ngưỡng rút sẵn

Thời gian tới khi khách hủy là một biến ngẫu nhiên có hazard $h$ (xác suất hủy mỗi phút, với điều kiện chưa hủy). Hàm sống $S(t) = e^{-H(t)}$ với $H(t) = \int_0^t h$. Cách rút mẫu:

$$
e \sim \text{Exp}(1) \text{ rút sẵn cho mỗi session}, \qquad \text{hủy ở thời điểm đầu tiên } H(t) \ge e .
$$

Cách này cho đúng phân phối, vì $P(\text{hủy trước } t) = P(e \le H(t)) = 1 - e^{-H(t)}$. Lợi ích chính là **CRN**: ngưỡng $e$ ("độ kiên nhẫn") của một session giống nhau ở mọi chính sách; chính sách chỉ đổi $H$ qua ETA đón. Nếu session hủy dưới chính sách 1 và có ETA dài hơn dưới chính sách 2 thì nó cũng hủy dưới chính sách 2. Hai lượt chạy được ghép cặp chặt, phương sai của hiệu nhỏ (§2.9).

Mô hình trong simulator (M7):

$$
h(\eta) = b + k \max(0, \eta - \eta_{\text{free}}),
\qquad
P(\text{hủy trước khi xe tới}) = 1 - e^{-h(\eta)\,\eta},
$$

với $b = 0{,}005$/phút, $k = 0{,}004$/phút², $\eta_{\text{free}} = 3$ phút (`[assume]`):

| ETA đón | 3 phút | 5 phút | 10 phút | 15 phút |
|---|---|---|---|---|
| P(hủy trước khi xe tới) | 1,5% | 6,3% | 28,1% | 54,8% |

Rà soát ngày 02/10 đo được tỷ lệ hủy theo ETA đón từ 0,7% (dưới 3 phút) đến 61,1% (từ 12 phút), khớp dạng này.

**Bỏ chờ** (trước khi được ghép) dùng một ngưỡng cố định theo rider: $\text{max\_wait}_i \sim \text{LogNormal}(\mu, 0{,}5)$ với mode 5 phút (Castillo et al. 2025), tức $\mu = \ln 5 + 0{,}5^2$; trung vị 6,42 phút, trung bình 7,28 phút.

### 2.6 Gây nhiễu, propensity và lát ngẫu nhiên hóa

Trên dữ liệu quan sát, việc nhận voucher $Z$ phụ thuộc đặc trưng rider $X$, trạng thái thị trường $S$ và có thể cả biến ẩn $U$. Nếu $U$ ảnh hưởng cả $Z$ lẫn kết cục $Y$ thì giả định không gây nhiễu ($Y(z) \perp Z \mid X, S$) sai, và hiệu so thô $\mathbb E[Y \mid Z=1] - \mathbb E[Y \mid Z=0]$ không phải hiệu ứng.

Các công cụ chuẩn:
- **Propensity** $e(x, s) = P(Z = 1 \mid X = x, S = s)$. Nếu biết $e$ và không có gây nhiễu ẩn, ước lượng IPW
  $$\hat\tau_{\text{IPW}} = \frac1n \sum_i \left( \frac{Z_i Y_i}{e_i} - \frac{(1 - Z_i) Y_i}{1 - e_i} \right)$$
  không chệch. Ước lượng doubly robust (DR, AIPW) kết hợp mô hình kết cục $\hat m_z$ với propensity và vẫn đúng nếu một trong hai đúng:
  $$\hat\tau_{\text{DR}} = \frac1n \sum_i \left( \hat m_1(X_i) - \hat m_0(X_i) + \frac{Z_i (Y_i - \hat m_1(X_i))}{e_i} - \frac{(1 - Z_i)(Y_i - \hat m_0(X_i))}{1 - e_i} \right).$$
- **Overlap:** cần $0 < e < 1$ ở mọi vùng của $(x, s)$; nếu một mức căng cung luôn bật thì không học được gì về trạng thái tắt ở đó (Kennedy 2023).
- **Lát ngẫu nhiên hóa:** một phần session được gán bằng đồng xu với xác suất biết trước; trên lát này so thô là không chệch.
- **Không điều kiện hóa lên biến sau can thiệp.** Slack của chính slot hiện tại là hệ quả của voucher trong slot đó. Dùng nó làm đặc trưng là điều kiện hóa lên collider. Chỉ được dùng giá trị trễ (`slack_lag_slot`, `slack_lag_day`).

Chính sách cũ trong simulator (`LegacyPolicy`, §5.2) được thiết kế để tạo đủ ba thứ: gây nhiễu qua biến ẩn `u_latent`, overlap ở cấp ô nhờ đồng xu ε, và một lát explore 5% sạch. Biến ẩn `u_latent` làm tăng cả xu hướng đặt nền $\alpha$ (tương quan 0,63 trong quần thể) lẫn phản ứng voucher $\delta$ (tương quan 0,59) **và** xác suất được nhắm voucher. Kết quả đo trên `legacy_28d`: hiệu ứng lên tỷ lệ hoàn thành mỗi session so thô là +0,1018, trên lát explore là +0,0695 (SE 0,0039): so thô **phóng đại khoảng 46%** (H4.2 trong log).

Lưu ý về chiều chệch: ví dụ trong `docs/problem_statement.md` §5.3(b) cho chệch **xuống** (quy tắc cũ ưu tiên vùng thiếu cung). Simulator làm theo mô tả ở §1 của cùng tài liệu (vận hành *thu hẹp* khuyến mãi khi thiếu xe), nên quy tắc cũ bật ở ô dư cung và nhắm rider có `u_latent` cao: chệch **lên**. Chiều chệch là một lựa chọn thiết kế; báo cáo cuối phải nói rõ.

### 2.7 Thiết kế thí nghiệm trên thị trường hai phía

| Thiết kế | Đơn vị ngẫu nhiên hóa | Tranh chấp cung giữa hai nhánh | Chệch kỳ vọng |
|---|---|---|---|
| A/B theo rider | rider (cố định cả lượt chạy) | trong cùng ô, cùng lúc | lớn nhất |
| Switchback cụm 1 ô | (ô, block 60 phút) | qua ranh giới ô (M5 lấy xe từ vành) | lớn |
| Switchback cụm 7 ô | (cụm ô + vành 1, block) | chỉ qua ranh giới cụm | nhỏ hơn |
| Switchback toàn hệ | (toàn hệ, block) | chỉ qua thời gian (carryover) | nhỏ nhất |

- **Cụm 7 ô:** tâm cụm là ô có $(q + 5r) \bmod 7 = 0$. Trên lưới vô hạn, quy tắc này lát kín mặt phẳng bằng các "hoa" 7 ô và mỗi ô cách đúng một tâm không quá 1. Lưới torus 37 ô không chia hết cho 7, nên kích thước cụm là [3, 3, 4, 6, 7, 7, 7] (D11).
- **Carryover:** xe bận kéo dài qua ranh giới block, nên trạng thái đầu block chịu ảnh hưởng của block trước. Xử lý bằng **burn-in**: bỏ 15 phút đầu mỗi block khi ước lượng (Hu & Wager 2022). Block 60 phút theo Johari et al. (2026); Bojinov et al. (2023) cho khung thiết kế và phân tích switchback.
- **Suy luận:** session trong cùng (cụm, block) cùng nhánh và cùng thị trường, nên khoảng tin cậy phải bootstrap theo đơn vị (cụm, block), không theo session (H-19a).
- **Biến phân nhóm trong switchback:** `slack_lag_slot` bên trong một block đã bị voucher của chính block đó kéo xuống, nên tỷ lệ session ở nhánh bật lệch khỏi 50% giữa các nhóm (35,9% đến 58,2%). Phân nhóm phải dùng slack **trước khi block bắt đầu** (H-19b).
- Thí nghiệm và GTE **không** áp ngân sách (D10): ngân sách chung làm hai nhánh tranh nhau qua sổ ngân sách, thêm một kênh tranh chấp nữa.

Holtz et al. (2025) ghi nhận độ chệch do tranh chấp có thể lớn bằng chính GTE; simulator đo được thứ tự đúng như bảng (§9).

### 2.8 Phân bổ voucher dưới ngân sách

Nếu mỗi session $i$ có một hiệu ứng $\tau_i$ và chi phí kỳ vọng $c_i$, bài toán chọn tập phát voucher là bài toán cái túi:

$$
\max_{a \in \{0,1\}^n} \sum_i \tau_i a_i \quad \text{với} \quad \sum_i c_i a_i \le B
\qquad\leadsto\qquad
a_i = \mathbf 1\!\left[ \frac{\tau_i}{c_i} \ge \lambda \right],
$$

trong đó nghiệm của bản nới lỏng tuyến tính là ngưỡng trên **hiệu ứng mỗi USD**, và $\lambda$ là giá bóng của ngân sách (Zhao & Harinen 2019). Hai điểm cụ thể của simulator:
- **Chi phí chỉ phát sinh khi chuyến hoàn thành:** $c_i = v_i \cdot P(\text{hoàn thành} \mid \text{được phát})$, và voucher tỷ lệ với giá nên chuyến dài tốn hơn. Xếp hạng theo $\tau$ thay vì $\tau / c$ là thiếu tối ưu; trên 5 seed, điểm `tau_per_dollar_baseline` cho N = 3.896,0, hơn `tau_x_baseline` (3.862,4) (H-19d).
- **Hai tầng của π_θ là hai xấp xỉ thô của quy tắc trên:** tầng rider giữ session có điểm ≥ κ; tầng ô bỏ cả những ô mà hiệu ứng mỗi USD được dự báo thấp (ô căng). Nếu hàm điểm đã chứa đủ thông tin về trạng thái cung thì tầng ô không thêm gì; rà soát ngày 02/10 thấy đúng như vậy với một điểm chẩn đoán đọc tham số ẩn (Q27c).

Hệ quả quan trọng: **dưới ngân sách, θ\* không phải điểm hiệu ứng đổi dấu.** Đáng cắt cả những ô có hiệu ứng *dương nhưng nhỏ hơn giá bóng* λ, để dồn tiền sang ô tốt hơn. Vì vậy ngưỡng ước lượng từ thí nghiệm không ngân sách (điểm hiệu ứng cắt 0, $\hat\theta = 0$ trong dữ liệu hiện có) khác θ\* dưới ngân sách ([0,4; 2]) (H-19c, T-31).

Giới hạn của khung này: khi SUTVA vỡ, $\tau_i$ không xác định rõ (§2.1). Bài toán cái túi chỉ dùng để *thiết kế* lớp chính sách; thứ phán xử cuối cùng là $N(\pi)$ chạy trong simulator.

### 2.9 So sánh chính sách bằng mô phỏng: CRN, ghép cặp, so sánh bội

**Số ngẫu nhiên chung (CRN).** Hai chính sách chạy trên cùng các seed với cùng số ngẫu nhiên cho mỗi session (§6). Khi đó

$$
\operatorname{Var}(N_1 - N_2) = \operatorname{Var} N_1 + \operatorname{Var} N_2 - 2 \operatorname{Cov}(N_1, N_2),
$$

và CRN làm $\operatorname{Cov} > 0$ lớn. A2(b) đo được phương sai của hiệu bằng 0,242 lần so với seed độc lập (§8.2). Mọi so sánh vì vậy dùng **hiệu ghép cặp theo seed** và SE của hiệu.

**Tập θ\* bằng so sánh bội với cái tốt nhất (T-31).** Đường $N(\pi_\theta)$ có đoạn phẳng nên θ\* được báo là một **tập**: các θ chưa phân biệt được với θ tốt nhất $\hat b$. Với $n$ seed và $k$ mốc θ:

$$
\text{gap}_\theta = \overline{N_{\hat b} - N_\theta},
\qquad
\theta \in \Theta^* \iff \text{gap}_\theta - t_{1 - \alpha/(k-1),\; n-1} \cdot \text{SE}(\text{gap}_\theta) \le 0 ,
$$

tức cận dưới một phía đồng thời (Bonferroni trên $k - 1$ phép so, phân vị Student-t) không loại được khả năng θ tốt bằng $\hat b$. Khoảng θ\* báo cáo là bao của tập (`analysis.metrics.theta_star_set`, `theta_star_interval`).

**Regret.** Ngưỡng $\hat\theta$ ước lượng từ dữ liệu được chấm bằng $\text{regret}(\hat\theta) = N(\pi_{\hat b}) - N(\pi_{\hat\theta})$, ghép cặp theo seed, nội suy tuyến tính giữa hai mốc lưới (`analysis.metrics.sweep_regret`). Trong đoạn phẳng regret gần 0 dù $\hat\theta$ xa θ tốt nhất, nên regret khớp với tiêu chí N hơn khoảng cách.

### 2.10 Qini và AUUC

Qini đo khả năng **xếp hạng** hiệu ứng cá nhân trên một tập session đã cho. Theo Radcliffe, với $k$ session điểm cao nhất:

$$
Q(k) = Y_T(k) - Y_C(k)\,\frac{N_T(k)}{N_C(k)},
$$

với $Y_T, Y_C$ là số kết cục dương và $N_T, N_C$ là số session ở nhánh có và không có voucher trong nhóm đó. Hệ số Qini là diện tích dưới đường Qini trừ diện tích của đường thẳng ngẫu nhiên (T-27).

Qini được tính trên dữ liệu đã sinh, với thị trường đã cố định: nó không thấy việc phát voucher theo thứ hạng đó sẽ làm thị trường đổi thế nào, cũng không thấy chi phí. Vì vậy một chính sách có Qini cao hơn vẫn có thể có N(π) thấp hơn dưới cùng B. Tìm một ví dụ cụ thể là tiêu chí nghiệm thu quan trọng nhất của đề tài (T5.2; Yadlowsky et al. 2025 cho cách nhìn Qini như một trung bình có trọng số của hiệu ứng theo thứ hạng).

---

## 3. Kiến trúc simulator

### 3.1 Mô hình tác tử, thời gian rời rạc

Simulator là mô hình agent-based (ABM) với hai loại tác tử: rider (20.000, cố định, quay lại qua nhiều ngày) và tài xế (240). Thời gian tiến theo **tick** 60 giây; mỗi tick chạy 10 bước theo thứ tự cố định (§3.3). Thời điểm sự kiện (đón, trả, hủy) lưu chính xác bằng giây, không làm tròn theo tick (H-10a).

Sáu khối, 13 module:

| Khối | Module | File | Vai trò |
|---|---|---|---|
| A. Thế giới và trạng thái | M1 SpaceTime | `sim/space.py` | lưới ô, torus, ma trận thời gian $T[a,b,h]$, ETA |
| | thế giới tĩnh | `sim/population.py` | trọng số ô, rider, lịch ca tài xế (theo `world_seed`) |
| | trạng thái | `sim/state.py` | mảng xe, order, session; bộ đếm; đồng hồ |
| B. Hành vi khách | M2 DemandGenerator | `sim/demand.py` | sinh session Poisson, chọn rider và ô đích |
| | M4 RiderChoice | `sim/choice.py` | quyết định đặt xe (logit) |
| | M7 Cancellation | `sim/cancel.py` | bỏ chờ, hủy trong lúc xe đi đón |
| C. Chính sách nền tảng | M3 Pricing & Promotion | `sim/pricing.py`, `sim/budget.py`, `sim/policies/` | giá, voucher, ngân sách, chính sách |
| | M5 Matching | `sim/matching.py` | ghép đơn với xe rảnh |
| D. Vận hành đội xe | M6 TripExecution | `sim/trips.py` | đón, chở, trả, thanh toán |
| | M8 SupplyModel | `sim/supply.py` | ca làm |
| | M9 Repositioning | `sim/reposition.py` | xe rảnh lâu chuyển sang ô kề |
| E. Điều phối thí nghiệm | M10 ExperimentDesigner | `sim/experiment.py` | cụm, block, gán nhánh |
| | M13 CounterfactualRunner | `sim/runner.py` | các chế độ chạy, pilot, quét θ, GTE |
| F. Giám sát và dữ liệu | M11 MarketMonitor | `sim/monitor.py` | chỉ số theo (ô, slot), công bố snapshot |
| | M12 Logger | `sim/logger.py` | ghi Parquet theo `docs/schema.md` |

Vòng lặp nằm ở `sim/engine.py`. Mô hình uplift nằm **ngoài** simulator: simulator chỉ nhận một hàm điểm $\hat\tau(x, s)$ (`policies/scores.py`).

### 3.2 Thang thời gian và cửa sổ đánh giá

| Thang | Mặc định | Vai trò |
|---|---|---|
| Thời điểm sự kiện | giây, số thực | mốc đặt, ghép, đón, trả, hủy |
| Tick | 60 giây | một vòng 10 bước; ghép đơn theo lô |
| Slot | 15 phút = 15 tick | đơn vị quyết định bật/tắt khuyến mãi; tổng hợp `slot_snapshots` |
| Block | 60 phút | đơn vị thời gian của switchback; là bội của slot |
| Ngày / kỳ ngân sách | 24 giờ | chu kỳ cầu, ca làm; giá trị trễ theo ngày; mỗi kỳ có ngân sách B |

Một lượt chạy gồm ba đoạn:

```
t = 0         60 phút                              60 + window                       + tối đa 120 phút
|-- warm-up --|--------- cửa sổ đánh giá ----------|---------- cool-down ----------|
  không tính     session chỉ sinh trong đoạn này      không sinh session mới; chạy đến khi
  vào N, V       N, V tính theo đơn đặt trong đoạn này mọi đơn của cửa sổ kết thúc; còn dở -> Truncated
```

- **Warm-up** cho đội xe và hàng chờ về trạng thái ổn định. Ca làm tuần hoàn (T-02) nên lúc t = 0 đã có đúng số xe đang trong ca, không có khởi động lạnh.
- **Cool-down** để N(π) đếm cả đơn đặt cuối cửa sổ mà hoàn thành sau cửa sổ; bỏ đi sẽ làm chính sách tạo nhiều đơn muộn bị thiệt.
- **Kỳ ngân sách** (T-03) neo theo cửa sổ, dài $P = \min(1440, \text{window})$ phút. Mỗi kỳ có sổ riêng và cùng mức B; mỗi khoản giữ chỗ thuộc kỳ của thời điểm mở session, kể cả khi đơn kết thúc ở kỳ sau. Warm-up là kỳ −1 với ngân sách $B \times \text{warmup}/P$, để trạng thái đầu cửa sổ đã phản ánh chính sách.

### 3.3 Vòng lặp 10 bước của một tick và lý do của thứ tự

| # | Bước | Module | Vì sao ở vị trí này |
|---|---|---|---|
| 1 | Xe tới điểm đón, trả khách, điều chuyển xong | M6, M9 | Giải phóng xe trước mọi quyết định của tick. |
| 2 | Vào ca, hết ca | M8 | Xe vừa trả khách ở bước 1 được rời ngay nếu đã hết ca; "chỉ rời khi rảnh" tự đúng nhờ thứ tự này (H-08a). |
| 3 | Đơn chờ quá `max_wait` bị bỏ | M7 | Loại đơn hết kiên nhẫn trước khi ghép. |
| 4 | Sinh session mới (chỉ trong cửa sổ) | M2 | |
| 5 | Gán nhánh, báo giá, voucher, giữ ngân sách, ETA báo | M10, M3 | Voucher phải quyết định **trước** khi rider chọn, để nó tác động tới hành vi. ETA báo tính từ số xe rảnh hiện tại. |
| 6 | Rider quyết định đặt; không đặt thì nhả ngân sách | M4 | |
| 7 | Ghép đơn theo FIFO, lập lịch đón | M5, M6 | Đơn mới được ghép ngay trong tick. |
| 8 | Hủy trong lúc xe đi đón | M7 | Xe bị hủy rảnh lại tại chỗ, không ghép lại trong cùng tick. |
| 9 | Điều chuyển xe rảnh lâu | M9 | Sau ghép, để xe rảnh được ưu tiên nhận đơn trước khi bỏ đi. |
| 10 | Cộng dồn chỉ số; hết slot thì công bố snapshot | M11, M12 | Snapshot của slot k chỉ dùng được từ slot k + 1 (không nhìn trước). |

### 3.4 Vòng đời session, order, tài xế

```
Session/Order:
  Quoted --không đặt--> NoRequest
     |
    đặt
     v
  Waiting --ghép--> Matched --xe tới--> OnTrip --trả khách--> Completed
     |                  |
  quá max_wait     H(t) >= e_cancel
     v                  v
  Abandoned         Cancelled          (còn dở khi hết cool-down: Truncated)

Tài xế:
  Offline --vào ca--> Idle --được ghép--> EnRoute --đón khách--> OnTrip --trả khách tại ô đích--> Idle
                       ^  \                  |
                       |   rảnh >= max_idle  khách hủy -> Idle (tại ô xuất phát hoặc ô khách)
                       |      v
                       +-- Repositioning (tới ô kề)
  Idle --hết ca--> Offline   (chỉ rời khi đang Idle)
```

Chỉ xe `Idle` **và** còn trong ca được ghép. Xe đang đi đón, đang chở, đang điều chuyển đều không nhận đơn mới. Tính thời gian đi đón vào thời gian bận là điều kiện để WGC xuất hiện (Castillo et al. 2025).

### 3.5 Cài đặt và tính tái lập

- Trạng thái xe, order, session lưu dạng struct-of-arrays numpy; không tạo object Python cho từng xe hay khách trong vòng lặp nóng; không lặp qua toàn bộ đội xe mỗi tick (quy tắc 7).
- Tiền trong sổ ngân sách tính bằng **cent nguyên**, để bất biến ngân sách đúng tuyệt đối.
- Simulator tất định theo (config, seed). Mỗi output mang `config_hash` (SHA-1 của config đã chuẩn hóa kiểu), `git_sha`, `run_id = <mode>-<config_hash>-<policy>-<theta>-<seed>`, và toàn văn config trong `meta/run_metadata`.
- A5: một ngày mô phỏng với chính sách mặc định (threshold, κ auto) mất trung vị 6,53 giây trên 1 lõi, dưới mục tiêu 30 giây (H4.1).

---

## 4. Mô hình từng thành phần

Nhãn nguồn của tham số theo `default.yaml`: `[report]` báo cáo thiết kế, `[data]` số liệu thị trường, `[paper]` bài báo, `[assume]` giả định của nhóm, `[P3]` đã hiệu chỉnh ở mốc P3. Bảng đầy đủ ở Phụ lục A.

### 4.1 M1 Không gian và thời gian di chuyển

**Lưới lục giác.** Tọa độ trục $(q, r)$, tập ô $\{(q, r) : \max(\lvert q\rvert, \lvert r\rvert, \lvert q + r\rvert) \le R\}$, gồm $3R^2 + 3R + 1$ ô; $R = 3$ cho 37 ô (D6). Lưới lục giác được chọn vì tâm sáu ô kề cách đều tâm ô đang xét, thuận cho tìm xe lân cận và cho xe di chuyển sang ô kề (Lin et al. 2018).

**Torus.** Ô kề vượt biên được ánh xạ sang biên đối diện bằng hai vector tịnh tiến $a = (2R + 1, -R)$, $b = (R, R + 1)$; khoảng cách là $\min_{i,j \in \{-1,0,1\}} \text{hexdist}(x, y + i a + j b)$. Lý do: với lưới cắt biên, ô biên có ít ô kề nên luôn căng cung hơn, và độ căng bị lẫn với vị trí địa lý (với $R = 2$, 12 trên 19 ô nằm ở biên). Trên torus mọi ô có đúng 6 ô kề; quanh mỗi ô có 6, 12, 18 ô ở vành 1, 2, 3, phủ đúng 37 ô.

**Hình học.** Cạnh ô 0,75 km, diện tích $A = \tfrac{3\sqrt3}{2} \cdot 0{,}75^2 = 1{,}461$ km², khoảng cách tâm hai ô kề $s = \sqrt3 \cdot 0{,}75 = 1{,}299$ km.

**Ma trận thời gian** (phút), với tốc độ $v_h = 18 \cdot \text{speed\_factor}[h]$ km/h và hệ số đường vòng 1,3:

$$
T[a, b, h] =
\begin{cases}
1{,}3 \cdot D[a,b] \cdot s / v_h \cdot 60 & a \ne b \\
1{,}3 \cdot 0{,}5 \sqrt{A} / v_h \cdot 60 & a = b \text{ (chuyến trong ô)}
\end{cases}
$$

**ETA đón khi trong ô khách có $I \ge 1$ xe rảnh** (công thức (4) của báo cáo thiết kế, §2.3):

$$
\text{ETA}_{\text{in}}(I, h) = \max\!\left(1, \; 1{,}3 \cdot 0{,}5 \left(\frac{A}{I}\right)^{0{,}5} \!\Big/ v_h \cdot 60 \right).
$$

Số minh họa (phút):

| Giờ | $v_h$ (km/h) | Trong ô | Vành 1 | Vành 2 | Vành 3 | ETA trong ô, I = 1 | I = 4 | I ≥ 13 |
|---|---|---|---|---|---|---|---|---|
| 3h | 22,5 | 2,10 | 4,50 | 9,01 | 13,51 | 2,10 | 1,05 | 1,00 |
| 13h | 16,2 | 2,91 | 6,25 | 12,51 | 18,76 | 2,91 | 1,46 | 1,00 |
| 8h, 18h | 13,5 | 3,49 | 7,51 | 15,01 | 22,52 | 3,49 | 1,75 | 1,00 |

Đọc bảng: khi ô khách còn 1 xe rảnh, ETA lúc cao điểm là 3,5 phút; khi ô hết xe, ETA nhảy lên ít nhất 7,5 phút (vành 1). Bước nhảy này là cơ chế vi mô của WGC. $T[a, a, h]$ trùng $\text{ETA}_{\text{in}}(1, h)$ vì hai hệ số cùng bằng 0,5: trùng hợp, không phải lỗi.

**Tìm xe** (`SpaceTime.find_pickup`, dùng chung cho báo giá và ghép, H-04): ô khách còn xe rảnh thì dùng $\text{ETA}_{\text{in}}$; hết xe thì xét vành 1, 2, 3 và lấy ô có $T$ nhỏ nhất ở vành gần nhất còn xe; ETA vượt `max_pickup_eta_min` (30 phút) thì coi như không đón được. Vì $T$ xa nhất là 22,5 phút < 30, với cấu hình mặc định giới hạn này không bao giờ chặn: còn một xe rảnh ở bất kỳ đâu thì đơn được ghép. Đó là ý đồ (D5): giới hạn thấp sẽ xóa WGC.

### 4.2 Thế giới tĩnh: ô, rider, tài xế

Sinh một lần theo `world_seed`, giống nhau ở mọi lượt chạy, mọi chính sách.

**Trọng số ô** $w_z \sim \text{LogNormal}(0, 0{,}5)$, chuẩn hóa trung bình 1 (thực tế từ 0,32 đến 2,44). Trọng số quyết định cầu, ô nhà của rider, ô xuất phát của tài xế và hướng điều chuyển.

**Rider** (20.000):

| Thuộc tính | Phân phối | Quan sát được? |
|---|---|---|
| `home_cell` | theo $w_z$ | có |
| `x_freq` | Gamma(2, 1), trung bình 2 | có |
| `x_tenure` | Uniform(0, 36) tháng | có |
| `x_segment` | 0/1/2 với xác suất 0,5/0,3/0,2 (thường / nhạy giá / ít nhạy giá) | có |
| `u_latent` | N(0, 1) | **ẩn** |
| $\alpha_i$ | $0{,}35 + 0{,}4\,z_f + 0{,}4\,u + \mathcal N(0, 0{,}3^2)$ | **ẩn** |
| $\beta^p_i$ | $-0{,}10 \cdot m_{\text{seg}} \cdot e^{\mathcal N(0, 0{,}25^2)}$, $m = (1{,}0;\ 1{,}6;\ 0{,}6)$ | **ẩn** |
| $\beta^\eta_i$ | $-0{,}10 \cdot e^{\mathcal N(0, 0{,}25^2)}$ | **ẩn** |
| $\delta_i$ | $0{,}25 + 0{,}10\,u + \delta_{\text{seg}} + \mathcal N(0, 0{,}1^2)$, $\delta_{\text{seg}} = (0;\ 0{,}15;\ -0{,}10)$ | **ẩn** |
| $\text{max\_wait}_i$ | LogNormal, mode 5 phút | **ẩn** |

($z_f$ là `x_freq` chuẩn hóa z-score.) Trung bình trong quần thể: $\alpha = 0{,}35$, $\beta^p = -0{,}113$/USD, $\beta^\eta = -0{,}103$/phút, $\delta = 0{,}274$. Biến ẩn chỉ dùng để sinh hành vi và làm ground truth; chúng nằm trong `hidden/riders_hidden` và không bao giờ vào `observed/` (§4.12).

**Tài xế** (240, `[P3]`):
- Giờ bắt đầu ca rút từ hỗn hợp: 30% trong 6:00–8:30, 20% trong 10:00–14:00, 35% trong 15:00–19:00, 15% trong 19:00–23:00. Độ dài ca $\mathcal N(8; 1{,}5^2)$ giờ, cắt trong [4; 11]. Ô xuất phát theo $w_z$.
- Ca tuần hoàn theo ngày: tài xế trong ca khi $((t/3600 - \text{shift\_start}) \bmod 24) < \text{shift\_len}$ (T-02).

Cung và cầu theo giờ (minh họa; cầu = session kỳ vọng mỗi giờ trên toàn lưới):

| Giờ | 0h | 3h | 5h | 6h | 7h | 8h | 9h | 12h | 14h | 17h | 18h | 19h | 21h |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Xe trong ca | 94 | 43 | 19 | 15 | 31 | 57 | 68 | 92 | 118 | 99 | 108 | 122 | 120 |
| Session/giờ | 385 | 220 | 495 | 881 | 1.541 | 1.871 | 1.431 | 1.211 | 1.101 | 1.926 | 2.036 | 1.651 | 1.156 |
| Session/xe | 4,1 | 5,1 | 26,1 | 58,7 | 49,7 | 32,8 | 21,0 | 13,2 | 9,3 | 19,5 | 18,9 | 13,5 | 9,6 |

Vùng căng của thế giới mặc định nằm ở **5–8h**: cầu buổi sáng lên trước khi ca sáng vào đủ. Đỉnh cầu 18h không căng vì có 108 xe. Đây là hệ quả của lịch ca giả định, không phải của dữ liệu (Q25, H-20; §10).

### 4.3 M2 Sinh cầu

Số session của ô $z$ trong tick bắt đầu lúc $t$:

$$
\lambda_z(t) = 35 \cdot 0{,}85 \cdot w_z \cdot \text{hour\_profile}[h(t)] \cdot \frac{60}{3600},
\qquad n_z(t) \sim \text{Poisson}(\lambda_z(t)).
$$

Tổng hệ số giờ là 23,3, nên kỳ vọng khoảng 25.650 session/ngày; đo được 25.859 (seed 0, gồm warm-up).

Với mỗi session:
- **Rider:** với xác suất 0,8 chọn trong các rider có ô nhà là $z$, ngược lại chọn trong toàn bộ; trong nhóm được chọn, xác suất tỷ lệ với `x_freq`.
- **Ô đích:** $P(d \mid o) \propto w_d \exp(-D[o, d] / 3)$.
- **Rút sẵn**, luôn đủ và theo thứ tự cố định: `u_book`, `u_target`, `u_explore`, `u_explore_arm`, `trip_noise` (LogNormal(0; 0,15)), `e_cancel` (Exp(1)), `u_score` (§6.3).

Session là **lượt mở app** (nhu cầu tiềm năng), không phải request: chỉ khoảng 14% thành request. Session không đặt vẫn được ghi để học tỷ lệ chuyển đổi và hiệu ứng voucher (Johari et al. 2026).

### 4.4 M3 Giá, voucher và ngân sách

- **Giá gốc** $p_s = 3{,}0 + 1{,}70 \cdot T[\text{đón}, \text{trả}, h]$ USD (`per_min_usd` `[P3]`), trung bình 19,03 USD trên chuyến hoàn thành, trong mục tiêu 19,1 ± 10% `[data]`. Không có surge (ngoài phạm vi).
- **Voucher** $v_s = 0{,}20 \cdot p_s$, làm tròn cent; giá thực trả $p_s - v_s$. Nền tảng chịu voucher; tài xế nhận $(1 - 0{,}24) \cdot p_s$ trên giá gốc.

**Sổ ngân sách** (`BudgetLedger`). Mỗi voucher đi qua ba trạng thái:

```
bước 5: phát voucher  -> reserved
bước 6: rider đặt     -> committed      (không đặt: nhả)
bước 1: Completed     -> spent          (Abandoned / Cancelled / Truncated: nhả)
```

Chỉ phát khi $\text{spent} + \text{committed} + \text{reserved} + v_s \le B$ của kỳ; nếu không đủ thì session ghi `budget_blocked`. Bất biến $\text{spent} + \text{committed} + \text{reserved} \le B$ đúng tại mọi tick, mọi kỳ (quy tắc 8). Giữ chỗ ngay lúc phát (thay vì trừ khi hoàn thành) để giới hạn là cứng dù kết cục của các đơn đang chạy chưa biết. Ngân sách áp ở **một chỗ** cho mọi chính sách: lớp voucher trong `pricing.py` gọi chính sách, rồi giữ ngân sách theo thứ tự `session_id` (L12), nên thứ tự giữ chỗ không phụ thuộc chính sách.

**Mức B** (`budget.mode = fraction_of_all_on`): chạy pilot `all_on` không ngân sách (seed `run_seed + 9000`), lấy chi tiêu voucher trung bình mỗi kỳ trong cửa sổ, nhân 0,3 (`[assume]`). Pilot chi 18.486,00 USD nên **B = 5.545,80 USD/kỳ**. B tính một lần cho mỗi thế giới và dùng chung cho mọi chính sách, θ và seed. Chính sách cũ cũng chịu B, để dữ liệu quan sát giống thực tế.

### 4.5 M4 Quyết định đặt xe

Công thức logit của §2.4, với giá và ETA báo của bước 5 và voucher do lớp voucher cấp (session bị chặn ngân sách quyết định như không có voucher, H-06d). Đặt xe khi `u_book` < P. Nếu không có xe trong giới hạn (`no_supply`), rider vẫn quyết định với ETA báo 30 phút.

Cùng lúc ghi vào `hidden/sessions_hidden` hai xác suất **trong cùng bối cảnh**: `p_request_treat` (voucher tính bằng đúng quy tắc làm tròn của voucher thật, H-06b) và `p_request_control`. Session được cấp voucher có xác suất đặt đúng bằng `p_request_treat`, session không được cấp đúng bằng `p_request_control`.

### 4.6 M5 Ghép đơn

Mỗi tick duyệt các đơn `Waiting` theo thứ tự đặt (FIFO). Với mỗi đơn, dùng quy tắc tìm xe của §4.1: ưu tiên xe cùng ô (chọn xe rảnh lâu nhất, chỉ để phá hòa, rồi `driver_id` nhỏ nhất), hết xe cùng ô thì lấy xe ở vành gần nhất còn xe. Đây là giao thức **first dispatch** (ghép ngay xe rảnh gần nhất) mà Castillo et al. chỉ ra là sinh WGC khi xe rảnh thưa; quy tắc ưu tiên không gian theo Lin et al. (2018). Ô nào đã không tìm được xe trong tick thì các đơn sau ở ô đó bỏ qua luôn (số xe chỉ giảm trong tick, nên kết quả không đổi; H-09e). Khi ghép, chốt thời gian chuyến (§4.7) và ghi `pickup_eta_min`, `driver_origin_cell`.

### 4.7 M6 Chạy chuyến và thanh toán

- Đón lúc $t_{\text{ghép}} + \eta$; trả lúc đón $+ T[\text{đón}, \text{trả}, h_{\text{đón}}] \cdot \text{trip\_noise}$, với `trip_noise` rút sẵn (sai số ±15% quanh thời gian kỳ vọng).
- Trả khách: xe rảnh tại ô trả, `idle_since` = thời điểm trả; ngân sách chuyển committed → spent.
- Thanh toán: `gross_fare` $= p_s$; `net_fare` $= p_s - v_s$; `driver_pay` $= 0{,}76\,p_s$; `platform_profit` $= \text{net} - \text{driver\_pay}$.

### 4.8 M7 Bỏ chờ và hủy

- **Bỏ chờ** (bước 3): đơn `Waiting` có $t - t_{\text{đặt}} \ge \text{max\_wait}_i \cdot 60$ chuyển `Abandoned`, nhả ngân sách.
- **Hủy trong lúc xe đi đón** (bước 8): hazard tích lũy so với `e_cancel` rút sẵn (§2.5). Khi hủy: đơn `Cancelled`, nhả ngân sách; xe rảnh **tại chỗ đang đứng**, xấp xỉ bằng ô xuất phát nếu chưa đi quá nửa ETA, ngược lại ô khách; không được ghép lại trong cùng tick (Yao & Bekhor 2024).

### 4.9 M8 Cung

- Vào ca: `Offline → Idle` tại ô xuất phát. Hết ca: chỉ rời khi đang `Idle`; đang bận thì rời ngay sau khi trả khách.
- **Cung độc lập với chính sách** (D7, quy tắc 5): rời sớm theo thu nhập tắt mặc định (`early_exit_enabled = false`; nhánh bật chưa cài, Q18). Tài xế không phản ứng với voucher hay thu nhập.
- `shift_mode = always_on` (mọi xe online suốt lượt) chỉ dùng cho `throughput_curve` (T-08).

### 4.10 M9 Điều chuyển xe

Xe rảnh từ 10 phút trở lên chuyển sang một ô kề, rút theo trọng số **tĩnh** $w_z$ bằng một số đều từ luồng DRIVER khóa `(driver_id, reposition_count)` (H-11). Không đọc cầu hay snapshot hiện tại (có test cắm đồ giả ném lỗi nếu bị gọi). Xe đang điều chuyển không nhận đơn và không tính vào slack.

Rà soát ngày 02/10: xe dành 16,4% thời gian online để điều chuyển. Tắt điều chuyển (`stay`) gần như không đổi GTE (+1.193,8 ± 22,3 so với +1.198,8 ± 27,1, 5 seed), nên kết luận không phụ thuộc M9.

Lưu ý chính xác: "cung độc lập với chính sách" nghĩa là **quy tắc quyết định** của tài xế không đọc tín hiệu chính sách. **Vị trí** của xe vẫn đổi theo chính sách, vì vị trí là hệ quả của các chuyến đã chạy. Đó chính là kênh tranh chấp cung cần đo.

### 4.11 M11 Chỉ số thị trường và công bố snapshot

Sau bước 9 của mỗi tick, cộng dồn cho từng ô $z$:
- $I_z$: số xe rảnh trong ô;
- $E_z$: số xe đang đi đón, đếm theo **ô khách**;
- $O_z$: số xe đang chở, đếm theo ô đón;
- $W_z$: số đơn đang chờ.

Cuối slot lấy trung bình theo tick và tính:

$$
\text{slack} = \frac{I}{E} \;\; (E > 0); \qquad
\text{slack} = +\infty \text{ nếu } E = 0,\ I > 0; \qquad
\text{slack} = 0 \text{ nếu } I = 0 .
$$

Trường hợp $I = 0$ được chốt là 0 (H-14): ô không có xe rảnh nào không thể là ô dư cung. Trước khi chốt, 26,6% số (ô, slot) có $I = E = 0$ bị coi là slack vô cùng và chính sách bật khuyến mãi đúng ở chỗ thiếu xe nhất.

Vì sao **slack** là chỉ số mặc định (D4, theo Castillo et al.): nó có ngưỡng WGC đã biết (0,25–0,45) và vẫn phân biệt được các mức căng quanh ngưỡng đó. Tỷ lệ bận $u = (E + O)/(I + E + O)$ chạm 1 khi hết xe rảnh nên không phân biệt được mức quá tải; $I/W$ bằng 0 khi hết xe rảnh dù thiếu ít hay nhiều. Chọn chỉ số nào cho ngưỡng tốt nhất vẫn là câu hỏi phân tích; cách chọn đã chốt ở H-22 (theo khả năng dự báo mức phục vụ, không theo N).

**Không nhìn trước** (quy tắc 2): snapshot của slot k được công bố khi slot k kết thúc. Chính sách ở slot k chỉ đọc qua `SnapshotView(k)`, đối tượng này ném `LookAheadError` nếu truy cập slot ≥ k. Snapshot ghi hai giá trị trễ: `slack_lag_slot` (slot k − 1) và `slack_lag_day` (slot k − 96, NaN nếu chưa có).

Bộ đếm theo slot (`n_sessions`, `n_requests`, `n_matched`, …) tính theo **thời điểm sự kiện** và **ô đón** (T-15).

### 4.12 M12 Ghi dữ liệu: tách quan sát và ground truth

```
observed/   riders, sessions, orders          mô hình và chính sách được đọc
market/     slot_snapshots                    được đọc
hidden/     riders_hidden, sessions_hidden    chỉ để đánh giá, debug; không nối vào dữ liệu huấn luyện
results/    policy_results, theta_sweep, throughput_curve
meta/       run_metadata
```

Danh sách cột ẩn chuẩn nằm ở `docs/schema.md` (T-11): `u_latent, alpha, beta_price, beta_eta, delta_promo, max_wait_min, propensity_true, p_request_treat, p_request_control, direct_request_effect_fixed_market` và mọi số rút sẵn của session. Ba hàng rào: assert lúc import trong `logger.py`, test `test_no_hidden_leak`, và `analysis.io.load_run` không bao giờ trả bảng ẩn.

---

## 5. Chính sách voucher

### 5.1 Giao diện chung

Mỗi chính sách có hai hàm:
- `cell_state(slot, snapshots)`: gọi đầu mỗi slot, trả `promo_on[N]`, `cell_propensity[N]`, cơ chế gán;
- `offer(batch, cell_dec, ledger)`: gọi ở bước 5, trả `offer[n]`, `propensity[n]`, `score[n]`.

`SessionBatch` chỉ chứa cột quan sát được (rider, đặc trưng, ô, giờ, giá, ETA báo) và bốn số đều rút sẵn dành cho chính sách. Chính sách không được tự rút số ngẫu nhiên (§6). Riêng `LegacyPolicy` được đọc `u_latent` qua `LegacyHiddenView` để tạo gây nhiễu. Ngân sách áp **sau** chính sách, ở lớp voucher (L12).

### 5.2 Chính sách cũ (`legacy`): nguồn dữ liệu quan sát có gây nhiễu

Mô phỏng người vận hành, ba tầng:

| Tầng | Quy tắc | Propensity ghi lại |
|---|---|---|
| Ô | bật nếu `slack_lag_slot` ≥ 0,6; với xác suất ε = 0,1 thay bằng đồng xu 0,5 (luồng CELLSLOT) | `cell_propensity` = $(1 - \varepsilon)\cdot\text{rule} + \varepsilon \cdot 0{,}5$ ∈ {0,05; 0,95} |
| Rider, trong ô bật | phát nếu `u_target` < $\sigma(-0{,}5 - 0{,}5\,z_f + 1{,}0\,u_{\text{latent}})$ | quan sát: NaN (không biết); thật: $p_{\text{target}}$, chỉ ở `hidden/` |
| Explore | 5% session (`u_explore` < 0,05) phát bằng đồng xu 0,5, **bất kể** trạng thái ô | 0,5 |

Session ở ô tắt và không thuộc explore có propensity 0 (T-24). Thiết kế này cho đủ ba thứ: gây nhiễu (nhắm theo biến ẩn có ảnh hưởng tới kết cục), overlap cấp ô (đồng xu ε), và một lát RCT sạch (explore). Đồng xu ε còn đảm bảo ở mọi mức căng cung đều có cả ô bật lẫn ô tắt.

### 5.3 Thí nghiệm (`experiment`, M10)

- `cluster_switchback`: trạng thái của (cụm, block) = Uniform < 0,5 từ luồng CELLSLOT khóa (mức cụm, cụm, block); trong ô bật mọi session được phát. Cụm 1 ô, 7 ô hoặc toàn hệ (`global_switchback`).
- `rider_ab`: arm theo rider từ luồng RIDER, cố định cả lượt; mọi ô bật.
- Propensity = `p_on` = 0,5 cho mọi session (xác suất của thiết kế). Không áp ngân sách.
- Block đếm từ đầu lượt chạy; `warmup_min` là bội của `block_min` nên cửa sổ bắt đầu đúng biên block (H-01). Session và snapshot trong 15 phút đầu block ghi `in_burnin = True`; simulator vẫn chạy bình thường, bước phân tích tự loại.

### 5.4 Chính sách π_θ (`threshold`)

**Tầng ô.** Dự báo slack $\hat s_{z,k}$ từ snapshot đã công bố:
- `persistence`: $\hat s_{z,k} = \text{slack}_{z,k-1}$ (mặc định);
- `ar`: $0{,}7 \cdot \min(\text{slack}_{z,k-1}, 10) + 0{,}3 \cdot \min(\text{slack}_{z,k-96}, 10)$; ngày đầu (chưa có lag ngày) quay về persistence.

**Phạm vi đo** (`policy.threshold.scope`, H-25, T-35): `cell` (mặc định) dùng slack của chính ô; `ring1` dùng $\sum_{j \in R(z)} I_j / \sum_{j \in R(z)} E_j$ trên ô z và 6 ô kề $R(z)$, cùng quy tắc H-14, $+\infty$ cắt ở `slack_cap` = 10. Lý do (H-25): trên `all_off`, slack vòng 1 giải thích 26,9% phương sai ETA báo và bắt 86,0% session bị phục vụ tệ, so với 17,2% / 72,0% của slack theo ô: một ô cạn xe nhưng ô bên cạnh dư xe thì khách vẫn được đón nhanh. Vì cắt trần, với `ring1` mọi θ > 10 là `all_off`.

$\text{promo\_on}_{z,k} = \lnot(\hat s_{z,k} < \theta)$. Hệ quả: θ = 0 không cắt ô nào; ô có $\hat s$ = NaN (chưa có snapshot) hoặc $+\infty$ bật; ô không có xe rảnh ($\hat s = 0$) bị cắt với mọi θ > 0 (T-28). Với `hysteresis_h > 0`, ô đang tắt chỉ bật lại khi $\hat s > \theta + h$.

**Tầng rider.** Trong ô bật, phát nếu `score_fn(batch, ŝ)` ≥ κ và ngân sách còn đủ. Hàm điểm có sẵn: `random` (trả `u_score` rút sẵn), `heuristic_low_freq` ($-x_{\text{freq}}$, mặc định), hoặc chuỗi `"module:function"` nạp từ ngoài (ví dụ `analysis.scores:tau_per_dollar_baseline`). Quyết định tất định nên propensity là 1 hoặc 0: dữ liệu sinh bởi π_θ không dùng được cho IPW.

**κ auto** (D12, đã sửa theo H-21 ngày 05/10): κ chọn sao cho chi tiêu vừa B:
1. Chạy pilot π_θ với κ = −∞, **không** áp ngân sách nhưng vẫn cắt ô theo θ.
2. Với mỗi session được phát trong pilot, chi tiêu = voucher nếu chuyến hoàn thành, 0 nếu không.
3. Sắp giảm theo điểm; κ = điểm nhỏ nhất sao cho tổng chi tiêu của các session có điểm ≥ κ không vượt $B \times$ số kỳ.
4. **Lặp đến điểm bất động:** chạy lại pilot tại κ vừa tìm; nếu chi tiêu vẫn > B thì làm lại bước 2–3 trên lượt này (κ chỉ tăng). Dừng khi chi ≤ B hoặc hết số lần lặp tối đa (khóa YAML, thêm khi cài).
5. Mọi θ dùng **chung** seed pilot `run_seed + pilot_seed_offset`.

Dừng cứng khi chạm B vẫn giữ làm chốt an toàn. Lý do của bước 4 và 5: một lượt pilot ở κ = −∞ phát cho mọi rider nên thị trường tắc hơn lượt đánh giá; khi chỉ phát cho nhóm điểm cao, nhóm này hoàn thành nhiều chuyến hơn dự báo, chi 1,113 × B khi không chặn, và ngân sách cạn khoảng 22h (Q26). Pilot riêng cho từng θ thì mỗi θ mang một sai số κ riêng mà SE ghép cặp theo seed không thấy (Q24). **Trạng thái:** đã cài ngày 05/10 (T-32): khóa `policy.threshold.kappa_max_iter = 10`; mỗi θ cần 1–6 lượt pilot; số sweep θ ở §9 tính bằng κ mới. κ giữ hoặc bỏ trọn nhóm điểm bằng nhau, nên hàm điểm dạng bảng (ít giá trị) phải được phá hòa ngẫu nhiên bằng `u_score` trước khi dùng dưới B (T-33e).

### 5.5 Chính sách cố định và các chính sách so sánh

- `all_off`; `all_on` không ngân sách (chỉ cho GTE); `all_on` **có** ngân sách (phát theo thứ tự đến cho tới khi hết B mỗi kỳ, T-12).
- Bảng so sánh tuần 5 dưới cùng B (T5.1): `all_off`, `all_on` có B, điểm `random`, $\hat\tau(x)$, $\hat\tau(x, s)$, π_θ với θ ước lượng. Khi θ = 0, π_θ trùng chính sách xếp theo $\hat\tau(x, s)$.

---

## 6. Số ngẫu nhiên và CRN

### 6.1 Bộ sinh có khóa

Mọi phép rút ngẫu nhiên đi qua

```python
rng_for(stream, *key) = Generator(Philox(key = BLAKE2b_64(seed, stream, *key)))
```

với `seed = world_seed` cho luồng WORLD và `run_seed` cho các luồng khác. Mỗi (luồng, khóa) có một bộ sinh **riêng, độc lập với thứ tự gọi**. Nếu dùng một bộ sinh toàn cục, chỉ cần một chính sách rút thêm một số là mọi số sau đó lệch đi, và hai lượt chạy không còn so được với nhau. Philox là bộ sinh dựa trên bộ đếm, tạo luồng mới từ một khóa rất rẻ; BLAKE2b được dùng vì `hash()` của Python không ổn định giữa các tiến trình (L6). Không module nào được dùng `np.random.*` toàn cục hay `random` (test tĩnh, L9).

| Luồng | Khóa | Dùng cho |
|---|---|---|
| WORLD | (phần thế giới, chỉ số) | trọng số ô, rider, tài xế; không phụ thuộc `run_seed` |
| DEMAND | (ngày, tick trong ngày, ô) | số session Poisson |
| SESSION | (`session_id`) | rider, ô đích, các số rút sẵn |
| CELLSLOT | (loại, mức cụm, ô hoặc cụm, slot hoặc block) | ε của chính sách cũ, switchback |
| RIDER | (`rider_id`) | arm của A/B theo rider |
| DRIVER | (`driver_id`, bộ đếm) | hướng điều chuyển |

`session_id = ((ngày · tick_mỗi_ngày + tick) · N + ô) · 1000 + k` là định danh ổn định: cùng một session có cùng ID ở mọi chính sách.

### 6.2 Rút sẵn theo thứ tự cố định

Mỗi session rút, theo đúng thứ tự và **luôn rút đủ** bất kể chính sách: rider, ô đích, `u_book`, `u_target`, `u_explore`, `u_explore_arm`, `trip_noise`, `e_cancel`, `u_score` (T-07). Nếu một số chỉ được rút khi cần (ví dụ `u_score` chỉ khi `score_fn = random`), thứ tự rút sẽ phụ thuộc chính sách và CRN vỡ.

### 6.3 CRN ghép được gì và không ghép được gì

Giống hệt giữa mọi chính sách: thời điểm và vị trí mở app, rider, ô đích, ngưỡng đặt xe `u_book`, nhiễu thời gian chuyến, ngưỡng hủy `e_cancel`, độ kiên nhẫn chờ, hướng điều chuyển thứ n của mỗi tài xế.

Khác nhau (đúng ý đồ): voucher, trạng thái thị trường (số xe rảnh, ETA), xe nào phục vụ đơn nào, và mọi thứ đi theo. Sau một thời gian, trạng thái hai lượt chạy tách xa nhau, nên phần ghép cặp ở mức kết cục không hoàn hảo. Mức ghép cặp thực tế được đo bằng A2(b): phương sai của hiệu còn 0,242 lần (§8.2). A2(a) kiểm cùng chính sách, cùng seed cho N, V giống hệt; A2(c) kiểm hai chính sách gặp đúng cùng tập session.

### 6.4 Thế giới và lượt chạy

`world_seed` cố định thế giới (ô, rider, tài xế); `run_seed` thay đổi giữa các lần lặp. Mọi khoảng tin cậy hiện nay là **có điều kiện trên một thế giới** (`world_seed = 20260930`); phương sai giữa các thế giới chưa được đo, ngoài một lần kiểm CAL với `world_seed = 7` (§10.3).

---

## 7. Dùng simulator để ra đáp án đúng

### 7.1 Các chế độ chạy

| Mode | Làm gì | Ngân sách |
|---|---|---|
| `calibrate_budget` | pilot `all_on` để tính B | không |
| `evaluate` | 1 chính sách × `n_seeds` → N, V | có |
| `sweep_theta` | mỗi θ trong lưới × `n_seeds`, κ auto riêng từng θ, cùng B | có |
| `gte` | `all_on` và `all_off` × `n_seeds`, ghép cặp theo seed | không |
| `generate` | chạy nhiều ngày liên tục, ghi đủ `observed/`, `market/`, `hidden/` | legacy: có; thí nghiệm: không |
| `throughput_curve` | quét `demand_scale` với đội xe luôn online, giờ cố định 18h → đường throughput (A1) | không |

Lệnh: `python -m sim run --mode <mode> --config config/default.yaml [--config overlay.yaml] [--set a.b=c]`. Các seed chạy song song bằng `multiprocessing`.

### 7.2 Quy trình tìm θ\*

```
1. calibrate_budget: pilot all_on (seed 9000)                       -> B = 5.545,80 USD/kỳ
2. với mỗi θ_i trong lưới:
     pilot threshold, κ = -inf, không ngân sách, lặp đến khi chi ≤ B
     (H-21: chung seed 9000 cho mọi θ; 1–6 lượt pilot mỗi θ)    -> κ_i
     n seed đánh giá (0..n-1), có B, κ_i                            -> N_i(seed), V_i(seed)
3. theta_star_set: so sánh bội với cái tốt nhất, ghép cặp theo seed -> tập θ*
4. sweep_regret(θ̂): N(tốt nhất) - N(θ̂)                             -> regret của ngưỡng ước lượng
```

Sweep tham chiếu: lưới 16 mốc θ từ 0 đến 30 (`config/sweep_reference.yaml`) × 30 seed (T-31).

### 7.3 Dữ liệu cho phân tích (bộ B7a)

Năm bộ `generate` 28 ngày, cùng `run_seed = 0` nên cùng 718.749 session: `legacy_28d` (dữ liệu quan sát, có B), switchback cụm 1 / 7 / toàn hệ, `rider_ab` (không ngân sách); cộng `gte` 10 seed. Chi tiết và lệnh sinh lại ở `docs/datasets.md`.

### 7.4 Tách ba nguồn sai số (tiêu chí nghiệm thu 4)

| Nguồn | Phép so | Dữ liệu |
|---|---|---|
| Gây nhiễu | so thô có/không voucher trong `legacy_28d` so với lát explore (hoặc switchback) | B7a |
| Tranh chấp cung | ước lượng từ A/B theo rider hoặc switchback cụm nhỏ so với GTE | B7a + `gte` |
| Công suất | hiệu ứng lên request khi giữ thị trường cố định (`p_request_*`) so với hiệu ứng lên request và lên chuyến hoàn thành ở cân bằng (GTE) | `hidden/` + `gte` |

Số chỉ báo hiện có cho kênh công suất (khác quần thể nên chưa phải phép tách chính xác; phép tách đúng là việc của S5): request tăng +50,6% khi giữ thị trường cố định (session ở ô dư cung, `all_off`); request tăng +42,1% ở cân bằng (GTE: 3.644,2 → 5.178,3); chuyến hoàn thành tăng +35,3% (3.439,6 → 4.652,5).

---

## 8. Kiểm định: vì sao tin được simulator

Ba lớp: **verification** (code làm đúng spec), **nghiệm thu** (simulator tái tạo được hiện tượng cần đo), **hiệu chỉnh và đối chiếu** (độ lớn hợp lý).

### 8.1 Bất biến và kiểm tra cấu trúc

| Kiểm tra | Nội dung | Test |
|---|---|---|
| Bảo toàn | sessions = requested + không đặt; requested = Completed + Abandoned + Cancelled + Truncated | `test_integration::test_conservation` |
| Trạng thái xe | mỗi tick: tổng xe theo trạng thái = số xe online; xe rảnh không giữ đơn; mỗi xe bận giữ đúng một đơn còn sống | `test_driver_state_consistency` |
| Ngân sách | spent + committed + reserved ≤ B sau bước 9 của **mọi** tick, mọi kỳ, 1 ngày `default.yaml` | `test_acceptance`, `test_pricing` |
| Không nhìn trước | `SnapshotView(k)` ném lỗi khi đọc slot ≥ k; snapshot công bố đúng cuối slot | `test_monitor` |
| Không rò biến ẩn | không cột ẩn nào trong `observed/`, `market/`; `SessionBatch` không có cột ẩn | `test_logger::test_no_hidden_leak`, `test_policies` |
| CRN | không có `np.random` toàn cục; cùng session cùng số ở mọi chính sách | `test_rng`, A2 |
| Cung độc lập | điều chuyển không đọc snapshot hay cầu (đồ giả ném lỗi) | `test_supply` |
| Hợp đồng dữ liệu | tên và kiểu cột khớp `schema.md` | `test_schema_contract`, `test_logger` |

Bộ test nhanh: 477 test pass (log ngày 02/10).

### 8.2 Năm kiểm thử nghiệm thu của báo cáo thiết kế

| | Kiểm thử | Tiêu chí | Kết quả (`cb27f5348011`) |
|---|---|---|---|
| A1 | Đường throughput (đội xe cố định, quét cầu, giờ 18 cố định, 3 seed) | tăng rồi có đỉnh; mức cao nhất ≤ 0,95 × đỉnh; slack < 0,45 ở vùng giảm; ETA tăng không bước nhảy > 3 phút | **đạt 4/4**: đỉnh 781,2/giờ ở 3,25; mức 4,0 = 0,845 × đỉnh; slack ≤ 0,095; bước ETA lớn nhất +1,871 phút |
| A2 | CRN | (a) lặp lại giống hệt; (b) Var(hiệu) CRN ≤ 0,5 × seed độc lập; (c) cùng tập session | **đạt**: (b) 1.434,45 / 5.925,40 = 0,242 (20 seed) |
| A3 | Dao động của π_θ (θ = 0,35) | báo cáo; > 12 lần/ô/ngày thì thử hysteresis | trung vị 26,08 lần/ô/ngày; h = 0,1: 25,38 (gần như không giảm) |
| A4 | Tính đơn điệu (switchback cụm 7, tứ phân vị slack) | ghi số lần đổi dấu | 0 lần; hiệu ứng lên tỷ lệ hoàn thành tăng theo slack: +0,0500; +0,0645; +0,0751; +0,0813 |
| A5 | Thời gian chạy | trung vị ≤ 30 giây/ngày | 6,53 giây (threshold, κ auto) |

A1 là kiểm thử quan trọng nhất: nếu không tái tạo được đoạn giảm thì cả đề tài không có hiện tượng để đo (`plan.md`, gate P3). Các số A1 trong bảng đo ở cấu hình đã hiệu chỉnh:

| `demand_scale` | 0,25 | 1,0 | 2,0 | 3,0 | **3,25** | 3,5 | 3,75 | 4,0 |
|---|---|---|---|---|---|---|---|---|
| chuyến/giờ | 80,3 | 317,7 | 598,9 | 780,2 | **781,2** | 735,1 | 671,6 | 659,8 |

### 8.3 Hiệu chỉnh (CAL, mốc P3)

Chạy `all_off`, 5 seed. Session ở "ô dư cung" khi slack của **slot trước**, cùng ô, lớn hơn 1 (H-15): slack của chính slot là kết quả của các lượt đặt trong slot, điều kiện hóa lên nó cho P(đặt) ở ô "dư" gần 0.

| Chỉ tiêu | Mục tiêu | Nguồn mục tiêu | Trước | Sau |
|---|---|---|---|---|
| P(đặt) không voucher, ô dư cung | 13–17% | `[data]` 15% | 17,21% | **15,35%** |
| Request tăng khi có voucher, ô dư cung (`p_request_*`, H-16) | +35% đến +70% | `[data]` +50% | +36,4% | **+50,6%** |
| Giá gốc trung bình | 17,2–21,0 USD | `[data]` 19,1 USD | 16,47 | **19,03** |
| Tỷ lệ (ô, slot) slack < 0,35 | 10–35% | thiết kế kịch bản | 80,5% | **27,9%** |
| Tỷ lệ (ô, slot) slack > 1 | 30–80% | thiết kế kịch bản | 13,5% | **63,3%** |

Núm đã chỉnh (H-17): `fleet_size` 120 → 240; `demand_scale` 1,0 → 0,85; `alpha0` 0,475 → 0,35; `delta0` 0,15 → 0,25; `per_min_usd` 1,4 → 1,70. Không chỉnh `beta_price_per_usd`, `grid_radius`, tốc độ, `max_wait`, `max_pickup_eta_min`. Kiểm thêm với `run_seed` 100, 200 và `world_seed` 7: đều trong khoảng.

Hai lưu ý (Q28, chốt bằng H-23): hai chỉ tiêu cuối là **thiết kế kịch bản** ("có vùng căng thật, có vùng dư thật"), không phải số đo thực tế, và số tuyệt đối theo USD, số xe là quy ước; lời giải không duy nhất (270 xe với `demand_scale` 1,0 cũng đạt CAL; 240 xe được chọn vì đỉnh A1 nằm xa mép lưới cầu hơn).

### 8.4 Đối chiếu với dữ liệu NYC TLC (tháng 3/2024)

So 21,3 triệu chuyến Uber/Lyft với 5 ngày `all_off` của simulator (Q25, `analysis/tlc_hourly.py`):

| Chỉ số | NYC TLC | Simulator |
|---|---|---|
| Thời gian chờ xe đến trung bình | 3,54 phút | 3,52 phút |
| Phần tài xế nhận trên giá | 76,5% | 76% |
| Biên độ thời gian chờ theo giờ | 2,76–4,85 phút (1,8 lần) | 2,11–8,28 phút (3,9 lần) |
| Tài xế đang chở lúc 7h / đỉnh | 70% | 25% (xe trong ca) |
| Chuyến trung bình | 19,6 phút, 25,55 USD | 9,5 phút, 19,0 USD |

Đường cầu theo giờ của hai bên tương quan 0,85 (0,92 nếu chỉ lấy ngày thường). Mức trung bình khớp; hình dạng theo giờ thì không: simulator nhọn hơn ở hai đỉnh cầu và căng hơn nhiều vào sáng sớm. Nhóm quyết định giữ nguyên (H-20), vì ép simulator theo New York không làm nó sát thị trường mục tiêu (Việt Nam) hơn; điểm này phải ghi trong phần hạn chế.

### 8.5 Rà soát tính hợp lý (02/10)

- Thời gian xe theo trạng thái cộng đủ: rảnh 42,2%, đi đón 13,1%, chở 28,4%, điều chuyển 16,4%.
- ETA báo trung bình 3,64 phút so với ETA lúc ghép 3,81 phút (ETA báo hơi lạc quan vì các session trong cùng tick thấy cùng số xe rảnh).
- Điểm tốt hơn cho N cao hơn (so với `random`, θ = 0, 10 seed): điểm oracle chẩn đoán +259,4 ± 10,3; `heuristic_low_freq` +48,8 ± 8,4; oracle đảo ngược −172,7 ± 5,9.
- Độ chệch các thiết kế đúng thứ tự lý thuyết (§9).
- `legacy_28d` không trôi theo thời gian (−0,71 chuyến/ngày trên mức 3.871,8).

---

## 9. Kết quả đến Sprint 5

Các con số dưới đây vừa là kết quả, vừa là bằng chứng phương pháp chạy đúng. Phần S5 (τ̂ học bằng DR-learner, bảng N/V dưới cùng B, Qini so với N, sweep θ theo ŝ và hàm điểm) chạy ngày 05/10; mọi số ở `docs/datasets.md` (mục S5) và `docs/log.md`.

**Hiệu ứng toàn hệ.** GTE = **+1.212,9** chuyến/ngày (SE 14,2; 10 seed): N từ 3.439,6 lên 4.652,5, chi 18.630,5 USD voucher, V từ 15.661,5 xuống 3.732,0 USD. Theo giờ, bật toàn bộ chỉ làm **giảm** số chuyến ở 7h (−15,4) và 8h (−6,4): hiện tượng "voucher làm hại" có thật nhưng hẹp trong thế giới mặc định.

**Độ chệch của thiết kế thí nghiệm** (quy ra chuyến/ngày, so với GTE +1.212,9):

| Thiết kế | Ước lượng | Chệch |
|---|---|---|
| A/B theo rider | +1.647 | +36% |
| Switchback cụm 1 ô | +1.633,2 [1.576,4; 1.691,3] | +35% |
| Switchback cụm 7 ô | +1.513,0 [1.420,0; 1.601,7] | +25% |
| Switchback toàn hệ | +1.312,7 [1.101,7; 1.513,6] | +8% |

Thứ tự đúng như §2.7: cụm càng lớn, chệch càng nhỏ. Switchback toàn hệ vẫn chệch +8%; nhiều khả năng do carryover giữa block, nhưng phần này chưa được tách riêng.

**Gây nhiễu.** Trên `legacy_28d`, so thô +0,1018 so với lát explore +0,0695 (hiệu ứng lên tỷ lệ hoàn thành mỗi session).

**Hiệu ứng theo độ căng (RQ1, A4).** Không đổi dấu: hiệu ứng tăng theo slack. Theo slack toàn hệ trước block (switchback toàn hệ): +0,0042 [−0,0134; +0,0196] khi slack < 0,05; +0,0334 khi 0,6–1; +0,0680 khi slack ≥ 5. Ngưỡng không ngân sách (điểm hiệu ứng cắt 0) $\hat\theta = 0$ [0; 0,289].

**Đường N(π_θ) dưới B** (sweep tham chiếu B7b bản H-21, 16 θ × 30 seed, `heuristic_low_freq`, κ auto điểm bất động):

| θ | 0 | 0,1 | 0,4 | 1,0 | 1,5 | **2,0** | 5,0 | 10 | 30 |
|---|---|---|---|---|---|---|---|---|---|
| N | 3.860,3 | 3.884,3 | 3.890,8 | 3.889,9 | 3.891,8 | **3.899,7** | 3.876,9 | 3.837,2 | 3.693,0 |
| % (ô, slot) tắt | 0 | 25 | 31 | 39 | 45 | 47 | 61 | 69 | 75 |

Đường có ba đoạn: tăng (θ = 0 → 0,1, đúng lúc cắt 25% (ô, slot) không có xe rảnh), phẳng, rồi giảm khi cắt nhiều đến mức không tiêu hết B (từ θ ≈ 10). Tập θ\* = {0,3; 0,4; 0,5; 0,6; 0,8; 1,25; 1,5; 2,0}, bao **[0,3; 2]** (mốc 1,0 bị loại: chung seed pilot chưa xóa hết nhiễu κ riêng theo θ). Regret: θ = 0: 39,5 ± 4,0 (1,01%); θ mặc định 0,35: 7,8 ± 3,3; θ = 30: 206,7 ± 3,8. θ = 0,6 thuộc tập θ\* ở cả năm kịch bản (chuẩn; B × 1/3; B × 2; voucher 30%; cầu × 1,5). So với bản κ cũ (02/10: tốt nhất 3.901,7 ở θ = 1,5, regret θ = 0 là 53,3), lợi ích của tầng ô nhỏ hơn: một phần lợi ích cũ đến từ việc κ cũ làm ngân sách cạn sớm.

**Bậc thang dưới cùng B** (T5.1, `analysis.policy_table`, 30 seed, κ auto bản H-21; hiệu ghép cặp theo seed):

```
all_on có B (đến trước phát trước, hết tiền giữa ngày)   N = 3.686,7
+ rải ngân sách cả ngày (điểm random, θ = 0)            +120,3
+ xếp hạng rider (heuristic_low_freq)                    +53,3
+ tầng ô (θ = 0,5)                                       +34,6

đổi hàm điểm thay cho tầng ô (θ = 0):
τ̂(x)/USD nền H4.2                                       N = 4.002,0  (+315,3 ± 5,3 so với all_on có B)
τ̂(x)/USD DR (H-24, toàn bộ legacy)                      N = 3.989,9  (−12,1 ± 4,4 so với bản nền)
τ̂(x, s)/USD DR                                          N = 4.010,3  (+20,4 ± 4,9 so với τ̂(x)/USD DR)
τ̂(x) nền H4.2                                           N = 3.803,7  (ngang random)
τ̂(x) DR / τ̂(x, s) DR                                   N = 3.752,7 / 3.780,3  (dưới random)

hàm điểm học được cộng tầng ô ŝ = ring1:
τ̂(x)/USD DR, θ̂ (A) = 0,25                              N = 4.011,8  (+21,8 ± 4,6 so với θ = 0; ngang τ̂(x, s)/USD: +1,4 ± 4,0)
τ̂(x)/USD DR, θ̂ (B) = 5                                 N = 3.849,2  (tắt 70% (ô, slot), chỉ chi 0,890 × B)
```

Hai điều đọc được từ phần mới. Một: đưa trạng thái cung vào **hàm điểm** (τ̂(x, s)/USD, không tầng ô) hay vào **tầng ô** (τ̂(x)/USD với θ̂ (A)) cho cùng một mức lợi, khoảng +20 chuyến/ngày; hai cách này thay thế nhau chứ không cộng dồn (chưa thử cả hai cùng lúc, vì τ̂(x, s) học trên slack theo ô, T-35b). Hai: DR-learner chưa hơn bảng nền H4.2 trên N (−12,1 ± 4,4 với bản /USD), dù DR có Qini cao hơn; bản học trên toàn bộ legacy hơn bản chỉ học trên lát explore (+55,0 ± 5,0 với /USD), tức là ở cỡ mẫu này phương sai quan trọng hơn chệch do `u_latent`.

**Sweep θ theo phạm vi ŝ và hàm điểm (H-22 ii, H-25).** Ba sweep mới cùng lưới, cùng 30 seed với B7b (`runs/s5/sweep_*`); "DR/USD" = `analysis.uplift:tau_x_dr_all_per_dollar`:

| ŝ, hàm điểm | θ tốt nhất | N tốt nhất | Bao tập θ\* | Regret θ = 0 |
|---|---|---|---|---|
| ô, heuristic (B7b) | 2 | 3.899,7 | [0,3; 2] | 39,5 ± 4,0 (1,01%) |
| `ring1`, heuristic | 3 | 3.915,7 | [1,5; 3] | 55,4 ± 4,7 (1,42%) |
| ô, DR/USD | 0,4 | 4.006,6 | [0,1; 0,6] | 16,6 ± 5,7 (0,42%) |
| `ring1`, DR/USD | 1 | 4.017,4 | [0,2; 1,5] | 27,4 ± 4,1 (0,68%) |

Dự đoán ghi trước của H-22 (ii), "điểm càng tốt thì θ\* càng gần 0", **đúng trên cả hai cách đo ŝ**: thay heuristic bằng DR/USD, tập θ\* dời về gần 0 và regret của θ = 0 giảm khoảng một nửa; θ = 0 vẫn chưa vào tập θ\*. `ring1` hơn ô ở θ tốt nhất (+16,0 ± 3,2 với heuristic; +10,8 ± 4,4 với DR/USD), nhưng hiệu này chọn "tốt nhất" trên chính các seed đo nên hơi lớn hơn thật (§10.3 điểm 2). Hai thang θ không so trực tiếp được: ở cùng θ, `ring1` tắt ít (ô, slot) hơn khi θ nhỏ và nhiều hơn khi θ lớn. Regret của hai θ̂ của H5.3 trên `ring1`, DR/USD: θ̂ (A) = 0,25 (chỉ tránh tác hại, không ngân sách): **5,1 ± 3,1 (0,13%), CI chứa 0**; θ̂ (B) = 5 (có ngân sách): 168,2 ± 5,3 (4,19%). Mô hình (B) cắt quá tay: ở θ = 5, κ = −∞ mà vẫn không tiêu hết B. Một giải thích có thể (chưa kiểm): giả định "tầng rider rải đều" của (B) bỏ qua việc hàm điểm /USD đã dồn tiền vào session tốt nhất, nên phần còn lại cho tầng ô nhỏ hơn (B) tính.

Theo H-22, θ\* từ nay luôn báo kèm hàm điểm, B và bậc thang này, thay cho một con số "π_θ hơn all_on". Cách đọc: phần lợi lớn nhất đến từ việc **không tiêu hết ngân sách buổi sáng**; tầng ô thêm khoảng 1% số chuyến, và lợi ích đó đến từ việc **dồn ngân sách** sang giờ khác (θ = 0,5 bớt 57% lượt phát trong 5–9h mà N của 5–9h gần như không đổi), không phải từ việc tránh tác hại. Điều này khớp §2.8: dưới ngân sách, θ\* > 0 ngay cả khi hiệu ứng dương ở mọi mức căng. Hai dòng cuối của bậc thang cho thấy điều §2.8 dự báo: so với điểm `random`, xếp hạng theo **hiệu ứng mỗi USD** thêm 195 chuyến/ngày, hơn gấp đôi phần của heuristic cộng tầng ô (+87,9); xếp hạng theo hiệu ứng mỗi lượt phát thì không hơn ngẫu nhiên.

**Qini so với N (T5.2, tiêu chí nghiệm thu 3).** Qini tính trên `rider_ab_28d` (dữ liệu A/B theo rider, kết cục `completed`, bootstrap 200 lần theo rider); N lấy từ bậc thang trên:

| Hàm điểm | Qini [95% CI] | N dưới B | Session được phát | q0 / q1 của nhóm được phát | Chuyến thêm / 100 USD (A/B, mức cá nhân) |
|---|---|---|---|---|---|
| τ̂(x, s) DR | 1.600,6 [1.090,8; 2.106,8] | 3.780,3 | 14% | 0,234 / 0,320 | 6,4 |
| τ̂(x) DR | 1.055,1 [472,7; 1.707,8] | 3.752,7 | 18% | 0,207 / 0,282 | 6,4 |
| τ̂(x) nền | 862,6 [418,6; 1.313,7] | 3.803,7 | 22% | 0,159 / 0,231 | 7,7 |
| `random` | 59,8 [−154,6; 256,1] | 3.807,0 | 27% | 0,126 / 0,193 | 8,6 |
| τ̂(x, s)/USD DR | −443,8 [−1.140,7; 233,7] | 4.010,3 | 41% | 0,077 / 0,137 | 12,3 |
| τ̂(x)/USD nền | −619,0 [−1.336,3; −2,0] | 4.002,0 | 46% | 0,071 / 0,129 | 12,5 |
| τ̂(x)/USD DR | −756,5 [−1.490,4; −16,3] | 3.989,9 | 45% | 0,073 / 0,129 | 12,1 |
| `heuristic_low_freq` | −985,9 [−1.820,6; −172,2] | 3.860,3 | 39% | 0,089 / 0,142 | 9,5 |

(Bảng đủ 10 hàm điểm và mọi cặp ở `runs/s5/qini_vs_value`. Ba cột cuối: lấy đúng κ của mỗi hàm điểm trong bảng T5.1, coi session có điểm ≥ κ là được phát, rồi đo trên `rider_ab_28d`: q0, q1 là tỷ lệ hoàn thành ở nhóm đối chứng và nhóm được voucher; chi phí = voucher × hoàn thành ở nhóm được voucher.)

Có 28 trên 45 cặp "Qini cao hơn có ý nghĩa mà N thấp hơn có ý nghĩa" (cả với `completed` lẫn `requested`). Lớn nhất: τ̂(x) DR so với τ̂(x, s)/USD DR, Qini +1.498,9 [503,9; 2.562,6], N −257,6 ± 5,2; kết cục `requested` cho cùng thứ tự. Cặp không dính đến điểm /USD: τ̂(x, s) DR so với `random`, Qini +1.540,8 [900,2; 2.111,3], N −26,7 ± 5,3.

**Cơ chế là chi phí, không phải trạng thái cung.** Thứ hạng N dưới B của 10 hàm điểm trùng gần như hoàn toàn với thứ hạng "chuyến thêm / 100 USD" đo ở mức cá nhân trong A/B theo rider (Spearman 0,976), mà thí nghiệm này không có cân bằng thị trường. Voucher mỗi lượt phát gần như bằng nhau giữa các hàm điểm (4,91–5,05 USD), nên khác biệt cũng không nằm ở cỡ voucher. Nó nằm ở chỗ **trả tiền cho chuyến đằng nào cũng có**: voucher chỉ trả khi chuyến hoàn thành, nên chi phí một lượt phát là $v \cdot q_1$ và số chuyến thêm mỗi USD là $(1 - q_0/q_1)/v$ (cùng lập luận với ngưỡng $q_1/q_0 \ge c/(c-r)$ của §1.5). Hàm điểm Qini cao chọn rider hay đi ($q_0$ 0,21–0,23 so với 0,13 trung bình): uplift mỗi lượt phát lớn nhất, nhưng phần lớn tiền trả cho chuyến không tăng thêm. τ̂(x, s) DR còn né hẳn ô căng (slack trung bình của nhóm được phát 5,9; 0,4% ở ô không xe rảnh, so với 19% của mọi session), nhưng vẫn kém `random` vì cùng lý do. Trong thế giới mặc định, **chưa tìm thấy ví dụ đảo thứ tự do trạng thái cung**: phần do cung (đưa s vào điểm /USD, hoặc tầng ô) chỉ cỡ +20 chuyến/ngày, nhỏ hơn một bậc so với phần do chi phí (cỡ 200).

**Chệch thiết kế khi bỏ burn-in (T5.3).** So với GTE +1.212,9: A/B theo rider +35,8%; switchback cụm 1 +34,5%; cụm 7 +23,4%; toàn hệ +4,5% (tính cả burn-in thì +8,2%, tức gần nửa chệch của switchback toàn hệ là carryover đầu block). Trên request chệch nhỏ hơn (+17,6% đến +2,6%), hợp với việc tranh chấp cung tác động lên chuyến hoàn thành qua cả ETA báo lẫn việc giành xe, còn lên request chỉ qua ETA báo.

**Độ nhạy theo `u_latent` (T5.3).** Bốn bộ legacy 28 ngày chỉ khác `target_g_u`. Sau khi điều chỉnh theo đặc trưng quan sát được (trong ô bật, phân tầng phân khúc × thập phân vị tần suất), chệch còn lại so với lát explore là −0,0052 [−0,0134; +0,0032] khi `target_g_u` = 0, rồi +0,021; +0,043; +0,072 khi `target_g_u` = 0,5; 1; 2, trên nền hiệu ứng thật khoảng 0,06–0,07. Không có biến ẩn thì điều chỉnh theo X là đủ; ở mức mặc định (1), ước lượng quan sát phóng đại khoảng 60% dù đã điều chỉnh.

---

## 10. Giả định, hạn chế và việc cần làm để phương pháp chắc hơn

### 10.1 Mức độ chắc của từng phần

| Phần | Mức độ | Căn cứ |
|---|---|---|
| Cơ chế WGC, tranh chấp cung, carryover | **chắc**: tự xuất hiện từ cơ chế, đã kiểm | A1, chệch thiết kế đúng thứ tự, GTE |
| CRN, không nhìn trước, không rò biến ẩn, ngân sách | **chắc**: bất biến có test | §8.1, A2 |
| Hành vi rider (logit), hủy, bỏ chờ | **dạng hợp lý, độ lớn hiệu chỉnh theo 3 số** | CAL (P(đặt), uplift, giá); hủy theo ETA khớp rà soát |
| Độ căng thị trường và hình dạng theo giờ | **giả định** | dải căng/dư của CAL là thiết kế kịch bản (H-23); lệch NYC (H-20) |
| Kết luận về θ\* | **có điều kiện** trên hàm điểm, B, độ căng, một thế giới | H-22, H-23, §10.3 |

### 10.2 Điểm yếu đã biết: đã chốt cách xử lý và còn mở

Đã chốt (Tình và Hoàng, 05/10), còn việc phải làm:

| Quyết định | Vấn đề gốc | Cách xử lý | Việc kéo theo |
|---|---|---|---|
| H-21 (Q24, Q26), **đã cài** | κ từ một lượt pilot ở κ = −∞ đánh giá thấp chi tiêu (chi 1,113 × B khi không chặn; cả 10 seed chạm trần từ khoảng 21:25–22:55, nên π_θ thực thi là "điểm ≥ κ **và** trước ~22h"); pilot riêng theo θ gây nhiễu khoảng 10 chuyến/ngày giữa các θ trong đoạn phẳng | κ là điểm bất động (lặp pilot đến khi chi ≤ B), chung seed pilot cho mọi θ, giữ dừng cứng; test đo thêm "chi khi không chặn / B" và "tỷ lệ voucher bị chặn cứng" | đã cài 05/10 (T-32), B7b chạy lại vào `runs/b7b_h21`; chi khi không dừng cứng còn 0,97–1,02 × B, voucher bị chặn ≤ 1,9% |
| H-22 (Q27) | lợi ích tầng ô là dồn ngân sách, không phải tránh hại; θ\* phụ thuộc hàm điểm; slack theo ô dự báo mức phục vụ kém hơn slack cụm hay toàn hệ (18,0% phương sai ETA báo so với 25,9% và 30,1%) | báo θ\* kèm hàm điểm, B và bậc thang; quét lại θ với hàm điểm học ở S5, ghi trước dự đoán "điểm càng tốt thì θ\* càng gần 0"; chọn ŝ theo khả năng dự báo mức phục vụ trên `all_off`, không dùng N | ŝ chốt là slack vòng 1 (H-25), đã cài thành tùy chọn `scope: ring1` (T-35), mặc định vẫn `cell` cho tới khi hai người quyết; sweep với hàm điểm học được đã chạy: dự đoán đúng (§9) |
| H-23 (Q28) | dải CAL về tỷ lệ căng/dư không có nguồn dữ liệu; nhiều cấu hình cùng đạt CAL; quy mô lợi ích tầng ô đi theo độ căng (regret θ = 0: 1,37% ở chuẩn, 4,10% khi cầu × 1,5) | ghi là thiết kế kịch bản; báo θ\* và regret theo bộ kịch bản khai báo trước (chuẩn; cầu × 1,5; dạng TLC; thiếu xe); không dùng N, θ\*, GTE làm mục tiêu hiệu chỉnh | chạy bộ kịch bản ở S5 |
| H-20 (Q25) | hình dạng cung cầu theo giờ là giả định, lệch NYC; vùng căng 5–8h là hệ quả của lịch ca giả định | giữ nguyên, ghi hạn chế | không |

Còn mở trong `decisions.md`:

| ID | Vấn đề | Ảnh hưởng |
|---|---|---|
| Q19 | chỉ số `utilization`, `eta` chưa cài (hướng so sánh ngược slack) | chỉ phân tích độ nhạy |
| Q18 | rời sớm theo thu nhập chưa cài | chỉ phân tích độ nhạy |

### 10.3 Điểm phát hiện thêm khi viết báo cáo này

Các điểm dưới đây chưa có trong `decisions.md`; nên bàn trước S5.

1. **`forecast: ar` gần như trùng `persistence` trong lượt đánh giá 1 ngày.** `slack_lag_day` là slot k − 96 đếm từ đầu lượt chạy. Lượt `evaluate`/`sweep_theta` chỉ có warm-up 4 slot + 96 slot cửa sổ, nên chỉ 4 slot cuối cửa sổ có giá trị trễ ngày; 92 slot còn lại `ar` quay về persistence (T-23b). H-22 đưa `ar` vào danh sách ứng viên ŝ: muốn so thật thì phải đánh giá trên lượt nhiều ngày (`days_per_run` ≥ 2, chỉ tính từ ngày thứ hai), hoặc cho snapshot trễ ngày từ một lượt chạy trước.
2. **Chọn "tốt nhất" và đo khoảng cách trên cùng một tập seed** (winner's curse). $\hat b = \arg\max$ của trung bình mẫu nên $N(\hat b)$ bị ước lượng cao; regret và gap tới cái tốt nhất vì thế hơi lớn hơn thật. Ở đoạn phẳng, độ chệch này có thể cùng cỡ với chênh lệch giữa các θ (chưa đo). Cách sửa rẻ: chọn $\hat b$ trên một nửa số seed, tính regret và tập θ\* trên nửa còn lại (hoặc trên seed mới). H-21 bỏ được nhiễu κ theo θ nhưng không bỏ được độ chệch này.
3. **Mọi kết quả có điều kiện trên một thế giới** (`world_seed = 20260930`). Trọng số ô, vị trí nhà rider, lịch ca đều rút một lần; θ\* và GTE có thể đổi theo thế giới. Đề xuất: lặp sweep rút gọn (vài θ quanh tập θ\*, 10 seed) trên 3–5 `world_seed` để báo phương sai giữa các thế giới.
4. **Cầu không có trí nhớ.** Session là Poisson độc lập: rider bỏ chờ không đặt lại, chất lượng phục vụ hôm qua không đổi cầu hôm nay, rider có thể mở session mới khi chuyến trước chưa xong (0,70% chuyến hoàn thành). Hệ quả: carryover chỉ đi qua phía cung (vị trí và trạng thái xe), không qua phía cầu. Đây là đơn giản hóa hợp lý cho 5 tuần nhưng phải ghi trong hạn chế, vì nó làm hiệu ứng dài hạn của voucher (giữ chân khách) bằng 0 theo thiết kế.
5. **Thí nghiệm không ngân sách không thấy chi phí cơ hội.** $\hat\theta$ ước lượng từ switchback là điểm hiệu ứng đổi dấu, còn θ\* dưới B là điểm hiệu ứng mỗi USD rơi dưới giá bóng (§2.8). Muốn ước lượng θ\* từ dữ liệu thì phải ước lượng hiệu ứng **mỗi USD** theo ŝ và một mức λ, không chỉ dấu của hiệu ứng. Nên ghi rõ trong định nghĩa $\hat\theta$ của S5.
6. **Tài liệu lệch nhau một chỗ nhỏ:** `docs/tests.md` mục M11 còn ghi "slack `inf` khi E = 0", chưa sửa theo H-14 ("0 nếu I = 0"). Code và `schema.md`, `spec.md` đã đúng.

### 10.4 Đề xuất cho phiên bản 2 của báo cáo

Theo thứ tự ưu tiên:
1. ~~Cài H-21, chạy lại B7b~~ (xong 05/10). ~~Thêm τ̂(x, s) (B8, H5.2) vào bảng T5.1 và cặp τ̂(x)–τ̂(x, s) vào T5.2~~ (xong 05/10).
2. ~~Chốt định nghĩa ŝ theo H-22(iii)~~ (H-25: `ring1`, chọn trên `persistence`; điểm 1 ở §10.3 vẫn còn cho `ar`). Còn: quyết định đổi mặc định sang `ring1`; học lại τ̂(x, s) trên slack vòng 1 (T-35b).
3. Thêm phép tách ba nguồn sai số đúng nghĩa (§7.4) trên cùng quần thể session.
4. ~~Thêm kết quả S5: τ̂(x), τ̂(x, s) từ DR-learner; bảng N/V dưới cùng B; ví dụ Qini cao hơn mà N thấp hơn~~ (xong 05/10, §9). Còn: tìm một kịch bản (thiếu xe, cầu × 1,5) mà phần do cung đủ lớn để đảo thứ tự Qini so với N.
5. Lặp các kết quả chính trên nhiều `world_seed` và trên bộ kịch bản khai báo trước (chuẩn; cầu × 1,5; thiếu xe; dạng TLC).

---

## 11. Thuật ngữ và ký hiệu

| Thuật ngữ | Nghĩa trong simulator |
|---|---|
| Session | một lần rider mở app và nhận báo giá; có thể không thành đơn |
| Order | một yêu cầu đặt xe; `order_id = session_id` |
| ETA báo / ETA đón | ETA hiển thị lúc báo giá (bước 5) / ETA thật khi được ghép (bước 7) |
| $I, E, O, W$ | xe rảnh, xe đang đi đón, xe đang chở, đơn đang chờ (trung bình theo tick trong slot) |
| Slack | $I/E$; 0 khi không có xe rảnh; $+\infty$ khi có xe rảnh mà không xe nào đi đón |
| ŝ (`slack_hat`) | slack dự báo cho slot hiện tại từ snapshot đã công bố |
| θ | ngưỡng tầng ô: tắt khuyến mãi khi ŝ < θ |
| κ | ngưỡng tầng rider: phát khi điểm ≥ κ |
| B | ngân sách voucher mỗi kỳ (mỗi ngày của cửa sổ đánh giá) |
| N(π), V(π) | số chuyến hoàn thành / lợi nhuận nền tảng của đơn đặt trong cửa sổ |
| θ\* | θ tốt nhất theo N dưới cùng B; báo là tập vì đường có đoạn phẳng |
| θ̂ | ngưỡng ước lượng từ dữ liệu |
| Regret | N(π tốt nhất) − N(π_θ̂) |
| GTE | N(all_on) − N(all_off), không ngân sách |
| CRN | số ngẫu nhiên chung giữa các chính sách |
| WGC | wild goose chase: thiếu xe rảnh → ghép xa → xe bận lâu → càng thiếu |
| Propensity | xác suất session được phát voucher; `cell_propensity` ở cấp (ô, slot) |
| Explore | lát 5% session của chính sách cũ được gán bằng đồng xu 0,5 |
| Warm-up / burn-in / cool-down | giờ đầu lượt chạy bỏ khỏi đánh giá / 15 phút đầu mỗi block switchback bỏ khi ước lượng / thời gian chạy thêm sau cửa sổ |
| Truncated | đơn chưa kết thúc khi hết cool-down |

---

## 12. Tài liệu tham khảo và vai trò trong simulator

| Tài liệu | Dùng cho |
|---|---|
| Blake & Coey (2014), EC '14 | trực giác chệch do tranh chấp trong thí nghiệm marketplace (§2.1) |
| Castillo, Knoepfle & Weyl (2025), Management Science | WGC, slack và ngưỡng 0,25–0,45, ETA $c(A/I)^\gamma$, first dispatch, hủy tăng khi slack giảm, `max_wait` mode 5 phút (§2.2, M1, M5, M7, M11) |
| Johari, Peng & Xing (2026), arXiv 2506.05308 | logit theo giá và ETA, tách session/order, block 60 phút, đánh giá chính sách bằng lượt chạy toàn hệ (M4, M10, M13) |
| Johari, Li, Liskovich & Weintraub (2022), Management Science | độ chệch thiết kế trên nền tảng hai phía (§2.1, §2.7) |
| Hu & Wager (2022), arXiv 2209.00197 | switchback, burn-in, carryover (§2.7) |
| Bojinov, Simchi-Levi & Zhao (2023), Management Science | thiết kế và phân tích switchback (§2.7) |
| Holtz et al. (2025), Management Science | cluster randomization, chệch theo kích thước cụm (§2.7) |
| Kennedy (2023), Electronic Journal of Statistics | DR-learner, điều kiện overlap (§2.6) |
| Zhao & Harinen (2019), DSAA | phân bổ dưới ràng buộc chi phí, Qini (§2.8, §2.10) |
| Athey & Wager (2021), Econometrica | học chính sách từ dữ liệu quan sát (§2.8) |
| Yadlowsky et al. (2025), JASA | Qini/RATE chỉ đo khả năng xếp hạng (§2.10) |
| Lin et al. (2018), KDD | lưới lục giác, ghép ưu tiên không gian, xe đứng yên hoặc sang ô kề (M1, M5, M9) |
| Feng et al. (2024), Communications in Transportation Research | vòng lặp tick, sinh cầu Poisson, vòng đời đơn (§3) |
| Engelhardt et al. (2022), FleetPy | bảng thời gian thay tính đường, lấy mẫu 10% (M1, bản NYC) |
| Yao & Bekhor (2024), J. Intelligent Transportation Systems | hủy sau ghép khi thời gian đón dài; xe rảnh tại chỗ (M7) |
| Künzel et al. (2019), PNAS; Gutierrez & Gérardy (2017) | meta-learner, uplift (dùng ở `analysis/`, S5) |

---

## Phụ lục A. Tham số mặc định

Nguồn: `config/default.yaml`, `config_hash = 92b7d13adc39` (thêm `policy.threshold.kappa_max_iter = 10` và `policy.threshold.scope = cell` so với `cb27f5348011`).

| Nhóm | Khóa | Giá trị | Nguồn | Vai trò |
|---|---|---|---|---|
| Không gian | `grid_radius`, `torus` | 3, true | [report] | 37 ô, không có biên |
| | `edge_km` | 0,75 | [report] | diện tích ô 1,461 km² |
| | `detour_factor` | 1,3 | [assume] | đường thực / đường chim bay |
| | `nn_const`, `eta_gamma` | 0,5; 0,5 | [paper] | ETA trong ô (§2.3) |
| | `eta_floor_min` | 1,0 | [assume] | ETA tối thiểu |
| | `base_speed_kmh` | 18 | [data] | ~11,4 mph Manhattan |
| | `speed_factor_by_hour` | 0,75–1,25 | [assume] | chậm nhất 8h, 17h, 18h |
| Thời gian | `tick_s`, `slot_min` | 60; 15 | [report] | |
| | `warmup_min`, `cooldown_max_min` | 60; 120 | [report] | |
| Cầu | `base_sessions_per_cell_h` × `demand_scale` | 35 × 0,85 | [assume], [P3] | ~25.650 session/ngày |
| | `cell_weight_sigma` | 0,5 | [assume] | độ lệch cầu giữa các ô |
| | `hour_profile` | 0,20–1,85 | [assume] | hai đỉnh 8h, 18h |
| | `dest_decay_rings` | 3,0 | [assume] | chuyến ngắn có xác suất cao hơn |
| | `n_riders`, `home_cell_share` | 20.000; 0,8 | [assume] | |
| | `trip_time_noise_sigma` | 0,15 | [assume] | |
| Rider | `alpha0`, `alpha_freq`, `alpha_u` | 0,35; 0,4; 0,4 | [P3], [assume] | xu hướng đặt nền; `alpha_u` tạo gây nhiễu |
| | `beta_price_per_usd`, `beta_price_seg_mult` | 0,10; (1,0; 1,6; 0,6) | [assume] | nhạy giá |
| | `beta_eta_per_min` | 0,10 | [assume] | nhạy ETA |
| | `delta0`, `delta_u`, `delta_seg` | 0,25; 0,10; (0; 0,15; −0,10) | [P3], [assume] | phản ứng riêng với voucher |
| | `max_wait_mode_min`, `max_wait_sigma` | 5,0; 0,5 | [paper], [assume] | kiên nhẫn chờ ghép |
| Giá | `base_fare_usd`, `per_min_usd` | 3,0; 1,70 | [assume], [P3] | giá TB 19,0 USD |
| | `commission_rate` | 0,24 | [data] | tài xế nhận 76% |
| Voucher | `pct_of_fare` | 0,20 | [data] | |
| Ngân sách | `fraction` | 0,30 | [assume] | B = 5.545,80 USD/kỳ |
| Chính sách cũ | `slack_on`, `epsilon_cell` | 0,6; 0,10 | [assume], [report] | |
| | `target_g0`, `target_g_freq`, `target_g_u` | −0,5; −0,5; 1,0 | [assume] | nhắm theo biến ẩn |
| | `explore_frac`, `explore_p` | 0,05; 0,5 | [report] | lát RCT |
| π_θ | `theta`, `forecast`, `hysteresis_h` | 0,35; persistence; 0 | | |
| | `score_fn`, `kappa` | heuristic_low_freq; auto | | |
| Ghép | `max_pickup_eta_min`, `max_ring` | 30; null | [report] | không chặn WGC |
| Hủy | `base_per_min`, `slope_per_min2`, `eta_free_min` | 0,005; 0,004; 3,0 | [assume] | §2.5 |
| Cung | `fleet_size` | 240 | [P3] | trung bình 80,75 xe trong ca |
| | `shift_len_mean_h`, `sd`, `clip` | 8; 1,5; [4; 11] | [assume] | |
| | `early_exit_enabled` | false | [report] | cung độc lập chính sách |
| Điều chuyển | `mode`, `max_idle_min` | static_weights; 10 | [assume] | |
| Thí nghiệm | `block_min`, `burnin_min`, `p_on` | 60; 15; 0,5 | [paper] | |
| Monitor | `slack_cap` | 10 | | thay +∞ khi dự báo `ar` |

## Phụ lục B. Bản đồ khái niệm → code → test

| Khái niệm | Code | Test |
|---|---|---|
| Lưới, torus, $T$, ETA | `sim/space.py` | `tests/test_space.py` |
| Thế giới, rider, lịch ca | `sim/population.py` | `tests/test_demand.py`, `tests/test_supply.py` |
| Sinh cầu, rút sẵn | `sim/demand.py`, `sim/rng.py` | `tests/test_demand.py`, `tests/test_rng.py` |
| Giá, voucher, lớp voucher | `sim/pricing.py` | `tests/test_pricing.py` |
| Sổ ngân sách, B | `sim/budget.py`, `runner.calibrate_budget` | `tests/test_pricing.py`, `tests/test_acceptance.py` |
| Logit đặt xe, ground truth | `sim/choice.py` | `tests/test_choice.py` |
| Ghép đơn | `sim/matching.py` | `tests/test_matching.py` |
| Chuyến, thanh toán, hủy | `sim/trips.py`, `sim/cancel.py` | `tests/test_trips_cancel.py` |
| Ca làm, điều chuyển | `sim/supply.py`, `sim/reposition.py` | `tests/test_supply.py` |
| Cụm, block, switchback | `sim/experiment.py`, `sim/policies/experiment.py` | `tests/test_experiment.py` |
| Slack, snapshot, không nhìn trước | `sim/monitor.py`, `sim/policies/base.py` | `tests/test_monitor.py` |
| Chính sách cũ, π_θ, hàm điểm | `sim/policies/legacy.py`, `threshold.py`, `scores.py` | `tests/test_policies.py` |
| κ auto | `runner.kappa_auto`, `kappa_from_pilot` | `tests/test_runner.py`, `tests/test_acceptance.py` |
| Vòng lặp 10 bước | `sim/engine.py` | `tests/test_engine.py`, `tests/test_integration.py` |
| Ghi dữ liệu, tách ẩn | `sim/logger.py` | `tests/test_logger.py`, `tests/test_schema_contract.py` |
| A1, A5, CAL | `runner.run_throughput_curve` | `tests/test_acceptance_core.py` (slow) |
| A2, A3, κ auto | | `tests/test_acceptance.py` (slow) |
| A4, ước lượng switchback | `analysis/estimate.py` | `tests/test_estimate.py` |
| Tập θ\*, regret, Qini | `analysis/metrics.py` | `tests/test_analysis.py` |
