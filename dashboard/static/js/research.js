// Existing artifacts grouped by research question; presence is not proof of a conclusion.
import { html } from "./lib.js";
import { Icon, SectionHead } from "./ui.js";
export function ResearchEvidence({ sweeps, policies, throughput, gte }) {
  const cards = [
    { rq: "RQ1", title: "Uplift thay đổi theo độ căng cung?", body: "Đọc đường throughput, cung trễ và ngưỡng θ. θ* của sweep tối ưu giá trị chính sách; không đồng nhất với điểm τ_completed = 0.", ready: throughput.length > 0 || sweeps.length > 0, target: "evidence-capacity", count: `${throughput.length} đường công suất · ${sweeps.length} lượt quét` },
    { rq: "RQ2", title: "Chính sách biết cung tốt hơn bao nhiêu?", body: "So N(π), ΔN và SE theo seed dưới cùng B. Đối chiếu Qini với giá trị chính sách để đánh giá thứ hạng mô hình.", ready: policies.length > 0, target: "evidence-policies", count: `${policies.length} bảng chính sách` },
    { rq: "RQ3", title: "Đánh giá sai lệch do đâu?", body: "Đối chiếu GTE với rider A/B, switchback và confounding; thác nước ba nguồn sai số và burn-in ở notebook 03, gây nhiễu ở notebook 05.", ready: gte.length > 0, target: "evidence-gte", count: `${gte.length} bảng GTE` },
  ];
  return html`<section><${SectionHead} eyebrow="ĐỐI CHIẾU VỚI ĐỀ TÀI" title="Ba câu hỏi nghiên cứu" description="Trạng thái cho biết có dữ liệu đã lưu; cần đọc từng thực nghiệm để đánh giá mức độ đủ để kết luận." /><div className="grid cols-3 research-cards">${cards.map((card) => html`<button className="card research-card" key=${card.rq} onClick=${() => document.getElementById(card.target)?.scrollIntoView({ block: "start" })}><div className="row between"><span className="rq-label">${card.rq}</span><span className=${"evidence-status" + (card.ready ? " available" : "")}>${card.ready ? "Có dữ liệu" : "Chưa có dữ liệu"}</span></div><h3>${card.title}</h3><p>${card.body}</p><div className="research-card-footer"><span>${card.count}</span><${Icon} name="arrow" size=${16} /></div></button>`)}</div></section>`;
}
