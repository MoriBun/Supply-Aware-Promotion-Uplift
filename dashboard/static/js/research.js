// Existing artifacts grouped by research question; presence is not proof of a conclusion.
import { html, useState } from "./lib.js";
import { Icon, SectionHead } from "./ui.js";
const TOPICS = [["all", "Tất cả"], ["01", "Thị trường & công suất"], ["02", "Chính sách & Qini"], ["03", "Interference"], ["04", "Uplift & ngưỡng"], ["05", "Confounding"]];
const TITLES = {
  "01_thi_truong_theo_gio.png": "Cung & cầu theo giờ", "01_throughput.png": "Giới hạn công suất thị trường",
  "02_n_duoi_b.png": "Giá trị chính sách dưới cùng B", "02_n_theo_theta.png": "Chuyến hoàn thành theo ngưỡng θ", "02_qini_va_n.png": "Qini so với giá trị chính sách",
  "03_chech_thiet_ke.png": "Độ chệch theo thiết kế thí nghiệm", "03_chech_u_latent.png": "Độ chệch khi thay đổi nhiễu ẩn",
  "04_chon_s_hat.png": "Lựa chọn chỉ số dự báo cung", "04_duong_loi_ich_theta_hat.png": "Lợi ích dự báo theo θ̂", "04_n_duoi_b_theo_diem.png": "So sánh hàm điểm rider",
  "04_n_theo_theta_ring1.png": "Đường N(θ) với phạm vi ring1", "04_regret_theta_hat.png": "Regret của ngưỡng ước lượng", "04_switchback_theo_gio.png": "Hiệu ứng switchback theo giờ",
  "04_tac_hai_bat_tat_toan_bo.png": "Tác động bật voucher toàn thị trường", "04_tau_x_theo_rider.png": "Uplift ước lượng theo rider", "04_ti_le_cat_theo_gio.png": "Tỷ lệ cắt khuyến mãi theo giờ",
  "05_co_che_u_latent.png": "Cơ chế confounding ẩn", "05_do_nhay_u_latent.png": "Độ nhạy với confounder ẩn", "05_tach_do_lech.png": "Phân rã độ lệch quan sát", "05_uoc_luong_legacy.png": "Ước lượng trên dữ liệu legacy",
};
export function ResearchEvidence({ sweeps, policies, throughput, gte, figures }) {
  const has = (prefix) => figures.some((f) => f.name.startsWith(prefix));
  const cards = [
    { rq: "RQ1", title: "Uplift thay đổi theo độ căng cung?", body: "Đọc đường throughput, cung trễ và ngưỡng θ. θ* của sweep tối ưu giá trị chính sách; không đồng nhất với điểm τ_completed = 0.", ready: throughput.length > 0 || has("04_"), target: "evidence-capacity", count: `${throughput.length} đường công suất · ${sweeps.length} lượt quét` },
    { rq: "RQ2", title: "Chính sách biết cung tốt hơn bao nhiêu?", body: "So N(π), ΔN và SE theo seed dưới cùng B. Đối chiếu Qini với giá trị chính sách để đánh giá thứ hạng mô hình.", ready: policies.length > 0, target: "evidence-policies", count: `${policies.length} bảng chính sách` },
    { rq: "RQ3", title: "Đánh giá sai lệch do đâu?", body: "Đối chiếu GTE, rider A/B, switchback và confounding. Các hình notebook chứa phân tích chi tiết đã lưu.", ready: gte.length > 0 || has("03_") || has("05_"), target: "evidence-figures", count: `${gte.length} bảng GTE · ${figures.filter((f) => /^(03|05)_/.test(f.name)).length} hình sai lệch` },
  ];
  return html`<section><${SectionHead} eyebrow="ĐỐI CHIẾU VỚI ĐỀ TÀI" title="Ba câu hỏi nghiên cứu" description="Trạng thái cho biết có dữ liệu đã lưu; cần đọc từng thực nghiệm để đánh giá mức độ đủ để kết luận." /><div className="grid cols-3 research-cards">${cards.map((card) => html`<button className="card research-card" key=${card.rq} onClick=${() => document.getElementById(card.target)?.scrollIntoView({ block: "start" })}><div className="row between"><span className="rq-label">${card.rq}</span><span className=${"evidence-status" + (card.ready ? " available" : "")}>${card.ready ? "Có dữ liệu" : "Chưa có dữ liệu"}</span></div><h3>${card.title}</h3><p>${card.body}</p><div className="research-card-footer"><span>${card.count}</span><${Icon} name="arrow" size=${16} /></div></button>`)}</div></section>`;
}
export function FigureGallery({ figures }) {
  const [topic, setTopic] = useState("all");
  const shown = figures.filter((f) => topic === "all" || f.name.startsWith(topic + "_"));
  return html`<section className="card" id="evidence-figures"><${SectionHead} eyebrow="BẰNG CHỨNG TỪ NOTEBOOK" title="Hình & phân tích nghiên cứu" description="Hình đã xuất từ notebook, giữ nguyên dữ liệu và phương pháp của thực nghiệm gốc." /><div className="row figure-tabs" role="group" aria-label="Lọc hình theo chủ đề">${TOPICS.map(([key, label]) => html`<button className=${"btn sm" + (topic === key ? " primary" : "")} aria-pressed=${topic === key} key=${key} onClick=${() => setTopic(key)}>${label}</button>`)}</div>${shown.length ? html`<div className="figure-grid">${shown.map((f) => { const title = TITLES[f.name] || f.name; return html`<figure key=${f.name}><a href=${f.url} target="_blank" rel="noopener noreferrer" aria-label=${`Mở hình ${title}`}><img src=${f.url} alt=${title} loading="lazy" /></a><figcaption><b>${title}</b><p>${TOPICS.find(([key]) => f.name.startsWith(key + "_"))?.[1] || "Phân tích nghiên cứu"} · Kết quả trong mô phỏng</p><span>${f.name}</span></figcaption></figure>`; })}</div>` : html`<div className="empty">Chưa có hình cho chủ đề này. Chạy notebook tương ứng để xuất hình nghiên cứu.</div>`}</section>`;
}
