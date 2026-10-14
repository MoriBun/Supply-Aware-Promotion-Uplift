---
title Supply-Aware Promotion Uplift
date 2026-09-22
---

# bài toán voucher dưới ràng buộc cung

## Câu chuyện bắt đầu từ một bảng quyết định

Bộ phận vận hành có một quy tắc nghe rất hợp lý nếu promotion làm request tăng mà
supply gap và ETA xấu đi thì thu hẹp promotion ở zone và khung giờ đó. Không ai cãi
được trực giác này. Nhưng khi ta hỏi xấu đi bao nhiêu thì nên tắt hay tắt sai
ngưỡng thì mất bao nhiêu tiền, câu trả lời chỉ còn là kinh nghiệm.

Mức căng cung  utilization  ETA gốc (phút)  $tau_{request}$  $tau_{completed}$ 
---------------
 rất thừa cung  0.65  2.5  +57%  +58% 
 cân bằng  1.41  3.1  +38%  +32% 
 rất căng  3.05  9.3  +19%  +1.9% 

Hàng cuối là toàn bộ đề tài thu nhỏ. Voucher vẫn kéo thêm gần một phần năm request,
nhưng số chuyến hoàn thành gần như đứng yên, vì không còn tài xế để phục vụ. Đề bài
còn kể thêm hai con số khiến bức tranh rối hơn lát randomized 5% cho thấy voucher
tăng chuyến hoàn thành 44%, nhưng khi bật cho toàn hệ thì chỉ còn khoảng 20%. Còn
phân tích observational ngây thơ thì nói voucher gần như không có tác dụng (+1%).

Ba con số, ba câu trả lời khác nhau cho cùng một câu hỏi. Tài liệu này đi tìm những
paper giải thích vì sao chúng khác nhau, rồi xem có dữ liệu và mã nguồn công khai
nào giúp ta đo được chúng hay không.

Ta sẽ đi theo hướng xoáy ốc. Bắt đầu từ cách làm ngây thơ nhất là mô hình uplift
chuẩn, cho nó chạy trên ví dụ trên và xem nó gãy ở đâu. Chỗ gãy đầu tiên là
confounding, chỗ thứ hai là interference, chỗ thứ ba là giới hạn công suất và vòng
lặp wild goose chase. Mỗi chỗ gãy dẫn ta tới một nhóm paper. Cuối cùng ta quay về câu
hỏi đánh giá nếu Qini có thể nói dối, ta tin vào cái gì

## Bước ngây thơ uplift như thể mỗi rider sống một mình

Cách đơn giản nhất là coi voucher như một loại thuốc. Mỗi rider có một hiệu ứng
riêng $tau(x)$, ta học nó từ dữ liệu, rồi phát voucher cho những người có $tau$
cao nhất. Đây chính là thế giới của uplift modeling và của ước lượng hiệu ứng không
đồng nhất (heterogeneous treatment effect, HTE).

Bài nền của thế giới này là Künzel, Sekhon, Bickel & Yu (2019), Metalearners for
estimating heterogeneous treatment effects using machine learning (PNAS 1164156).
Ý tưởng của các meta-learner rất gần với trực giác. S-learner huấn luyện một mô hình
duy nhất với treatment là một feature, T-learner huấn luyện hai mô hình riêng cho
nhóm có và không có voucher rồi lấy hiệu, còn X-learner đi thêm một bước dùng mô
hình của nhóm này để đoán kết quả phản thực (counterfactual) cho nhóm kia, nhờ vậy
làm tốt hơn khi hai nhóm lệch cỡ nhau. Lệch cỡ là đúng tình huống của ta, vì lát
randomized chỉ chiếm 5%.

Đề bài yêu cầu dùng DR-learner ở tuần 2, và bài gốc của nó là Kennedy (2023),
Towards optimal doubly robust estimation of heterogeneous causal effects
(Electronic Journal of Statistics 17(2)3008). DR-learner không hồi quy thẳng lên
outcome mà lên một pseudo-outcome kép vững (doubly robust)

$$
tilde{Y} = mu_1(X) - mu_0(X) + frac{T - e(X)}{e(X),(1 - e(X))},bigl(Y - mu_T(X)bigr)
$$

