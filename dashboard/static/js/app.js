// App shell: sidebar navigation (hash routes), run selector, theme toggle, polling of the run list.
import { html, React, ReactDOM, useState, useEffect, useMemo, useApi, useLocalStorage } from "./lib.js";
import { OverviewPage, RunPage, MapPage, CellsPage, DistributionPage, ResultsPage } from "./pages.js";

const ROUTES = [
  ["overview", "Tổng quan"], ["run", "Mô phỏng"], ["map", "Bản đồ động"], ["cells", "Vùng & ngưỡng θ"],
  ["distribution", "Phân phát voucher"], ["results", "Kết quả thực nghiệm"],
];
const TITLES = {
  overview: "Tổng quan lượt chạy", run: "Chạy mô phỏng", map: "Bản đồ động: xe, khách, voucher theo từng phút",
  cells: "Tầng ô: ŝ, ngưỡng θ và các ô bị cắt", distribution: "Tầng rider: phân phát voucher và ngân sách",
  results: "Kết quả thực nghiệm đã lưu trong runs/",
};
const isRunning = (r) => r && !["done", "error"].includes(r.status);

/** Hash route ``#/page?run=<id>``: the page name and the optional run id of the link. */
function useHashRoute() {
  const read = () => {
    const [path, query] = location.hash.replace(/^#\/?/, "").split("?");
    const params = new URLSearchParams(query || "");
    return { route: path || "overview", runParam: params.get("run") };
  };
  const [state, setState] = useState(read);
  useEffect(() => { const h = () => setState(read()); window.addEventListener("hashchange", h); return () => window.removeEventListener("hashchange", h); }, []);
  return state;
}

function App() {
  const { route, runParam } = useHashRoute();
  const [theme, setTheme] = useLocalStorage("theme", "auto");
  useEffect(() => { if (theme === "auto") document.documentElement.removeAttribute("data-theme"); else document.documentElement.setAttribute("data-theme", theme); }, [theme]);
  const [selectedId, setSelectedId] = useLocalStorage("run.selected", null);
  const runsQ = useApi("/api/runs", [], { poll: 2500 });
  const runs = (runsQ.data && runsQ.data.runs) || [];
  const anyRunning = runs.some(isRunning);
  useEffect(() => { if (runParam && runParam !== selectedId) setSelectedId(runParam); }, [runParam]);
  useEffect(() => {
    if (!runs.length) return;
    if (!selectedId || !runs.some((r) => r.id === selectedId)) {
      const done = runs.find((r) => r.status === "done") || runs[0];
      if (done) setSelectedId(done.id);
    }
  }, [runs, selectedId]);
  const listed = runs.find((r) => r.id === selectedId);
  const running = isRunning(listed);
  const detailQ = useApi(selectedId ? `/api/runs/${selectedId}` : null, [listed && listed.status], { poll: running ? 1000 : 0 });
  const run = detailQ.data && detailQ.data.id === selectedId ? detailQ.data : null;
  const defaultsQ = useApi("/api/config/defaults");
  const onStarted = (id) => { setSelectedId(id); runsQ.reload(); };
  const page = (() => {
    switch (route) {
      case "run": return html`<${RunPage} defaults=${defaultsQ.data} runs=${runs} run=${run} onStarted=${onStarted} onSelect=${setSelectedId} />`;
      case "map": return html`<${MapPage} run=${run} />`;
      case "cells": return html`<${CellsPage} run=${run} />`;
      case "distribution": return html`<${DistributionPage} run=${run} />`;
      case "results": return html`<${ResultsPage} />`;
      default: return html`<${OverviewPage} run=${run} runs=${runs} onSelect=${setSelectedId} />`;
    }
  })();
  return html`<div className="shell">
    <aside className="sidebar">
      <div className="brand"><div className="title">Supply-Aware Promotion</div><div className="sub">simulator gọi xe · bảng điều khiển</div></div>
      <nav className="nav">${ROUTES.map(([key, label], i) => html`<a key=${key} href=${"#/" + key} className=${route === key ? "active" : ""}><span className="num">${i + 1}</span>${label}</a>`)}</nav>
      <div className="spacer"></div>
      <div className="small muted" style=${{ padding: "0 8px" }}>
        ${anyRunning ? html`<div><span className="status running">đang chạy</span></div>` : null}
        <div style=${{ marginTop: 6 }}>Giao diện: <div className="seg" style=${{ marginLeft: 4 }}>${[["auto", "tự động"], ["light", "sáng"], ["dark", "tối"]].map(([t, l]) => html`<button key=${t} className=${theme === t ? "on" : ""} onClick=${() => setTheme(t)}>${l}</button>`)}</div></div>
        <div style=${{ marginTop: 8 }}>Mã nguồn: <code>dashboard/</code> · spec: <code>docs/spec.md</code></div>
      </div>
    </aside>
    <main className="main">
      <div className="topbar">
        <h1>${TITLES[route] || "Bảng điều khiển"}</h1>
        <label className="field" style=${{ minWidth: 260 }}><span>Lượt chạy đang xem</span>
          <select value=${selectedId || ""} onChange=${(e) => setSelectedId(e.target.value || null)}>
            ${runs.length ? null : html`<option value="">(chưa có lượt chạy)</option>`}
            ${runs.map((r) => html`<option key=${r.id} value=${r.id}>${r.name} · ${r.status}${r.kpis ? ` · N=${r.kpis.N_completed}` : ""}</option>`)}
          </select></label>
      </div>
      ${runsQ.error ? html`<div className="card err">Không gọi được API: ${runsQ.error}</div>` : null}
      ${page}
    </main>
  </div>`;
}

ReactDOM.createRoot(document.getElementById("root")).render(html`<${App} />`);
