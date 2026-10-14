// App shell, grouped navigation, selected experiment and API state.
import { html, React, ReactDOM, useState, useEffect, useApi, useLocalStorage, fmtInt } from "./lib.js";
import { OverviewPage, RunPage, MapPage, CellsPage, DistributionPage, ResultsPage } from "./pages.js";
import { SweepPage } from "./sweep.js";
import { Icon, BrandMark } from "./ui.js";
import { isRunning, STATUS_VI } from "./common.js";

const GROUPS = [
  { label: "KHÔNG GIAN NGHIÊN CỨU", items: [["overview", "Tổng quan"], ["results", "Kết quả & đối chiếu"]] },
  { label: "THIẾT KẾ THỰC NGHIỆM", items: [["sweep", "Tìm ngưỡng tối ưu θ*"], ["run", "Chạy mô phỏng"]] },
  { label: "PHÂN TÍCH VẬN HÀNH", items: [["map", "Bản đồ thị trường"], ["cells", "Cung & chính sách vùng"], ["distribution", "Voucher & ngân sách"]] },
];
const META = {
  overview: ["Tổng quan nghiên cứu", "Theo dõi hiệu quả khuyến mãi trong điều kiện cung hữu hạn."],
  sweep: ["Tìm ngưỡng tối ưu θ*", "So sánh nhiều θ và seed, chọn ngưỡng theo số chuyến hoàn thành."],
  run: ["Thiết kế lượt mô phỏng", "Cấu hình thị trường, chính sách và ngân sách cho một lượt chạy."],
  map: ["Bản đồ thị trường", "Quan sát tài xế, nhu cầu và trạng thái voucher theo thời gian mô phỏng."],
  cells: ["Cung & chính sách vùng", "Đối chiếu dự báo cung trễ với quyết định bật, tắt khuyến mãi."],
  distribution: ["Voucher & ngân sách", "Theo dõi phân bổ voucher, đối tượng nhận và sổ ngân sách."],
  results: ["Kết quả & đối chiếu", "Đánh giá chính sách, ngưỡng θ và hiệu ứng ở cấp thị trường."],
};
function useHashRoute() {
  const read = () => {
    const [path, query] = location.hash.replace(/^#\/?/, "").split("?");
    const params = Object.fromEntries(new URLSearchParams(query || "").entries());
    return { route: Object.hasOwn(META, path) ? path : "overview", runParam: params.run || null, params };
  };
  const [state, setState] = useState(read);
  useEffect(() => { const h = () => setState(read()); window.addEventListener("hashchange", h); return () => window.removeEventListener("hashchange", h); }, []);
  return state;
}
function App() {
  const { route, runParam, params } = useHashRoute();
  const [theme, setTheme] = useLocalStorage("theme", "light");
  const [sidebarCollapsed, setSidebarCollapsed] = useLocalStorage("sidebar.collapsed", false);
  useEffect(() => { if (theme === "auto") document.documentElement.removeAttribute("data-theme"); else document.documentElement.setAttribute("data-theme", theme); }, [theme]);
  const [selectedId, setSelectedId] = useLocalStorage("run.selected", null);
  const runsQ = useApi("/api/runs", [], { poll: 2500 });
  const runs = runsQ.data?.runs || [];
  const activeCount = runs.filter(isRunning).length;
  useEffect(() => { if (runParam && runParam !== selectedId) setSelectedId(runParam); }, [runParam]);
  useEffect(() => {
    if (!runs.length) return;
    if (!selectedId || !runs.some((r) => r.id === selectedId)) setSelectedId((runs.find((r) => r.status === "done") || runs[0]).id);
  }, [runs, selectedId]);
  useEffect(() => { document.title = `${META[route][0]} · Xanh SM Analytics`; window.scrollTo(0, 0); }, [route]);
  const listed = runs.find((r) => r.id === selectedId);
  const detailQ = useApi(selectedId ? `/api/runs/${selectedId}` : null, [listed?.status], { poll: isRunning(listed) ? 1000 : 0 });
  const run = detailQ.data?.id === selectedId ? detailQ.data : null;
  const defaultsQ = useApi("/api/config/defaults");
  const onStarted = (id) => { setSelectedId(id); runsQ.reload(); };
  const page = (() => {
    switch (route) {
      case "run": return html`<${RunPage} defaults=${defaultsQ.data} runs=${runs} run=${run} onStarted=${onStarted} onSelect=${setSelectedId} params=${params} />`;
      case "sweep": return html`<${SweepPage} defaults=${defaultsQ.data} runs=${runs} run=${run} onStarted=${onStarted} onSelect=${setSelectedId} />`;
      case "map": return html`<${MapPage} run=${run} />`;
      case "cells": return html`<${CellsPage} run=${run} />`;
      case "distribution": return html`<${DistributionPage} run=${run} />`;
      case "results": return html`<${ResultsPage} />`;
      default: return html`<${OverviewPage} run=${run} runs=${runs} defaults=${defaultsQ.data} loading=${runsQ.loading || detailQ.loading} onSelect=${setSelectedId} />`;
    }
  })();
  return html`<div className=${"shell" + (sidebarCollapsed ? " sidebar-collapsed" : "")}>
    <a className="skip-link" href="#main-content">Đến nội dung chính</a>
    <aside className="sidebar">
      <div className="brand-row"><a className="brand" href="#/overview" aria-label="Xanh SM Analytics · Tổng quan"><${BrandMark} /><span className="brand-caption">PROMOTION ANALYTICS</span></a><button className="sidebar-collapse" type="button" aria-label=${sidebarCollapsed ? "Mở rộng thanh điều hướng" : "Thu gọn thanh điều hướng"} aria-expanded=${!sidebarCollapsed} title=${sidebarCollapsed ? "Mở rộng thanh điều hướng" : "Thu gọn thanh điều hướng"} onClick=${() => setSidebarCollapsed(!sidebarCollapsed)}><${Icon} name="collapse" size=${17} /><span className="sr-only">${sidebarCollapsed ? "Mở rộng thanh điều hướng" : "Thu gọn thanh điều hướng"}</span></button></div>
      <div className="workspace-label"><span className="workspace-dot"></span> Phòng thí nghiệm mô phỏng</div>
      <nav className="nav" aria-label="Điều hướng chính">${GROUPS.map((group) => html`<div className="nav-group" key=${group.label}><div className="nav-label">${group.label}</div>${group.items.map(([key, label]) => html`<a key=${key} href=${"#/" + key} title=${label} aria-label=${label} aria-current=${route === key ? "page" : undefined} className=${route === key ? "active" : ""}><${Icon} name=${key} /><span>${label}</span>${route === key ? html`<span className="active-dot"></span>` : null}</a>`)}</div>`)}</nav>
      <div className="spacer"></div>
      <div className="sidebar-purpose"><${Icon} name="info" /><div><b>Mục tiêu chiến lược</b><p>Tối đa số chuyến hoàn thành<br />dưới ngân sách voucher B.</p></div></div>
      <div className="theme-control"><span>Giao diện</span><div className="seg" role="group" aria-label="Chế độ giao diện">${[["light", "Sáng"], ["dark", "Tối"], ["auto", "Tự động"]].map(([t, l]) => html`<button key=${t} aria-pressed=${theme === t} className=${theme === t ? "on" : ""} onClick=${() => setTheme(t)}>${l}</button>`)}</div></div>
      <div className="sidebar-foot">Xanh SM (GSM) · VinAI</div>
    </aside>
    <main className="main" id="main-content" tabIndex="-1">
      <header className="topbar"><div className="breadcrumb">Hệ thống phân tích Xanh SM <span>/</span> <b>${META[route][0]}</b></div><div className="connection"><span className=${"connection-dot" + (runsQ.error ? " offline" : "")}></span>${runsQ.error ? "Mất kết nối API" : runsQ.loading ? "Đang kết nối" : activeCount ? `${activeCount} thực nghiệm đang chạy` : "Hệ thống đã sẵn sàng"}<span className="environment">Dữ liệu mô phỏng</span></div></header>
      <div className="page-heading"><div><div className="eyebrow">XANH SM / PHÂN TÍCH KHUYẾN MÃI</div><h1>${META[route][0]}</h1><p>${META[route][1]}</p></div><a className="btn primary" href="#/run"><${Icon} name="run" size=${15} /> Tạo lượt chạy</a></div>
      <div className="experiment-bar"><div className="experiment-picker"><${Icon} name="results" /><label className="field"><span>Thực nghiệm đang xem</span><select aria-label="Thực nghiệm đang xem" value=${selectedId || ""} onChange=${(e) => setSelectedId(e.target.value || null)}>${!runs.length ? html`<option value="">Chưa có lượt chạy</option>` : null}${runs.map((r) => html`<option key=${r.id} value=${r.id}>${r.kind === "sweep" ? "[Quét θ] " : ""}${r.name} · ${STATUS_VI[r.status] || r.status}</option>`)}</select></label></div><div className="experiment-meta"><span><b>${fmtInt(runs.filter((r) => r.status === "done").length)}</b> lượt hoàn tất</span><span className="chip">${listed?.kind === "sweep" ? "Nhiều θ × seed" : "Một chính sách × seed"}</span><button className="btn icon" title="Làm mới danh sách lượt chạy" aria-label="Làm mới danh sách lượt chạy" onClick=${() => { runsQ.reload(); detailQ.reload(); }}><${Icon} name="refresh" size=${16} /></button></div></div>
      ${runsQ.error || detailQ.error || defaultsQ.error ? html`<div className="card err" role="alert">Không tải được dữ liệu: ${runsQ.error || detailQ.error || defaultsQ.error}<button className="btn sm" onClick=${() => { runsQ.reload(); detailQ.reload(); defaultsQ.reload(); }}>Thử lại</button></div>` : null}
      <div className="page-content">${page}</div>
      <footer className="main-footer"><span>Xanh SM (GSM) · Supply-Aware Promotion Uplift Platform</span><span>Mô phỏng đa tác tử (ABM) · N(π) là chỉ tiêu chính</span></footer>
    </main>
  </div>`;
}
ReactDOM.createRoot(document.getElementById("root")).render(html`<${App} />`);