Ta cùng đọc công thức này. Hai số hạng đầu là dự đoán hiệu ứng từ mô hình outcome;
nếu mô hình đó hoàn hảo thì ta dừng ở đây. Số hạng thứ ba là phần sửa sai lấy phần
dư $Y - mu_T(X)$ của chính người này, rồi phóng lên theo nghịch đảo xác suất nhận
voucher $e(X)$. Nếu mô hình outcome sai nhưng propensity đúng, phần sửa sai kéo ước
lượng về đúng; nếu propensity sai nhưng mô hình outcome đúng, phần dư có kỳ vọng
bằng không và không làm hỏng gì. Đó là nghĩa của kép vững chỉ cần đúng một trong
hai là đủ.

Hai tài liệu còn lại của tầng này là để tra cứu. Gutierrez & Gérardy (2017)
(PMLR 67) là bài review nối cộng đồng uplift với cộng đồng HTE, và Zhang, Li & Liu
(2021) (ACM Computing Surveys 54(8)) thống nhất ký hiệu giữa hai cộng đồng vốn gọi
cùng một thứ bằng tên khác nhau.

Bây giờ cho bước ngây thơ này chạy trên ví dụ của ta. Nếu học $tau(x)$ trên toàn bộ
dữ liệu observational, ta được con số +1% và kết luận voucher vô dụng. Nếu chỉ học
trên lát randomized, ta được +44% và kết luận voucher tuyệt vời. Cả hai đều sai, và
chúng sai vì hai lý do khác nhau. Ta xử lý từng lý do một.

## Chỗ gãy thứ nhất legacy rule phát voucher đúng vào nơi thiếu cung

Vì sao observational cho +1% Vì quy tắc phát voucher cũ ưu tiên những zone hay
thiếu cung. Ở đó conversion vốn thấp sẵn, nên nhóm có voucher trông kém hơn nhóm
không có, và hiệu ứng thật bị che mất. Đây là confounding kinh điển. Về nguyên tắc,
DR-learner với propensity đúng sẽ gỡ được nó, miễn là mọi biến gây nhiễu đều quan sát
được.

Miễn là chính là chỗ nguy hiểm, vì simulator cố tình giấu biến `u_latent`. Ta cần
một cách hỏi một biến ẩn phải mạnh đến đâu thì mới lật ngược được kết luận. Bài
trả lời gọn nhất là Cinelli & Hazlett (2020), Making sense of sensitivity
extending omitted variable bias (JRSS-B 82(1)39). Thay vì giả định dạng phân phối
cho biến ẩn, họ đo độ mạnh của nó bằng partial $R^2$ với treatment và với outcome, rồi
so với một biến quan sát được làm mốc. Ví dụ biến ẩn phải giải thích treatment mạnh
gấp ba lần `freq` thì hiệu ứng mới về không. Đây là thứ dùng được ngay cho câu hỏi
sensitivity ở tuần 4. Cần lưu ý rằng khung này dựng cho hồi quy tuyến tính, nên áp vào
DR-learner phi tuyến chỉ là phép xấp xỉ.

Khi đã có $hattau(x)$ và cần biến nó thành một chính sách phát voucher dưới ngân
sách, bài nền là Athey & Wager (2021), Policy learning with observational data
(Econometrica 89(1)133). Họ dùng chính các điểm số doubly robust ở trên để chấm điểm
trực tiếp từng chính sách, thay vì chỉ xếp hạng $hattau$, và cho phép ràng buộc
ngân sách hoặc dạng chính sách đơn giản. Bài này nằm ở ranh giới phạm vi đề bài cấm
đọc lý thuyết Double Machine Learning, nên chỉ nên đọc phần đặt vấn đề và phần phương
pháp, bỏ phần chứng minh.

Như vậy chỗ gãy thứ nhất có thuốc. Nhưng kể cả khi confounding đã được gỡ hoàn toàn,
ta vẫn còn con số +44% của lát randomized, cao gấp đôi con số +20% khi bật toàn hệ.
Lát randomized không có confounding, vậy phần chênh đến từ đâu

## Chỗ gãy thứ hai rider không sống một mình

Hãy tưởng tượng một zone có mười tài xế rảnh và năm mươi rider. Ta phát voucher cho
năm rider ngẫu nhiên. Năm người đó đặt xe nhiều hơn và chiếm mất vài tài xế, nên
những rider không có voucher phải chờ lâu hơn và một số bỏ đi. Khi so nhóm có voucher
với nhóm không có, ta đang đo hai thứ cộng lại phần voucher thật sự tạo thêm chuyến,
và phần chuyến bị giành từ nhóm đối chứng. Phần thứ hai không tồn tại khi bật voucher
cho tất cả mọi người, vì lúc đó không còn ai để giành. Giả định bị phá có tên là
SUTVA (stable unit treatment value assumption) kết quả của một người không phụ thuộc
vào việc người khác có được can thiệp hay không.

Bài bắt buộc đọc đầu tiên của đề tài, Blake & Coey (2014), Why marketplace
experimentation is harder than it seems the role of test-control interference (EC
'14), phân tích đúng loại bài toán này trên một chiến dịch email của eBay và thấy ước
lượng bị phóng đại khoảng gấp đôi. Điểm đáng giá nhất của bài là khung cung cầu rất
đơn giản độ chệch càng lớn khi cung càng kém co giãn. Trong ví dụ của ta, cung kém co
giãn nhất ở hàng rất căng, và đó cũng là nơi ta nên kỳ vọng AB cấp user nói dối
nhiều nhất.

Từ đó, một dòng nghiên cứu mô hình hoá độ chệch này một cách định lượng.
Johari, Li, Liskovich & Weintraub, Experimental design in two-sided platforms an
analysis of bias (arXiv 2002.05670), dựng mô hình thị trường mà ở đó có thể so sánh
randomize phía khách hàng hay phía nhà cung cấp. Kết luận đáng nhớ ở thị trường bị
chặn bởi cầu thì randomize theo khách hàng không chệch, còn ở thị trường bị chặn bởi
cung thì chính cách đó lại chệch. Lát randomized 5% của ta là randomize theo rider,
tức phía khách hàng, nên nó sẽ chệch nhiều nhất ở đúng những cell thiếu cung. Bài cũng
đề xuất randomize đồng thời cả hai phía để giảm chệch ở mọi trạng thái cân bằng. Bài
tiếp nối của Li, Zhao, Johari & Weintraub (2022), Interference, bias, and
variance in two-sided marketplace experimentation guidance for platforms (WWW '22),
đưa thêm phương sai vào bài toán và hỏi nên chia bao nhiêu phần trăm vào treatment.
Hai bài này giải thích vì sao tham số `explore_frac` trong `SimConfig` đáng thử nghiệm.

Một cách tiếp cận khác là không tránh interference mà dùng mô hình cân bằng để hiệu
chỉnh nó. Wager & Xu (2021), Experimenting in equilibrium (Management Science
67(11)6694), đề xuất các nhiễu ngẫu nhiên rất nhỏ trên từng đơn vị cộng với mô hình
mean-field của thị trường, để ước lượng tác động của một thay đổi nhỏ mà hệ vẫn ở
trạng thái cân bằng. Munro, Wager & Xu (2025), Treatment effects in market
equilibrium (American Economic Review 115(10)3273), tách hiệu ứng thành phần trực
tiếp và phần lan toả qua giá cân bằng. Kết quả quan trọng cho ta là một thí nghiệm
Bernoulli vẫn ước lượng đúng được phần trực tiếp và mức độ không đồng nhất, nhưng muốn
biết phần lan toả thì phải có thêm độ co giãn giá. Hai bài này nặng toán; với 5 tuần,
chỉ nên đọc phần giới thiệu để có ngôn ngữ nói về hiệu ứng trực tiếp và hiệu ứng lan
toả.

Góc nhìn gần với vận hành nhất đến từ Lyft. Ido Bright, Arthur Delarue & Ilan Lobel, Reducing
marketplace interference bias via shadow prices (arXiv 2205.02274, Management
Science), lấy biến đối ngẫu (shadow price) của bài toán ghép tài xế và rider làm giá
trị biên của mỗi tài xế, rồi trừ phần giá trị lấy từ nhóm đối chứng ra khỏi hiệu ứng
đo được. Bài blog đi kèm của Lyft cho hai con số đáng nhớ 10% thí nghiệm đổi quyết
định sau khi hiệu chỉnh, và khi kết quả hiệu chỉnh thấp hơn thì trung bình thấp hơn
45%. Cách này đặc biệt hợp với ta, vì simulator đã có sẵn hàm `market_clear` độ dốc
của throughput theo số tài xế chính là một shadow price.

Cuối cùng là con số thực nghiệm từ Airbnb. Holtz, Lobel, Lobel, Liskovich & Aral
(2025), Reducing interference bias in online marketplace experiments using cluster
randomization (Management Science 71(1)390), chạy một meta-experiment ngẫu nhiên
hoá chính thiết kế thí nghiệm một nửa randomize theo listing, một nửa theo cụm
listing. Tóm tắt tìm được cho biết ít nhất khoảng 20% ước lượng cấp listing là do
interference, còn đề bài nói độ chệch có thể lớn bằng GTE. Hai con số này cần được
đối chiếu lại trong PDF khi ingest.

Nhìn lại, ta đã hiểu vì sao +44% lại thành +20% một nửa hiệu ứng của lát randomized
là chuyến giành từ nhóm đối chứng. Nhưng câu chuyện chưa hết. Hàng rất căng trong
bảng cho thấy uplift gần như bằng không, và đề bài còn nói nó có thể âm. Interference
đơn thuần chỉ làm số đo phình lên, nó không làm cho voucher gây hại. Cần một cơ chế
khác.

## Chỗ gãy thứ ba khi cầu tăng làm throughput giảm

Cơ chế đó là wild goose chase. Castillo, Knoepfle & Weyl (2025), Matching and
pricing in ride hailing wild goose chases and how to solve them (Management Science
71(5)4377), mô tả một vòng lặp dương. Khi tài xế rảnh quá ít, hệ thống phải ghép
những cặp ở xa nhau. Thời gian đón dài ra, mỗi tài xế bị chiếm lâu hơn cho mỗi chuyến,
nên số tài xế rảnh càng ít đi, và thời gian đón lại càng dài. Ở vùng này, thêm cầu làm
giảm số chuyến hoàn thành. Nhóm tác giả cho thấy tăng giá (hoặc surge) là cách đưa
cầu về vùng an toàn. Với ta, điều này có nghĩa là voucher, vốn là một cách giảm giá,
đẩy hệ thống theo đúng chiều ngược lại.

Script `codeplot_uplift_supply.py` viết cơ chế này thành một phương trình

$$
tau_{completed} approx frac{dQ}{dD}cdot Delta D
$$

Ở đây $Delta D$ là lượng cầu tăng thêm nhờ voucher, đo bằng độ co giãn của rider, còn
$dQdD$ là độ dốc của hàm throughput thêm một request thì được thêm bao nhiêu chuyến
hoàn thành. Khi thừa cung, độ dốc gần bằng 1 và mọi request tăng thêm đều thành chuyến.
Khi chạm công suất, độ dốc về 0. Trong vùng wild goose chase, độ dốc âm. So với bảng
ban đầu $tau_{request}$ ở hàng rất căng vẫn là +19%, tức $Delta D$ vẫn dương,
nhưng $tau_{completed}$ chỉ còn +1.9% vì $dQdD$ đã về gần 0. Phương trình này cũng
cho ta một định nghĩa hình thức cho ngưỡng `util` của RQ1 đó là điểm mà $dQdD$ đổi
dấu.

Muốn hiểu hình dạng của hàm throughput $Q$, ta cần hàm ghép cặp (matching function).
Yang & Yang (2011), Equilibrium properties of taxi markets with search frictions
(Transportation Research Part B 45(4)696), và Zha, Yin & Yang (2016), Economic
analysis of ride-sourcing markets (Transportation Research Part C 71249), đều dùng
hàm Cobb-Douglas số lần ghép được tỷ lệ với tích luỹ thừa của số khách chờ và số xe
rảnh. Đề bài đã cảnh báo trước rằng dạng hàm này mất hiệu lực khi cung thiếu hụt, tức
đúng vùng ta quan tâm. Vì vậy hai bài này có giá trị như điểm xuất phát để so với
simulator, không phải như mô hình để dùng.

Còn một bài có trong bản đề bài cũ nhưng bị bỏ ở bản mới Zhu, Ke & Wang (2021), A
mean-field Markov decision process model for spatial-temporal subsidies in
ride-sourcing markets (Transportation Research Part B 150540). Bài này xem trợ giá
là một bài toán quyết định tuần tự và dùng học tăng cường, nên nằm ngoài phạm vi 5
tuần. Nó chỉ đáng mở nếu đến tuần 4 còn thời gian và muốn biết bài toán lớn hơn trông
ra sao.

## Đo cho đúng nếu không chia theo user thì chia theo gì

Chỗ gãy thứ hai dạy ta rằng AB cấp user không đáng tin cho quyết định rollout. Vậy
thiết kế nào đáng tin hơn Câu trả lời trong ngành là switchback bật và tắt can thiệp
cho cả một zone theo từng khung thời gian, để trong mỗi khung mọi người cùng một chế
độ.

Chamandy (2016), Experimentation in a ridesharing marketplace (Lyft Engineering
blog), là cách vào dễ nhất vì được viết từ góc nhìn người vận hành. Bài hình thức hoá
là Bojinov, Simchi-Levi & Zhao (2023), Design and analysis of switchback
experiments (Management Science, arXiv 2009.00148). Nhưng switchback có cái giá của
nó trạng thái của khung trước tràn sang khung sau. Nếu khung có voucher đã vét sạch
tài xế rảnh, khung đối chứng tiếp theo bắt đầu trong tình trạng thiếu cung, và trông
tệ hơn thực tế. Hu & Wager, Switchback experiments under geometric mixing (arXiv
2209.00197), định lượng hiện tượng này khi có carryover, sai số của switchback chuẩn
chỉ giảm theo $T^{-13}$ thay vì $T^{-12}$, và việc bỏ đi một đoạn đầu mỗi khung
(burn-in) đưa tốc độ gần về lại $T^{-12}$. Ta nhận ra chính các cột `_lag` của
simulator cũng là một dạng carryover trạng thái hôm trước ảnh hưởng tới hôm nay.

Ở mức nâng cao hơn, Farias, Li, Peng & Zheng (2022), Markovian interference in
experiments (NeurIPS '22), xét trường hợp can thiệp lên một đơn vị ảnh hưởng đơn vị
khác qua một ràng buộc dùng chung như số tài xế. Họ đề xuất ước lượng Differences-in-Q,
có độ chệch bậc hai theo cỡ can thiệp và phương sai nhỏ hơn nhiều so với đánh giá
off-policy. Bài này được thử trên một simulator gọi xe cỡ thành phố, mô phỏng Manhattan
với khoảng 300 nghìn request mỗi ngày. Nó nằm ngoài phạm vi vì dựa trên lý thuyết học
tăng cường, nhưng là tham chiếu tốt nếu nhóm muốn so simulator của mình với một
simulator cỡ lớn.

## Đánh giá chính sách khi Qini nói dối

Bây giờ ta quay về tiêu chí nghiệm thu quan trọng nhất tìm một ví dụ mà chính sách B
có Qini cao hơn chính sách C nhưng giá trị chính sách thật $V(pi)$ lại thấp hơn. Để
biết vì sao điều đó xảy ra được, ta cần hiểu Qini thực sự đo cái gì.

Nguồn chuẩn cho Qini và cho phần tối ưu chi phí là Zhao & Harinen (2019), Uplift
modeling for multiple treatments with cost optimization (DSAA). Nhưng cách nhìn rõ
nhất về bản chất của Qini đến từ Yadlowsky, Fleming, Shah, Brunskill & Wager (2025),
Evaluating treatment prioritization rules via rank-weighted average treatment effects
(JASA 120(549)). Họ chỉ ra Qini là một thành viên của họ chỉ số RATE nó chấm điểm một
quy tắc xếp hạng theo việc những người được xếp đầu có hiệu ứng trung bình cao đến đâu.
Và hiệu ứng ở đây là hiệu ứng cá nhân dưới SUTVA.

Đó chính là mấu chốt. Qini đo khả năng xếp hạng $tau$ cá nhân, trong khi đề bài nhấn
mạnh rằng ở marketplace không tồn tại $tau$ cá nhân ground truth, chỉ có $V(pi)$. Một
chính sách có thể xếp hạng rất giỏi những rider có $tau_{request}$ cao, và vì vậy có
Qini đẹp, nhưng nếu những rider đó tập trung ở hàng rất căng thì chuyến hoàn thành
thêm gần như bằng không. Tệ hơn, họ còn làm ETA của người khác dài ra. Bài mới của
Yang, Liu & Huang (2026), Evaluating uplift modeling under structural biases
(arXiv 2603.20775), đi đến kết luận gần với điều này bằng thực nghiệm bán mô phỏng
khi dữ liệu có selection bias và spillover, những chỉ số càng gần ATE thì càng cho
thứ hạng mô hình ổn định. Bài này mới và chưa qua phản biện, nên chỉ dùng làm bằng
chứng phụ.

Về phân bổ dưới ngân sách, có vài bài từ công nghiệp LBCF (A large-scale
budget-constrained causal forest algorithm, Ai et al.), bài của Uber Direct
heterogeneous causal learning for resource allocation problems in marketing (arXiv
2211.15728), và End-to-end cost-effective incentive recommendation under budget
constraint with uplift modeling (RecSys '24, arXiv 2408.11623). Tất cả đều giả định
SUTVA. Chúng hữu ích như baseline greedy theo $hattau$ không biết cung trong bảng
so sánh chính sách, không phải như lời giải. Đề bài cũng loại trừ rõ decision-focused
learning, nên không cần đi sâu vào hướng này.

Ta cũng tìm được vài bài gần đây cố gắng đưa interference vào uplift, như
Direct profit estimation using uplift modeling under clustered network interference
(van den Akker, workshop CONSEQUENCES @ RecSys 2025, arXiv 2509.01558) và CanniUplift
(arXiv 2607.05242) về cannibalization giữa các shop. Đây là những bài workshop hoặc
preprint, chưa phải nền tảng. Điều đáng chú ý là chúng xác nhận khoảng trống mà đề
tài nhắm tới uplift có tính tới trạng thái cung trong gọi xe vẫn chưa có tài liệu
chuẩn.

Việc thứ hai là hiệu chỉnh simulator để các phân phối của nó trông giống thật hơn.
Ở đây dữ liệu vận hành gọi xe có ích

- NYC TLC High Volume FHV trip records (Uber, Lyft từ 2019). Theo data dictionary,
  mỗi chuyến có `request_datetime`, `pickup_datetime`, `PULocationID` và giá. Hiệu
  `pickup_datetime - request_datetime` gộp theo taxi zone và giờ là một đại diện cho
  thời gian chờ, từ đó suy ra phân phối độ căng cung theo zone, giờ. Hạn chế chỉ có
  chuyến đã hoàn thành, không có request bị huỷ, nên không đo trực tiếp được tỷ lệ
  hoàn thành. `on_scene_datetime` chỉ có cho xe hỗ trợ xe lăn.
- Chicago Transportation Network Providers trips trên cổng dữ liệu mở của thành
  phố, cùng repo `toddwschneiderchicago-taxi-data` để nhập dữ liệu. Chưa kiểm tra các
  trường cụ thể.
- DiDi GAIA, Thành Đô 112016 và bộ công cụ KDD Cup 2020 (Learning to
  dispatch and reposition). Theo mô tả của cuộc thi, dữ liệu được bổ sung xác suất huỷ
  theo khoảng cách đón. Đây là đúng thứ cần để hiệu chỉnh tham số `b_cancel_eta` của
  simulator. Truy cập phải đăng ký qua GAIA và hiện chưa rõ còn mở hay không.

Đề bài đã loại trừ dữ liệu công ty, và mọi kết luận vẫn phải kèm trong mô phỏng này.

## Mã nguồn thư viện thì đủ, simulator thì không ai làm hộ

Về thư viện, hệ sinh thái Python đã có đủ cho mọi bước của lộ trình

- `ubercausalml` `BaseDRRegressor` và các meta-learner khác, module `metrics` có
  Qini và AUUC, module `feature_selection`. Đây là thư viện đề bài chỉ định.
- `py-whyEconML` (Microsoft) DR-learner, causal forest, và
  `DRPolicyTree``DRPolicyForest` cho policy learning kiểu Athey và Wager. Nên dùng để
  đối chiếu kết quả với CausalML.
- `maks-shscikit-uplift` các hàm tải dữ liệu ở bảng trên, cùng các hàm vẽ và
  metric uplift gọn nhẹ.
- `grf-labsgrf` (R) causal forest và hàm RATE của Yadlowsky et al. Chỉ cần đến
  nếu muốn có khoảng tin cậy cho Qini.
- `py-whydowhy` khung khai báo đồ thị nhân quả và các phép kiểm tra phản bác.
  Hữu ích để viết rõ ra vì sao `realized_` là collider.
- `nlapier2PySensemakr` bản Python của `sensemakr` (Cinelli và Hazlett) cho phân
  tích sensitivity với `u_latent`.

Về simulator gọi xe, ta tìm thấy vài dự án mã nguồn mở `Leot6AMoD2` (mô phỏng
mobility-on-demand dung lượng lớn với ba thuật toán điều phối),
`marina-haliemDynamic-RideSharing-Pooling-Simulator` (ghép cặp, định giá, điều phối
có đi chung) và `liiliiliilride-hailing-platform-with-simulator` (ghép cặp đồ thị
hai phía bằng thuật toán KM), cùng bộ khởi đầu `mktalkddcup-starting-kit` của KDD Cup
2020. Tất cả đều là mô phỏng theo từng tác tử (agent-based), nặng hơn nhiều và tập
trung vào điều phối, không có khái niệm voucher phía rider, không sinh dữ liệu
observational có confounding, và không tính $V(pi)$. Simulator Manhattan của Farias et
al. là cái gần nhất về mục đích (thí nghiệm có interference), nhưng ta không tìm thấy
đường dẫn mã nguồn công khai trong bài báo hay trang cá nhân của tác giả.

## Đọc gì trước, đọc gì sau

Ghép lại, ta có một thứ tự đọc bám sát lộ trình 5 tuần. Những bài không có trong đề bài
được đánh dấu mở rộng.

 Tuần  Bài  Trả lời  Ghi chú 
------------
 1  Blake & Coey 2014  RQ3  bắt buộc, đọc kỹ 
 1  Künzel et al. 2019; Gutierrez & Gérardy 2017  nền  
 1  Chamandy 2016 (blog)  trực giác  
 1  Castillo, Knoepfle & Weyl 2025  RQ1  chỉ phần cơ chế 
 2  Kennedy 2023  RQ1, RQ2  mở rộng, bài gốc của DR-learner 
 2  Zhao & Harinen 2019  tiêu chí 3  
 2  Yadlowsky et al. 2025 (RATE)  tiêu chí 3  mở rộng, giải thích Qini đo gì 
 2  Bojinov et al. 2023; Holtz et al. 2025  RQ3  
 3  Bright, Delarue & Lobel + blog Lyft MMV  RQ1, RQ3  mở rộng, shadow price từ `market_clear` 
 3  Yang & Yang 2011; Zha, Yin & Yang 2016  RQ1  chỉ mục matching function 
 4  Athey & Wager 2021  RQ2  mở rộng, bỏ chứng minh 
 4  Cinelli & Hazlett 2020  sensitivity  mở rộng 
 tuỳ  Li et al. 2022; Johari et al.; Hu & Wager  RQ3  mở rộng, nếu làm thí nghiệm `explore_frac` 
 tuỳ  Wager & Xu 2021; Munro, Wager & Xu 2025; Farias et al. 2022  RQ3  mở rộng, chỉ đọc phần giới thiệu 

Còn một câu hỏi bỏ ngỏ đáng ghi lại. Nếu ngưỡng `util` là điểm $dQdD$ đổi dấu, và
shadow price của Bright et al. chính là một ước lượng của $dQdD$, thì ta có hai cách
độc lập để ước lượng ngưỡng một từ đường cong uplift học từ dữ liệu, một từ cấu trúc
của `market_clear`. Hai con số có khớp nhau không, và nếu lệch thì lệch vì đâu Đó có
thể là một kết quả phụ đẹp cho báo cáo.

## Nguồn

Papers
[Blake & Coey 2014](httpsdl.acm.orgdoi10.11452600057.2602837) ·
[Künzel et al. 2019](httpswww.pnas.orgdoi10.1073pnas.1804597116) ·
[Kennedy 2023](httpsarxiv.orgabs2004.14497) ·
[Athey & Wager 2021](httpsonlinelibrary.wiley.comdoiabs10.3982ECTA15732) ·
[Cinelli & Hazlett 2020](httpsacademic.oup.comjrsssbarticle-abstract821397056023) ·
[Johari et al.](httpsarxiv.orgabs2002.05670) ·
[Li et al. 2022](httpsarxiv.orgabs2104.12222) ·
[Wager & Xu 2021](httpsarxiv.orgabs1903.02124) ·
[Munro, Wager & Xu 2025](httpsarxiv.orgabs2109.11647) ·
[Bright et al.](httpsarxiv.orgabs2205.02274) ·
[Holtz et al. 2025](httpspubsonline.informs.orgdoi10.1287mnsc.2020.01157) ·
[Castillo et al.](httpspapers.ssrn.comsol3papers.cfmabstract_id=2890666) ·
[Zha, Yin & Yang 2016](httpswww.sciencedirect.comsciencearticleabspiiS0968090X16301188) ·
[Zhu, Ke & Wang 2021](httpswww.sciencedirect.comsciencearticleabspiiS0191261521001259) ·
[Bojinov et al. 2023](httpsarxiv.orgabs2009.00148) ·
[Hu & Wager](httpsarxiv.orgabs2209.00197) ·
[Farias et al. 2022](httpsarxiv.orgabs2206.02371) ·
[Yadlowsky et al. 2025](httpsarxiv.orgabs2111.07966) ·
[Yang, Liu & Huang 2026](httpsarxiv.orgabs2603.20775) ·
[LBCF](httpswww.semanticscholar.orgpaperca6428ceff99f7df0bcf67c91f588c2a3ee8f12a) ·
[Uber DHCL](httpsarxiv.orgabs2211.15728) ·
[E³IR](httpsarxiv.orgabs2408.11623) ·
[van den Akker 2025](httpsarxiv.orgabs2509.01558) ·
[CanniUplift](httpsarxiv.orgabs2607.05242)

Blog
[Lyft — Marketplace marginal values](httpseng.lyft.comusing-marketplace-marginal-values-to-address-interference-bias-a11aff6e670f) ·
[Lyft — Chamandy 2016](httpseng.lyft.comexperimentation-in-a-ridesharing-marketplace-f75a9c4fcf01) ·
[DoorDash — switchback rigor](httpscareersatdoordash.comblogexperiment-rigor-for-switchback-experiment-analysis)

Dữ liệu
[scikit-uplift datasets](httpswww.uplift-modeling.comenlatestapidatasetsindex.html) ·
[Criteo Uplift](httpsailab.criteo.comcriteo-uplift-prediction-dataset) ·
[NYC TLC trip records](httpswww.nyc.govsitetlcabouttlc-trip-record-data.page) ·
[HVFHV data dictionary](httpswww.nyc.govassetstlcdownloadspdfdata_dictionary_trip_records_hvfhs.pdf) ·
[Chicago taxiTNP importer](httpsgithub.comtoddwschneiderchicago-taxi-data) ·
[KDD Cup 2020 DiDi](httpswww.biendata.xyzcompetitionkdd_didi)

Code
[causalml](httpsgithub.comubercausalml) ·
[EconML](httpsgithub.compy-whyEconML) ·
[scikit-uplift](httpsgithub.commaks-shscikit-uplift) ·
[grf](httpsgithub.comgrf-labsgrf) ·
[DoWhy](httpsgithub.compy-whydowhy) ·
[PySensemakr](httpsgithub.comnlapier2PySensemakr) ·
[AMoD2](httpsgithub.comLeot6AMoD2) ·
[DRSP-Sim](httpsgithub.commarina-haliemDynamic-RideSharing-Pooling-Simulator) ·
[ride-hailing-platform-with-simulator](httpsgithub.comliiliiliilride-hailing-platform-with-simulator) ·
[kddcup-starting-kit](httpsgithub.commktalkddcup-starting-kit)