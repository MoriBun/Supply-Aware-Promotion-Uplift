// The six pages. Each receives the selected run (detail of /api/runs/{id}) and fetches what it needs.
import { html, useState, useEffect, useRef, useMemo, api, useApi, useLocalStorage, useWidth, cssVar, clamp, sum,
  fmtInt, fmtNum, fmtUSD, fmtPct, fmtSigned, fmtClock, fmtHM, fmtDur, compact, driverColors, DRIVER_LABEL, SEQ, seqColor,
  ORDER_STATUS } from "./lib.js";
import { LineChart, BarChart, Heatmap, StatTile, Meter, Table, Legend } from "./charts.js";
import { HexMap, MapLegend, useFrames, usePlayer } from "./hexmap.js";

const isRunning = (r) => r && !["done", "error"].includes(r.status);
const S = (i) => cssVar(`--s${i}`);
const STATUS_VI = { queued: "xếp hàng", loading: "nạp config", budget: "pilot ngân sách B", kappa: "κ auto", simulating: "đang mô phỏng", writing: "ghi bảng", done: "xong", error: "lỗi" };

function StatusPill({ status }) {
  const cls = status === "done" ? "done" : status === "error" ? "error" : "running";
  return html`<span className=${"status " + cls}>${STATUS_VI[status] || status}</span>`;
}

function NoRun({ children }) {
  return html`<div className="card"><div className="empty">${children || "Chưa chọn lượt chạy. Vào trang \"Mô phỏng\" để chạy một lượt, hoặc chọn một lượt ở thanh trên."}</div></div>`;
}

function kappaText(run) {
  if (!run || run.policy !== "threshold") return "–";
  if (run.kappa == null) return "−∞ (không hạn chế)";
  return fmtNum(run.kappa, 3);
}

function RunChips({ run }) {
  if (!run) return null;
  const cfg = run.config || {};
  return html`<div className="row" style=${{ gap: 6 }}>
    <span className="chip">chính sách <b>${run.policy}</b></span>
    ${run.policy === "threshold" ? html`<span className="chip">θ <b>${fmtNum(run.theta, 2)}</b></span><span className="chip">ŝ theo <b>${run.scope}</b></span><span className="chip">điểm <b>${run.score_fn}</b></span><span className="chip">κ <b>${kappaText(run)}</b>${run.kappa_pilots ? html` <span className="muted">(${run.kappa_pilots} pilot)</span>` : null}</span>` : null}
    <span className="chip">B <b>${run.budget_usd == null ? "không áp" : fmtUSD(run.budget_usd, 2) + "/kỳ"}</b></span>
    ${cfg.supply ? html`<span className="chip">xe <b>${cfg.supply.fleet_size}</b></span>` : null}
    ${cfg.space ? html`<span className="chip">ô <b>${3 * cfg.space.grid_radius ** 2 + 3 * cfg.space.grid_radius + 1}</b></span>` : null}
    ${cfg.demand ? html`<span className="chip">cầu ×<b>${cfg.demand.demand_scale}</b></span>` : null}
    ${cfg.meta ? html`<span className="chip">seed <b>${cfg.meta.run_seed}</b></span>` : null}
    ${run.config_hash ? html`<span className="chip">config <b>${run.config_hash}</b></span>` : null}
  </div>`;
}

// ---------------------------------------------------------------------------
// 1. Overview
// ---------------------------------------------------------------------------
export function OverviewPage({ run, runs, onSelect, go }) {
  const sumQ = useApi(run && run.status === "done" ? `/api/runs/${run.id}/summary` : null, [run && run.id]);
  const s = sumQ.data;
  const k = run && run.kpis;
  const clock = run && run.clock;
  const slotCharts = useMemo(() => {
    if (!s || !s.slot_series) return null;
    const ss = s.slot_series;
    const x = ss.t_start.map((t) => t / 3600);
    const win = clock ? [{ x0: clock.window_start_s / 3600, x1: clock.window_end_s / 3600 }] : [];
    return { x, win, ss };
  }, [s, clock]);
  return html`<div className="stack">
    <div className="card">
      <div className="card-head"><h2>Thực nghiệm này đo gì</h2><span className="hint">spec §0–§1, D1–D3</span></div>
      <div className="grid cols-3">
        <div className="note"><b>1. Ngân sách B</b> cố định cho mọi chính sách: B = fraction × chi tiêu của pilot <code>all_on</code> không ngân sách (mặc định 0,3). Bất biến sổ cái: đã chi + đã giữ + đang giữ ≤ B mỗi kỳ.</div>
        <div className="note"><b>2. Tầng ô (cắt vùng):</b> đầu mỗi slot 15 phút, chính sách π<sub>θ</sub> dự báo độ dư cung ŝ = xe rảnh / xe đang đi đón từ snapshot slot trước (không nhìn trước). Ô có ŝ ${"<"} θ bị <b>tắt voucher</b>: cung căng thì khuyến mãi chỉ kéo thêm hủy và chờ.</div>
        <div className="note"><b>3. Tầng rider (phân phát):</b> trong ô đang bật, session có điểm τ̂ ≥ κ được phát voucher 20 % cước; κ hiệu chỉnh tự động bằng pilot để chi tiêu kỳ vọng ≈ B. Chỉ tiêu chính <b>N(π)</b> = số chuyến hoàn thành trong cửa sổ.</div>
      </div>
    </div>
    ${!run ? html`<${NoRun} />` : html`
      <div className="card">
        <div className="card-head"><h2>${run.name} <${StatusPill} status=${run.status} /></h2><span className="hint">${run.created_at ? run.created_at.replace("T", " ").slice(0, 16) : ""}</span></div>
        <${RunChips} run=${run} />
        ${isRunning(run) ? html`<p style=${{ marginTop: 10 }} className="ink2">${run.message} · <a href="#/run">theo dõi tiến độ</a> · <a href="#/map">xem bản đồ trực tiếp</a></p>` : null}
        ${run.error ? html`<p className="err">${run.error}</p>` : null}
      </div>
      ${k ? html`<div className="grid cols-6">
        <${StatTile} hero label="N(π): chuyến hoàn thành trong cửa sổ" value=${fmtInt(k.N_completed)} sub=${`${fmtNum(k.completed_per_h, 1)} chuyến/giờ · ${fmtInt(k.n_requests)} lượt đặt`} />
        <${StatTile} label="V(π): lợi nhuận nền tảng" value=${compact(k.V_profit_usd) + " USD"} sub="phụ; voucher làm V giảm" />
        <${StatTile} label="Chi voucher / ngân sách" value=${k.spent_share_of_budget == null ? fmtUSD(k.voucher_spent_usd) : fmtPct(k.spent_share_of_budget, 1)} sub=${k.budget_B_usd == null ? "không áp B" : `${fmtUSD(k.voucher_spent_usd, 0)} / ${fmtUSD(k.budget_B_usd * (clock ? clock.n_periods : 1), 0)}`} />
        <${StatTile} label="(ô, slot) bị cắt voucher" value=${fmtPct(k.share_cells_off, 1)} sub=${`${fmtNum(k.n_switches_per_cell_day, 1)} lần đổi trạng thái / ô / ngày`} />
        <${StatTile} label="ETA đón trung bình" value=${fmtNum(k.mean_pickup_eta_min, 2) + " ph"} sub=${`slack TB ${k.mean_slack == null ? "∞" : fmtNum(k.mean_slack, 2)}`} />
        <${StatTile} label="Hủy + bỏ / lượt đặt" value=${fmtPct((k.abandon_rate || 0) + (k.cancel_rate || 0), 1)} sub=${`${fmtInt(k.n_cancelled)} hủy khi xe đến · ${fmtInt(k.n_abandoned)} bỏ`} />
      </div>` : null}
      ${slotCharts ? html`<div className="grid cols-2">
        <div className="card">
          <div className="card-head"><h2>Theo slot 15 phút</h2><span className="hint">vùng vàng = cửa sổ đánh giá</span></div>
          <${LineChart} x=${slotCharts.x} height=${230} bands=${slotCharts.win} xFormat=${(v) => fmtHM(v * 3600)} yLabel="số lượng / slot"
            series=${[
              { name: "chuyến hoàn thành", color: S(1), y: slotCharts.ss.n_completed },
              { name: "lượt đặt xe", color: S(2), y: slotCharts.ss.n_requests },
              { name: "voucher phát", color: S(4), y: slotCharts.ss.n_offers },
            ]} />
        </div>
        <div className="card">
          <div className="card-head"><h2>Số ô bị tắt voucher theo slot</h2><span className="hint">tầng ô của π<sub>θ</sub>${run.theta != null ? `, θ = ${fmtNum(run.theta, 2)}` : ""}</span></div>
          <${LineChart} x=${slotCharts.x} height=${230} bands=${slotCharts.win} xFormat=${(v) => fmtHM(v * 3600)} yLabel="ô tắt" yDomain=${[0, null]}
            series=${[{ name: "ô bị tắt", color: S(7), y: slotCharts.ss.cells_off }, { name: "ŝ trung bình (cắt ở 10)", color: S(3), y: slotCharts.ss.s_hat_mean, dash: true, format: (v) => fmtNum(v, 2) }]} />
        </div>
      </div>` : null}
    `}
    <div className="card">
      <div className="card-head"><h2>Các lượt chạy</h2><a href="#/run" className="btn sm primary">+ Chạy mô phỏng mới</a></div>
      ${runs && runs.length ? html`<${Table} rowKey=${(r) => r.id} selectedKey=${run && run.id} onRow=${(r) => onSelect(r.id)} rows=${runs}
        columns=${[
          { key: "name", label: "Tên" }, { key: "status", label: "Trạng thái", fmt: (v) => html`<${StatusPill} status=${v} />` },
          { key: "policy", label: "Chính sách", fmt: (v, r) => v ? `${v}${r.theta != null ? ` θ=${r.theta}` : ""}` : "–" },
          { key: "kpis", label: "N(π)", num: true, fmt: (v) => v ? fmtInt(v.N_completed) : "–" },
          { key: "kpis", label: "Chi / B", num: true, fmt: (v) => v ? (v.spent_share_of_budget == null ? fmtUSD(v.voucher_spent_usd) : fmtPct(v.spent_share_of_budget)) : "–" },
          { key: "kpis", label: "% ô tắt", num: true, fmt: (v) => v ? fmtPct(v.share_cells_off) : "–" },
          { key: "n_frames", label: "tick", num: true, fmt: fmtInt },
          { key: "created_at", label: "Lúc", fmt: (v) => v ? v.replace("T", " ").slice(5, 16) : "" },
        ]} />` : html`<div className="empty">Chưa có lượt chạy nào.</div>`}
    </div>
  </div>`;
}

// ---------------------------------------------------------------------------
// 2. Run (form + progress)
// ---------------------------------------------------------------------------
const SPEEDS = [1, 2, 5, 10, 20, 30, 60, 120];

function initialForm(cfg) {
  const th = cfg.policy.threshold;
  return {
    name: "", policy: cfg.policy.name, theta: th.theta, scope: th.scope, forecast: th.forecast, hysteresis: th.hysteresis_h,
    score_fn: th.score_fn, kappaMode: th.kappa === "auto" ? "auto" : "manual", kappaValue: th.kappa === "auto" ? 0 : th.kappa,
    enforce: cfg.budget.enforce, budget_mode: cfg.budget.mode, fraction: cfg.budget.fraction, fixed_usd: cfg.budget.fixed_usd ?? 5000,
    budget_manual: "", pct: cfg.voucher.pct_of_fare, fleet: cfg.supply.fleet_size, demand_scale: cfg.demand.demand_scale,
    radius: cfg.space.grid_radius, window_min: cfg.time.window_min ?? "", warmup: cfg.time.warmup_min, seed: cfg.meta.run_seed,
    design: cfg.experiment.design, cluster_level: String(cfg.experiment.cluster_level), p_on: cfg.experiment.p_on,
    legacy_slack_on: cfg.policy.legacy.slack_on, explore_frac: cfg.policy.legacy.explore_frac, extra: "",
  };
}

function buildRequest(f) {
  const o = [`policy.name=${f.policy}`];
  if (f.policy === "threshold") o.push(`policy.threshold.theta=${f.theta}`, `policy.threshold.scope=${f.scope}`, `policy.threshold.forecast=${f.forecast}`,
    `policy.threshold.hysteresis_h=${f.hysteresis}`, `policy.threshold.score_fn=${f.score_fn}`, `policy.threshold.kappa=auto`);
  if (f.policy === "experiment") o.push(`experiment.design=${f.design}`, `experiment.cluster_level=${f.cluster_level}`, `experiment.p_on=${f.p_on}`);
  if (f.policy === "legacy") o.push(`policy.legacy.slack_on=${f.legacy_slack_on}`, `policy.legacy.explore_frac=${f.explore_frac}`);
  o.push(`budget.enforce=${f.enforce}`, `budget.mode=${f.budget_mode}`, `budget.fraction=${f.fraction}`);
  if (f.budget_mode === "fixed") o.push(`budget.fixed_usd=${f.fixed_usd}`);
  o.push(`voucher.pct_of_fare=${f.pct}`, `supply.fleet_size=${f.fleet}`, `demand.demand_scale=${f.demand_scale}`, `space.grid_radius=${f.radius}`,
    `time.warmup_min=${f.warmup}`, `meta.run_seed=${f.seed}`, `time.window_min=${f.window_min === "" || f.window_min == null ? "null" : f.window_min}`);
  for (const line of (f.extra || "").split("\n")) { const l = line.trim(); if (l && !l.startsWith("#")) o.push(l); }
  const name = f.name || `${f.policy}${f.policy === "threshold" ? ` θ=${f.theta}` : ""} seed ${f.seed}`;
  const body = { name, overrides: o, layers: [] };
  if (f.enforce && f.budget_manual !== "" && f.budget_manual != null) body.budget_usd = Number(f.budget_manual);
  if (f.policy === "threshold" && f.kappaMode === "manual") body.kappa = Number(f.kappaValue);
  return body;
}

const PRESET_FIELDS = {
  default: { radius: 3, fleet: 240, window_min: "" },
  demo4h: { radius: 3, fleet: 240, window_min: 240 },
  tiny: { radius: 1, fleet: 10, window_min: 120 },
};

// Defined at module level: a component created inside the page would remount its input on every keystroke.
const Field = ({ label, children, hint }) => html`<label className="field"><span>${label}${hint ? html` <span className="muted">· ${hint}</span>` : null}</span>${children}</label>`;

export function RunPage({ defaults, runs, run, onStarted, onSelect }) {
  const [form, setForm] = useState(null);
  const [check, setCheck] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  useEffect(() => { if (defaults && !form) setForm(initialForm(defaults.config)); }, [defaults, form]);
  if (!defaults || !form) return html`<div className="card"><div className="empty">Đang nạp config mặc định…</div></div>`;
  const set = (k) => (e) => { const v = e && e.target ? (e.target.type === "checkbox" ? e.target.checked : e.target.value) : e; setForm((f) => ({ ...f, [k]: v })); setCheck(null); };
  const num = (k) => (e) => { setForm((f) => ({ ...f, [k]: e.target.value === "" ? "" : Number(e.target.value) })); setCheck(null); };
  const preset = (key) => { setForm((f) => ({ ...f, ...PRESET_FIELDS[key] })); setCheck(null); };
  const validate = async () => { setBusy(true); setErr(null); try { setCheck(await api("/api/config/validate", { method: "POST", body: buildRequest(form) })); } catch (e) { setErr(String(e.message)); } finally { setBusy(false); } };
  const start = async () => {
    setBusy(true); setErr(null);
    try { const r = await api("/api/runs", { method: "POST", body: buildRequest(form) }); onStarted(r.id); }
    catch (e) { setErr(String(e.message)); } finally { setBusy(false); }
  };
  const active = run && isRunning(run) ? run : (runs || []).find(isRunning) || run;
  return html`<div className="grid cols-2" style=${{ gridTemplateColumns: "minmax(0, 3fr) minmax(0, 2fr)" }}>
    <div className="stack">
      <div className="card">
        <div className="card-head"><h2>Cấu hình lượt chạy</h2><span className="hint">mọi tham số đi qua <code>--set key=value</code> lên <code>config/default.yaml</code></span></div>
        <div className="row" style=${{ marginBottom: 10 }}>
          <span className="small ink2">Preset:</span>
          ${defaults.presets.map((p) => html`<button key=${p.key} className="btn sm" onClick=${() => preset(p.key)}>${p.label}</button>`)}
        </div>
        <div className="stack">
          <div className="form-grid">
            <${Field} label="Tên lượt chạy"><input type="text" value=${form.name} onChange=${set("name")} placeholder="ví dụ: threshold θ=0,35 ring1" /><//>
            <${Field} label="Chính sách voucher"><select value=${form.policy} onChange=${set("policy")}>
              <option value="threshold">threshold: π_θ hai tầng (cắt ô theo ŝ, rider theo điểm)</option>
              <option value="all_on">all_on: bật mọi ô, phát mọi session (chịu B)</option>
              <option value="all_off">all_off: không voucher</option>
              <option value="legacy">legacy: người vận hành cũ (luật slack trễ + ε, nhắm rider)</option>
              <option value="experiment">experiment: switchback / rider A/B</option>
            </select><//>
          </div>
          ${form.policy === "threshold" ? html`<fieldset><legend>Tầng ô và tầng rider của π<sub>θ</sub></legend><div className="form-grid">
            <${Field} label="θ: ngưỡng cắt ô" hint="ŝ < θ thì tắt"><input type="number" step="0.05" min="0" value=${form.theta} onChange=${num("theta")} /><//>
            <${Field} label="Phạm vi đo ŝ"><select value=${form.scope} onChange=${set("scope")}><option value="cell">cell: slack của chính ô</option><option value="ring1">ring1: ô + 6 ô kề (H-25)</option></select><//>
            <${Field} label="Dự báo ŝ"><select value=${form.forecast} onChange=${set("forecast")}><option value="persistence">persistence: slot trước</option><option value="ar">ar: 0,7 slot trước + 0,3 cùng slot hôm qua</option></select><//>
            <${Field} label="Trễ bật lại h" hint="bật lại khi ŝ > θ + h"><input type="number" step="0.05" min="0" value=${form.hysteresis} onChange=${num("hysteresis")} /><//>
            <${Field} label="Hàm điểm rider τ̂"><select value=${form.score_fn} onChange=${set("score_fn")}>${defaults.score_functions.map((s) => html`<option key=${s} value=${s}>${s}</option>`)}</select><//>
            <${Field} label="κ (ngưỡng điểm)"><div className="row"><select value=${form.kappaMode} onChange=${set("kappaMode")}><option value="auto">auto (pilot, H-21)</option><option value="manual">nhập tay</option></select>
              ${form.kappaMode === "manual" ? html`<input type="number" step="0.01" value=${form.kappaValue} onChange=${num("kappaValue")} />` : null}</div><//>
          </div></fieldset>` : null}
          ${form.policy === "experiment" ? html`<fieldset><legend>Thiết kế thí nghiệm (M10)</legend><div className="form-grid">
            <${Field} label="Thiết kế"><select value=${form.design} onChange=${set("design")}><option value="cluster_switchback">cluster_switchback</option><option value="global_switchback">global_switchback</option><option value="rider_ab">rider_ab</option></select><//>
            <${Field} label="Cụm"><select value=${form.cluster_level} onChange=${set("cluster_level")}><option value="1">1 (mỗi ô một cụm)</option><option value="7">7 (~7 ô)</option><option value="all">all (toàn hệ)</option></select><//>
            <${Field} label="p_on"><input type="number" step="0.05" min="0" max="1" value=${form.p_on} onChange=${num("p_on")} /><//>
          </div><p className="small muted" style=${{ marginTop: 6 }}>Thí nghiệm không áp ngân sách (experiment.budget_enforce = false, D10).</p></fieldset>` : null}
          ${form.policy === "legacy" ? html`<fieldset><legend>Chính sách cũ</legend><div className="form-grid">
            <${Field} label="slack_on" hint="bật ô nếu slack slot trước ≥"><input type="number" step="0.05" value=${form.legacy_slack_on} onChange=${num("legacy_slack_on")} /><//>
            <${Field} label="explore_frac" hint="lát ngẫu nhiên hóa"><input type="number" step="0.01" min="0" max="1" value=${form.explore_frac} onChange=${num("explore_frac")} /><//>
          </div></fieldset>` : null}
          <fieldset><legend>Ngân sách và voucher</legend><div className="form-grid">
            <label className="check"><input type="checkbox" checked=${form.enforce} onChange=${set("enforce")} /> Áp ngân sách B (budget.enforce)</label>
            <${Field} label="Cách lấy B"><select value=${form.budget_mode} onChange=${set("budget_mode")} disabled=${!form.enforce}><option value="fraction_of_all_on">fraction × chi của pilot all_on</option><option value="fixed">cố định (USD/kỳ)</option></select><//>
            ${form.budget_mode === "fixed" ? html`<${Field} label="B cố định (USD/kỳ)"><input type="number" step="10" value=${form.fixed_usd} onChange=${num("fixed_usd")} disabled=${!form.enforce} /><//>`
              : html`<${Field} label="fraction"><input type="number" step="0.05" min="0" value=${form.fraction} onChange=${num("fraction")} disabled=${!form.enforce} /><//>`}
            <${Field} label="Nhập B tay (bỏ qua pilot)" hint="để trống = chạy pilot"><input type="number" step="10" value=${form.budget_manual} onChange=${set("budget_manual")} disabled=${!form.enforce} /><//>
            <${Field} label="Voucher = % cước"><input type="number" step="0.05" min="0" max="1" value=${form.pct} onChange=${num("pct")} /><//>
          </div></fieldset>
          <fieldset><legend>Thị trường và thời gian</legend><div className="form-grid">
            <${Field} label="Đội xe (fleet_size)"><input type="number" step="10" min="1" value=${form.fleet} onChange=${num("fleet")} /><//>
            <${Field} label="Hệ số cầu (demand_scale)"><input type="number" step="0.05" min="0.05" value=${form.demand_scale} onChange=${num("demand_scale")} /><//>
            <${Field} label="Bán kính lưới" hint="3 → 37 ô, 2 → 19, 1 → 7"><input type="number" step="1" min="1" max="6" value=${form.radius} onChange=${num("radius")} /><//>
            <${Field} label="Cửa sổ (phút)" hint="trống = 1 ngày; bội của 15"><input type="number" step="15" min="15" value=${form.window_min} onChange=${set("window_min")} /><//>
            <${Field} label="Warm-up (phút)"><input type="number" step="15" min="0" value=${form.warmup} onChange=${num("warmup")} /><//>
            <${Field} label="run_seed"><input type="number" step="1" value=${form.seed} onChange=${num("seed")} /><//>
          </div></fieldset>
          <${Field} label="Override thêm (mỗi dòng key=value, cú pháp --set)"><textarea value=${form.extra} onChange=${set("extra")} placeholder=${"matching.max_pickup_eta_min=30\nreposition.max_idle_min=10"}></textarea><//>
          <div className="row">
            <button className="btn" onClick=${validate} disabled=${busy}>Kiểm tra config</button>
            <button className="btn primary" onClick=${start} disabled=${busy}>▶ Chạy mô phỏng</button>
            ${check ? (check.ok ? html`<span className="small ink2">OK · hash <code>${check.config_hash}</code> · ${check.n_cells} ô · ${check.fleet_size} xe · cửa sổ ${check.window_min} phút · ${check.policy}</span>` : html`<span className="err small">${check.error}</span>`) : null}
            ${err ? html`<span className="err small">${err}</span>` : null}
          </div>
          <p className="small muted">Thời gian ước tính với cấu hình mặc định (1 ngày, 240 xe): pilot B ≈ 10–15 s, κ auto 1–6 pilot × 10–20 s, mô phỏng ≈ 25–40 s. Các lượt chạy nối tiếp nhau trong một luồng nền; kết quả ghi vào <code>runs/dashboard/${"<"}id${">"}/</code> theo đúng <code>docs/schema.md</code>.</p>
        </div>
      </div>
    </div>
    <div className="stack">
      <${ProgressCard} run=${active} onSelect=${onSelect} />
      <div className="card">
        <div className="card-head"><h2>Hàng đợi và lịch sử</h2></div>
        ${runs && runs.length ? html`<${Table} rowKey=${(r) => r.id} selectedKey=${run && run.id} onRow=${(r) => onSelect(r.id)} rows=${runs.slice(0, 12)} columns=${[
          { key: "name", label: "Tên" }, { key: "status", label: "Trạng thái", fmt: (v) => html`<${StatusPill} status=${v} />` },
          { key: "kpis", label: "N", num: true, fmt: (v) => v ? fmtInt(v.N_completed) : "–" }]} />` : html`<div className="empty">trống</div>`}
      </div>
    </div>
  </div>`;
}

function ProgressCard({ run, onSelect }) {
  if (!run) return html`<div className="card"><div className="empty">Chưa có lượt chạy nào.</div></div>`;
  const indeterminate = ["loading", "budget", "kappa", "writing", "queued"].includes(run.status);
  const pct = run.status === "simulating" ? 100 * run.progress : (run.status === "done" ? 100 : 0);
  return html`<div className="card">
    <div className="card-head"><h2>${run.name} <${StatusPill} status=${run.status} /></h2>${run.stage_elapsed_s != null ? html`<span className="hint">giai đoạn này ${fmtDur(run.stage_elapsed_s)}</span>` : null}</div>
    <div className=${"progress" + (indeterminate ? " indeterminate" : "")}><div style=${{ width: `${pct}%` }}></div></div>
    <p className="ink2" style=${{ marginTop: 8 }}>${run.message}${run.status === "simulating" ? ` · tick ${fmtInt(run.tick)} / ≤ ${fmtInt(run.ticks_max)} · ${fmtClock(run.t_s)}` : ""}</p>
    ${run.status === "done" && run.kpis ? html`<div className="grid cols-3" style=${{ marginBottom: 10 }}>
      <${StatTile} label="N(π)" value=${fmtInt(run.kpis.N_completed)} />
      <${StatTile} label="Chi voucher" value=${fmtUSD(run.kpis.voucher_spent_usd, 0)} sub=${run.budget_usd != null ? `B = ${fmtUSD(run.budget_usd, 0)}/kỳ` : "không áp B"} />
      <${StatTile} label="% (ô, slot) tắt" value=${fmtPct(run.kpis.share_cells_off)} />
    </div>` : null}
    ${run.status === "done" || run.status === "simulating" ? html`<div className="row" style=${{ marginBottom: 8 }}><button className="btn sm primary" onClick=${() => { onSelect(run.id); location.hash = "#/map"; }}>Xem bản đồ động</button><button className="btn sm" onClick=${() => { onSelect(run.id); location.hash = "#/overview"; }}>Tổng quan</button></div>` : null}
    ${run.error ? html`<p className="err">${run.error}</p>` : null}
    <div className="log">${(run.log || []).join("\n")}</div>
  </div>`;
}

// ---------------------------------------------------------------------------
// 3. Map (animation)
// ---------------------------------------------------------------------------
export function MapPage({ run }) {
  const running = isRunning(run);
  const runId = run && run.geometry ? run.id : null;
  const { framesRef, loaded } = useFrames(runId, run ? run.n_frames : 0, running);
  const slotsQ = useApi(runId ? `/api/runs/${runId}/slots` : null, [run && run.n_slots]);
  const tick_s = run && run.clock ? run.clock.tick_s : 60;
  const player = usePlayer(tick_s);
  const [mode, setMode] = useLocalStorage("map.mode", "promo");
  const [selected, setSelected] = useState(null);
  const [pulseList, setPulseList] = useLocalStorage("map.pulses", ["offer", "match", "cancel"]);
  const pulses = useMemo(() => new Set(pulseList), [pulseList]);
  const wrapRef = useRef(null);
  const width = useWidth(wrapRef, 760);
  const height = clamp(Math.round(width * 0.82), 360, 680);
  useEffect(() => { player.ref.current.nFrames = loaded; }, [loaded]);
  // New run: a finished one plays from the start of the evaluation window, a running one follows the live frames.
  const startTau = run && run.clock ? run.clock.window_start_s / tick_s : 0;
  useEffect(() => { player.set({ tau: 0, playing: false, follow: !!running, last: null }); setSelected(null); }, [runId]);
  useEffect(() => {
    if (runId && !running && loaded > startTau && !player.ref.current.playing && player.ref.current.tau === 0) {
      player.set({ tau: startTau, playing: true, last: null });
    }
  }, [runId, running, loaded > startTau]);
  const clock = run ? run.clock : null;
  const slots = slotsQ.data;
  const selSeries = useMemo(() => {
    if (selected == null || !slots || !slots.n_slots || !clock) return null;
    const xs = slots.t_start.map((t) => t / 3600);
    return { x: xs, s_hat: slots.s_hat.map((row) => (row[selected] == null ? null : Math.min(row[selected], 10))),
      slack: slots.slack.map((row) => (row[selected] == null ? null : Math.min(row[selected], 10))),
      off: bandsOf(slots.promo_on.map((row) => !row[selected]), xs, clock.slot_s / 3600) };
  }, [selected, slots, clock]);
  if (!run) return html`<${NoRun} />`;
  if (!run.geometry) return html`<div className="card"><div className="empty">Lượt chạy đang ở giai đoạn ${STATUS_VI[run.status] || run.status}… bản đồ hiện khi mô phỏng bắt đầu.</div></div>`;
  const F = framesRef.current;
  const ui = player.ui;
  const n = loaded;
  const k = n ? clamp(Math.floor(ui.tau), 0, n - 1) : -1;
  const tDisp = n ? F.t[k] + (ui.tau - k) * tick_s : 0;
  const slotIdx = slots && slots.n_slots ? clamp(Math.floor(tDisp / clock.slot_s), 0, slots.n_slots - 1) : -1;
  const togglePulse = (g) => setPulseList(pulseList.includes(g) ? pulseList.filter((x) => x !== g) : [...pulseList, g]);
  const seek = (tau) => player.set({ tau: clamp(tau, 0, Math.max(0, n - 1)), follow: false });
  const winStartTau = clock ? clock.window_start_s / tick_s : 0;
  const winEndTau = clock ? clock.window_end_s / tick_s : 0;
  // live counters at frame k
  let counts = null;
  if (k >= 0) {
    const st = F.status[k];
    const c = [0, 0, 0, 0, 0];
    for (let d = 0; d < st.length; d++) c[st[d]]++;
    counts = { offline: c[0], idle: c[1], en_route: c[2], on_trip: c[3], repositioning: c[4], waiting: sum(F.waiting[k]),
      sessions: F.session_counts[k], orders: F.order_counts[k], ledger: F.ledger[k] };
  }
  const col = driverColors();
  const offNow = slotIdx >= 0 ? slots.promo_on[slotIdx].map((v, i) => (v ? -1 : i)).filter((i) => i >= 0) : [];
  return html`<div className="grid cols-2" style=${{ gridTemplateColumns: "minmax(0, 5fr) minmax(300px, 2fr)" }}>
    <div className="stack">
      <div className="card">
        <div className="row between" style=${{ marginBottom: 8 }}>
          <div className="seg">
            ${[["promo", "Trạng thái voucher"], ["slack", "ŝ dự báo"], ["waiting", "Khách chờ"], ["cluster", "Cụm thí nghiệm"]].map(([m, l]) => html`<button key=${m} className=${mode === m ? "on" : ""} onClick=${() => setMode(m)}>${l}</button>`)}
          </div>
          <div className="row small ink2">
            <span>Hiệu ứng:</span>
            ${[["offer", "phát / hết ngân sách"], ["match", "ghép / hoàn thành"], ["cancel", "hủy / bỏ"], ["request", "đặt xe"]].map(([g, l]) => html`<label key=${g} className="check"><input type="checkbox" checked=${pulses.has(g)} onChange=${() => togglePulse(g)} />${l}</label>`)}
          </div>
        </div>
        <div ref=${wrapRef}>
          ${n ? html`<${HexMap} geometry=${run.geometry} slots=${slots} framesRef=${framesRef} player=${player.ref} k=${k} tDisp=${tDisp} mode=${mode}
              selected=${selected} onSelect=${setSelected} pulses=${pulses} width=${width} height=${height} theta=${run.theta} clock=${clock} />`
            : html`<div className="empty" style=${{ height }}>Đang tải frame… (${run.n_frames} tick trên server)</div>`}
        </div>
        <${MapLegend} mode=${mode} />
      </div>
      <div className="card">
        <div className="timeline">
          <div className="row">
            <button className="btn icon" title="về đầu" onClick=${() => seek(0)}>⏮</button>
            <button className="btn icon primary" title=${ui.playing ? "tạm dừng" : "phát"} onClick=${() => player.set({ playing: !ui.playing, last: null, follow: false })}>${ui.playing ? "⏸" : "▶"}</button>
            <button className="btn icon" title="đến đầu cửa sổ đánh giá" onClick=${() => seek(winStartTau)}>⏭</button>
          </div>
          <select value=${ui.speed} onChange=${(e) => player.set({ speed: Number(e.target.value) })} title="phút mô phỏng mỗi giây thực">
            ${SPEEDS.map((s) => html`<option key=${s} value=${s}>×${s} (${s} ph/s)</option>`)}
          </select>
          <div>
            <div className="ticks"><div className="win" style=${{ left: `${100 * winStartTau / Math.max(1, run.ticks_max || n)}%`, width: `${100 * (winEndTau - winStartTau) / Math.max(1, run.ticks_max || n)}%` }}></div></div>
            <input type="range" min="0" max=${Math.max(0, n - 1)} step="0.5" value=${ui.tau} onChange=${(e) => seek(Number(e.target.value))} />
          </div>
          <div className="small ink2 mono" style=${{ textAlign: "right", minWidth: 150 }}>
            <div><b>${fmtClock(tDisp)}</b></div>
            <div>tick ${k + 1} / ${n}${running ? html` · <label className="check"><input type="checkbox" checked=${ui.follow} onChange=${(e) => player.set({ follow: e.target.checked, playing: false })} />theo dõi trực tiếp</label>` : ""}</div>
          </div>
        </div>
      </div>
    </div>
    <div className="stack">
      <div className="card">
        <div className="card-head"><h3>Đội xe lúc này</h3><span className="hint">${run.geometry.n_drivers} xe</span></div>
        ${counts ? html`<div className="kv">
          ${["idle", "en_route", "on_trip", "repositioning"].map((s) => html`<span key=${s} className="k"><i className="dot" style=${{ background: col[s], marginRight: 6 }}></i>${DRIVER_LABEL[s]}</span><span key=${s + "v"} className="v">${fmtInt(counts[s])}</span>`)}
          <span className="k">offline (hết ca)</span><span className="v">${fmtInt(counts.offline)}</span>
          <span className="k"><i className="dot" style=${{ background: "transparent", border: `2px solid ${S(5)}`, marginRight: 6, width: 8, height: 8 }}></i>khách đang chờ ghép</span><span className="v">${fmtInt(counts.waiting)}</span>
        </div>` : html`<div className="muted small">chưa có frame</div>`}
      </div>
      <div className="card">
        <div className="card-head"><h3>Cộng dồn từ đầu lượt</h3></div>
        ${counts ? html`<div className="kv">
          <span className="k">phiên mở (session)</span><span className="v">${fmtInt(counts.sessions[0])}</span>
          <span className="k">voucher đã phát</span><span className="v">${fmtInt(counts.sessions[1])}</span>
          <span className="k">muốn phát nhưng hết B</span><span className="v">${fmtInt(counts.sessions[2])}</span>
          <span className="k">lượt đặt xe</span><span className="v">${fmtInt(counts.sessions[3])}</span>
          <span className="k">chuyến hoàn thành</span><span className="v"><b>${fmtInt(counts.orders[3])}</b></span>
          <span className="k">hủy khi xe đang đến</span><span className="v">${fmtInt(counts.orders[5])}</span>
          <span className="k">bỏ vì chờ lâu</span><span className="v">${fmtInt(counts.orders[4])}</span>
        </div>` : null}
      </div>
      <div className="card">
        <div className="card-head"><h3>Ngân sách kỳ hiện tại</h3>${counts ? html`<span className="hint">kỳ ${counts.ledger[0] < 0 ? "warm-up" : counts.ledger[0]}</span>` : null}</div>
        ${counts ? html`<${Meter} max=${counts.ledger[4] < 0 ? null : counts.ledger[4] / 100} format=${(v) => fmtUSD(v, 0)}
          segments=${[{ value: counts.ledger[1] / 100, color: cssVar("--seq-600"), label: "đã chi" }, { value: counts.ledger[2] / 100, color: cssVar("--seq-400"), label: "đã đặt (chờ hoàn thành)" }, { value: counts.ledger[3] / 100, color: cssVar("--seq-200"), label: "đang giữ (chờ đặt xe)" }]} />` : null}
        <p className="small muted" style=${{ marginTop: 6 }}>Bất biến: chi + đặt + giữ ≤ B. Khi chạm trần, session muốn phát bị chặn (dấu × đỏ trên bản đồ).</p>
      </div>
      <div className="card">
        <div className="card-head"><h3>Ô đang bị cắt voucher</h3><span className="hint">${slotIdx >= 0 ? `${offNow.length} / ${run.geometry.n_cells} ô · slot ${slotIdx}` : ""}</span></div>
        ${offNow.length ? html`<div className="pill-list">${offNow.map((c) => html`<span key=${c} style=${{ cursor: "pointer" }} onClick=${() => setSelected(c)}>${c}</span>`)}</div>` : html`<div className="muted small">${run.policy === "threshold" ? "không ô nào" : "chính sách này không cắt ô theo ŝ"}</div>`}
      </div>
      ${selected != null ? html`<div className="card">
        <div className="card-head"><h3>Ô ${selected}</h3><button className="btn sm" onClick=${() => setSelected(null)}>đóng</button></div>
        ${k >= 0 ? html`<div className="kv">
          <span className="k">voucher slot này</span><span className="v">${slotIdx >= 0 ? (slots.promo_on[slotIdx][selected] ? "BẬT" : "TẮT") : "–"}</span>
          <span className="k">ŝ so với θ</span><span className="v">${slotIdx >= 0 && slots.s_hat[slotIdx][selected] != null ? fmtNum(slots.s_hat[slotIdx][selected], 2) : "–"} / ${run.theta != null ? fmtNum(run.theta, 2) : "–"}</span>
          <span className="k">xe rảnh · đi đón · chở</span><span className="v">${F.idle[k][selected]} · ${F.enroute[k][selected]} · ${F.ontrip[k][selected]}</span>
          <span className="k">khách chờ</span><span className="v">${F.waiting[k][selected]}</span>
        </div>` : null}
        ${selSeries ? html`<div style=${{ marginTop: 8 }}><${LineChart} x=${selSeries.x} height=${170} xFormat=${(v) => fmtHM(v * 3600)} bands=${selSeries.off.map((b) => ({ ...b, color: "rgba(137,135,129,0.18)" }))}
          hlines=${run.theta != null ? [{ y: run.theta, label: `θ = ${fmtNum(run.theta, 2)}`, color: S(8) }] : []} yFormat=${(v) => fmtNum(v, 1)}
          series=${[{ name: "ŝ dự báo (cắt ở 10)", color: S(1), y: selSeries.s_hat, format: (v) => fmtNum(v, 2) }, { name: "slack thực của slot", color: S(2), y: selSeries.slack, dash: true, format: (v) => fmtNum(v, 2) }]} />
          <p className="small muted">Vùng xám = slot ô bị tắt.</p></div>` : null}
      </div>` : null}
    </div>
  </div>`;
}

function bandsOf(flags, xs, w) {
  const out = [];
  let start = null;
  flags.forEach((f, i) => {
    if (f && start == null) start = i;
    if ((!f || i === flags.length - 1) && start != null) { const end = f ? i : i - 1; out.push({ x0: xs[start], x1: xs[end] + w }); start = null; }
  });
  return out;
}

// ---------------------------------------------------------------------------
// 4. Cells & theta
// ---------------------------------------------------------------------------
export function CellsPage({ run }) {
  const runId = run && run.n_slots ? run.id : null;
  const slotsQ = useApi(runId ? `/api/runs/${runId}/slots` : null, [run && run.n_slots]);
  const sumQ = useApi(runId ? `/api/runs/${runId}/summary` : null, [run && run.status]);
  const [mode, setMode] = useLocalStorage("cells.mode", "status");
  const [sel, setSel] = useState(0);
  const seq = useMemo(() => SEQ(), []);
  if (!run) return html`<${NoRun} />`;
  const slots = slotsQ.data;
  if (!slots || !slots.n_slots) return html`<div className="card"><div className="empty">Chưa có slot nào được ghi.</div></div>`;
  const N = slots.promo_on[0].length, Sn = slots.n_slots;
  const clock = run.clock;
  const theta = run.theta;
  // matrix [cell][slot]
  const transpose = (M) => Array.from({ length: N }, (_, c) => M.map((row) => row[c]));
  const promoT = transpose(slots.promo_on), shatT = transpose(slots.s_hat), slackT = transpose(slots.slack);
  const values = mode === "status" ? promoT : mode === "shat" ? shatT : slackT;
  const color = (v, r, c) => {
    if (mode === "status") return v ? "var(--promo-on)" : cssVar("--axis");
    return v == null ? cssVar("--surface-2") : seqColor(Math.min(v, 3), 3, seq);
  };
  const mark = mode === "status" ? null : (r, c) => !promoT[r][c];
  const colLabels = slots.t_start.map((t) => fmtHM(t));
  const offCount = promoT.map((row) => row.filter((v) => !v).length);
  const neverCut = offCount.filter((v) => v === 0).length;
  const top = offCount.map((v, i) => ({ cell: i, off: v })).sort((a, b) => b.off - a.off).slice(0, 8);
  const sw = (sumQ.data && sumQ.data.switch_events) || [];
  const xs = slots.t_start.map((t) => t / 3600);
  const detail = { s_hat: shatT[sel].map((v) => (v == null ? null : Math.min(v, 10))), slack: slackT[sel].map((v) => (v == null ? null : Math.min(v, 10))), off: bandsOf(promoT[sel].map((v) => !v), xs, clock.slot_s / 3600) };
  const windowSlots = slots.t_start.filter((t) => t >= clock.window_start_s && t < clock.window_end_s).length;
  const shareOff = sum(offCount) / (N * Sn);
  return html`<div className="stack">
    <div className="grid cols-4">
      <${StatTile} label="(ô, slot) bị cắt" value=${fmtPct(shareOff)} sub=${`${Sn} slot × ${N} ô (gồm warm-up, cool-down)`} />
      <${StatTile} label="Ô chưa bao giờ bị cắt" value=${`${neverCut} / ${N}`} />
      <${StatTile} label="Lần đổi trạng thái" value=${fmtInt(sw.length)} sub=${run.kpis ? `${fmtNum(run.kpis.n_switches_per_cell_day, 1)} / ô / ngày trong cửa sổ` : ""} />
      <${StatTile} label="Quy tắc cắt" value=${theta != null ? `ŝ < ${fmtNum(theta, 2)}` : "không cắt"} sub=${run.policy === "threshold" ? `ŝ theo ${run.scope}, dự báo ${run.config ? run.config.policy.threshold.forecast : ""}` : run.policy} />
    </div>
    <div className="card">
      <div className="card-head"><h2>Bản đồ nhiệt ô × slot</h2>
        <div className="seg">${[["status", "Bật / tắt"], ["shat", "ŝ dự báo (quyết định)"], ["slack", "slack thực (công bố cuối slot)"]].map(([m, l]) => html`<button key=${m} className=${mode === m ? "on" : ""} onClick=${() => setMode(m)}>${l}</button>`)}</div>
      </div>
      <${Heatmap} values=${values} rowLabels=${Array.from({ length: N }, (_, i) => String(i))} colLabels=${colLabels} colLabelEvery=${4} color=${color} mark=${mark}
        cellH=${Math.max(9, Math.min(14, Math.floor(520 / N)))} selectedRow=${sel} onClick=${(r) => setSel(r)}
        tooltip=${(r, c) => [`Ô ${r} · slot ${c} (${fmtHM(slots.t_start[c])})`, `voucher ${promoT[r][c] ? "BẬT" : "TẮT"}`, `ŝ = ${shatT[r][c] == null ? "–" : fmtNum(shatT[r][c], 2)}${theta != null ? ` (θ = ${fmtNum(theta, 2)})` : ""}`, `slack thực = ${slackT[r][c] == null ? "–" : fmtNum(slackT[r][c], 2)}`, `${slots.n_offers[c][r] == null ? "" : `${slots.n_offers[c][r]} voucher · ${slots.n_requests[c][r]} đặt · ${slots.n_completed[c][r]} hoàn thành`}`]} />
      <div className="legend">
        ${mode === "status" ? html`<span><i className="swatch" style=${{ background: "var(--promo-on)", border: "1px solid var(--border)" }}></i>bật</span><span><i className="swatch" style=${{ background: cssVar("--axis") }}></i>tắt (ŝ ${"<"} θ)</span>`
          : html`<span><i className="swatch" style=${{ background: "linear-gradient(90deg, var(--seq-100), var(--seq-700))" }}></i>0 → 3+ (dư cung)</span><span><i className="swatch" style=${{ background: "transparent", border: `1px solid ${cssVar("--ink")}` }}></i>viền = ô bị tắt</span><span><i className="swatch" style=${{ background: cssVar("--surface-2") }}></i>chưa có snapshot</span>`}
        <span className="muted">bấm một hàng để xem chi tiết ô</span>
      </div>
    </div>
    <div className="grid cols-2">
      <div className="card">
        <div className="card-head"><h2>Ô ${sel}: ŝ dự báo so với θ</h2><span className="hint">vùng xám = slot bị tắt</span></div>
        <${LineChart} x=${xs} height=${240} xFormat=${(v) => fmtHM(v * 3600)} bands=${detail.off.map((b) => ({ ...b, color: "rgba(137,135,129,0.18)" }))}
          hlines=${theta != null ? [{ y: theta, label: `θ = ${fmtNum(theta, 2)}`, color: S(8) }] : []} yFormat=${(v) => fmtNum(v, 1)}
          series=${[{ name: "ŝ dự báo (dùng để quyết định, cắt ở 10)", color: S(1), y: detail.s_hat, format: (v) => fmtNum(v, 2) }, { name: "slack thực của slot (công bố sau)", color: S(2), y: detail.slack, dash: true, format: (v) => fmtNum(v, 2) }]} />
        <p className="small muted">ŝ của slot k chỉ dùng snapshot slot ${"<"} k (không nhìn trước): đường liền đi sau đường đứt một slot khi dự báo persistence.</p>
      </div>
      <div className="card">
        <div className="card-head"><h2>Ô bị cắt nhiều nhất</h2><span className="hint">số slot tắt</span></div>
        <${BarChart} horizontal height=${240} categories=${top.map((t) => `ô ${t.cell}`)} series=${[{ name: "slot bị tắt", color: S(7), values: top.map((t) => t.off) }]} legend=${false} />
      </div>
    </div>
    <div className="card">
      <div className="card-head"><h2>Nhật ký bật / tắt</h2><span className="hint">${sw.length} sự kiện${sw.length > 400 ? ", hiện 400 đầu" : ""}</span></div>
      ${sw.length ? html`<${Table} maxHeight=${320} rows=${sw.slice(0, 400)} columns=${[
        { key: "slot", label: "Slot", num: true }, { key: "t_s", label: "Giờ", fmt: (v) => fmtClock(v) }, { key: "cell", label: "Ô", num: true, fmt: (v) => html`<a href="#" onClick=${(e) => { e.preventDefault(); setSel(v); }}>${v}</a>` },
        { key: "to_on", label: "Chuyển", fmt: (v) => (v ? "tắt → BẬT" : "bật → TẮT") }, { key: "s_hat", label: "ŝ", num: true, fmt: (v) => (v == null ? "–" : fmtNum(v, 2)) }, { key: "theta", label: "θ", num: true, fmt: (v) => (v == null ? "–" : fmtNum(v, 2)) }]} />` : html`<div className="empty">không có sự kiện đổi trạng thái</div>`}
    </div>
  </div>`;
}

// ---------------------------------------------------------------------------
// 5. Distribution
// ---------------------------------------------------------------------------
export function DistributionPage({ run }) {
  const sumQ = useApi(run && run.status === "done" ? `/api/runs/${run.id}/summary` : null, [run && run.id]);
  if (!run) return html`<${NoRun} />`;
  if (run.status !== "done") return html`<div className="card"><div className="empty">Trang này cần lượt chạy đã xong (đang ${STATUS_VI[run.status] || run.status}).</div></div>`;
  const s = sumQ.data;
  if (!s || !s.distribution) return html`<div className="card"><div className="empty">Đang tải…</div></div>`;
  const d = s.distribution, k = s.kpis, clock = run.clock;
  const curve = d.ledger_curve;
  const xh = curve ? curve.t.map((t) => t / 3600) : [];
  const hist = d.score_hist;
  const kText = kappaText(run);
  return html`<div className="stack">
    <div className="grid cols-6">
      <${StatTile} label="Voucher đã phát (cửa sổ)" value=${fmtInt(d.n_offers)} sub=${`${fmtPct(d.n_offers / Math.max(1, d.n_sessions))} số session`} />
      <${StatTile} label="Muốn phát nhưng hết B" value=${fmtInt(d.n_blocked)} sub="budget_blocked = true" />
      <${StatTile} label="Voucher trung bình" value=${d.mean_voucher_usd == null ? "–" : fmtUSD(d.mean_voucher_usd, 2)} sub=${run.config ? `${fmtPct(run.config.voucher.pct_of_fare, 0)} cước gốc` : ""} />
      <${StatTile} label="Chi thực / B" value=${k.spent_share_of_budget == null ? fmtUSD(k.voucher_spent_usd) : fmtPct(k.spent_share_of_budget)} sub="chỉ voucher của chuyến hoàn thành" />
      <${StatTile} label="κ tầng rider" value=${kText} sub=${run.policy === "threshold" ? `điểm ${run.score_fn}` : "không dùng"} />
      <${StatTile} label="Session trong cửa sổ" value=${fmtInt(d.n_sessions)} />
    </div>
    <div className="grid cols-2">
      <div className="card">
        <div className="card-head"><h2>Ngân sách theo thời gian</h2><span className="hint">sổ cái từng kỳ; bất biến chi + đặt + giữ ≤ B</span></div>
        ${curve ? html`<${LineChart} x=${xh} height=${240} xFormat=${(v) => fmtHM(v * 3600)} yFormat=${(v) => fmtUSD(v, 0)} bands=${[{ x0: clock.window_start_s / 3600, x1: clock.window_end_s / 3600 }]}
          series=${[{ name: "trần B của kỳ", color: S(8), y: curve.limit_usd, dash: true }, { name: "đã dùng (chi + đặt + giữ)", color: S(1), y: curve.used_usd }, { name: "đã chi (chuyến hoàn thành)", color: S(3), y: curve.spent_usd }]} />` : null}
        <${Table} rows=${d.budget_periods} columns=${[{ key: "period", label: "Kỳ", fmt: (v) => (v < 0 ? "warm-up" : v) }, { key: "spent_usd", label: "Đã chi", num: true, fmt: (v) => fmtUSD(v, 2) }, { key: "limit_usd", label: "Trần B", num: true, fmt: (v) => (v == null ? "không" : fmtUSD(v, 2)) }, { key: "spent_usd", label: "Chi / B", num: true, fmt: (v, r) => (r.limit_usd ? fmtPct(v / r.limit_usd) : "–") }]} />
      </div>
      <div className="card">
        <div className="card-head"><h2>Phát voucher theo giờ</h2><span className="hint">session mở trong giờ đó, cửa sổ đánh giá</span></div>
        <${BarChart} height=${240} stacked categories=${d.by_hour.map((h) => `${h.hour}h`)} labelEvery=${2}
          series=${[{ name: "đã phát", color: S(4), values: d.by_hour.map((h) => h.offers) }, { name: "bị chặn (hết B)", color: S(8), values: d.by_hour.map((h) => h.blocked) }]} />
        <${BarChart} height=${160} categories=${d.by_hour.map((h) => `${h.hour}h`)} labelEvery=${2} yFormat=${(v) => fmtPct(v, 0)} title="Tỷ lệ session được phát"
          series=${[{ name: "tỷ lệ phát", color: S(1), values: d.by_hour.map((h) => (h.sessions ? h.offers / h.sessions : 0)), format: (v) => fmtPct(v, 1) }]} legend=${false} />
      </div>
    </div>
    <div className="grid cols-2">
      <div className="card">
        <div className="card-head"><h2>Phân bố điểm τ̂ và ngưỡng κ</h2><span className="hint">${hist ? `κ = ${kText} · ${fmtPct(hist.share_on_cell)} session ở ô đang bật` : ""}</span></div>
        ${hist ? html`<${BarChart} height=${240} categories=${hist.edges.slice(0, -1).map((e, i) => fmtNum((e + hist.edges[i + 1]) / 2, 2))} labelEvery=${5}
          series=${[{ name: "mọi session", color: cssVar("--axis"), values: hist.all }, { name: "được phát (ô bật và điểm ≥ κ)", color: S(1), values: hist.offered }]} />` : html`<div className="empty">chính sách này không chấm điểm rider</div>`}
      </div>
      <div className="card">
        <div className="card-head"><h2>Ai nhận voucher</h2><span className="hint">theo phân khúc rider và cơ chế gán</span></div>
        ${d.by_segment.length ? html`<${BarChart} height=${170} categories=${d.by_segment.map((s) => ({ 0: "thường", 1: "nhạy giá", 2: "ít nhạy giá" })[s.segment])} yFormat=${(v) => fmtPct(v, 0)}
          series=${[{ name: "tỷ lệ session được phát", color: S(1), values: d.by_segment.map((s) => s.offer_share || 0), format: (v) => fmtPct(v, 1) }]} legend=${false} />` : null}
        <${Table} rows=${d.by_mechanism} columns=${[{ key: "mechanism", label: "Cơ chế (assign_mechanism)" }, { key: "sessions", label: "Session", num: true, fmt: fmtInt }, { key: "offers", label: "Phát", num: true, fmt: fmtInt }, { key: "offers", label: "Tỷ lệ", num: true, fmt: (v, r) => fmtPct(v / Math.max(1, r.sessions)) }]} />
        <div style=${{ marginTop: 10 }}>
          <${Table} rows=${d.by_arm} columns=${[{ key: "arm", label: "Nhánh", fmt: (v) => (v === "voucher" ? "có voucher" : "không voucher") }, { key: "sessions", label: "Session", num: true, fmt: fmtInt }, { key: "request_rate", label: "Tỷ lệ đặt", num: true, fmt: (v) => fmtPct(v) }, { key: "completion_rate", label: "Tỷ lệ hoàn thành", num: true, fmt: (v) => fmtPct(v) }]} />
          <p className="small muted" style=${{ marginTop: 6 }}>Mô tả, không phải uplift: nhánh không ngẫu nhiên (chính sách chọn ai được phát), và voucher còn làm đổi trạng thái thị trường của người khác (interference).</p>
        </div>
      </div>
    </div>
  </div>`;
}

// ---------------------------------------------------------------------------
// 6. Results of the saved experiments (runs/)
// ---------------------------------------------------------------------------
export function ResultsPage() {
  const sweepsQ = useApi("/api/results/sweeps");
  const ptQ = useApi("/api/results/policy_tables");
  const tpQ = useApi("/api/results/throughput");
  const gteQ = useApi("/api/results/gte");
  const evQ = useApi("/api/results/evaluations");
  const figQ = useApi("/api/results/figures");
  const [picked, setPicked] = useLocalStorage("results.sweeps", null);
  const [metric, setMetric] = useState("N");
  const sweeps = (sweepsQ.data && sweepsQ.data.sweeps) || [];
  const selected = useMemo(() => {
    if (picked && picked.length) return picked.filter((k) => sweeps.some((s) => s.key === k));
    const pref = ["b7b_h21/sweep_theta_ref", "s5/sweep_ring1_dr", "s5/sweep_ring1_heuristic"].filter((k) => sweeps.some((s) => s.key === k));
    return pref.length ? pref : sweeps.slice(0, 2).map((s) => s.key);
  }, [picked, sweeps]);
  const toggle = (key) => setPicked(selected.includes(key) ? selected.filter((k) => k !== key) : [...selected, key].slice(-4));
  const chosen = sweeps.filter((s) => selected.includes(s.key));
  const thetas = useMemo(() => Array.from(new Set(chosen.flatMap((s) => s.theta))).sort((a, b) => a - b), [chosen]);
  const sweepSeries = chosen.map((s, i) => {
    const idx = new Map(s.theta.map((t, j) => [t, j]));
    const y = thetas.map((t) => (idx.has(t) ? (metric === "N" ? s.N_mean[idx.get(t)] : metric === "V" ? s.V_mean[idx.get(t)] : s.spent_mean[idx.get(t)]) : null));
    const se = thetas.map((t) => (idx.has(t) ? (metric === "N" ? s.N_se[idx.get(t)] : metric === "V" ? s.V_se[idx.get(t)] : 0) : null));
    return { name: s.key, color: S(i + 1), y, band: metric === "spent" ? null : { lo: y.map((v, j) => (v == null ? null : v - se[j])), hi: y.map((v, j) => (v == null ? null : v + se[j])) }, dots: true, format: (v) => fmtNum(v, 1) };
  });
  const marks = metric === "N" ? chosen.map((s, i) => { const j = thetas.indexOf(s.argmax_theta); const jj = s.theta.indexOf(s.argmax_theta); return j < 0 || jj < 0 ? null : { x: j, y: s.N_mean[jj], color: S(i + 1), label: `θ* = ${s.argmax_theta}` }; }).filter(Boolean) : [];
  const groups = useMemo(() => { const g = {}; for (const s of sweeps) (g[s.group] = g[s.group] || []).push(s); return g; }, [sweeps]);
  const pt = (ptQ.data && ptQ.data.tables) || [];
  const tp = (tpQ.data && tpQ.data.curves) || [];
  const gte = (gteQ.data && gteQ.data.gte) || [];
  const ev = (evQ.data && evQ.data.tables) || [];
  const figs = (figQ.data && figQ.data.figures) || [];
  const [showEv, setShowEv] = useState(false);
  return html`<div className="stack">
    <div className="card">
      <div className="card-head"><h2>Đường N(π<sub>θ</sub>) theo θ: tìm θ* để tắt khuyến mãi</h2><span className="hint">results/theta_sweep.parquet · dải = ± 1 SE theo seed · chấm đậm = argmax</span></div>
      <div className="row" style=${{ marginBottom: 8 }}>
        <div className="seg">${[["N", "N(π): chuyến hoàn thành"], ["V", "V(π): lợi nhuận"], ["spent", "chi voucher"]].map(([m, l]) => html`<button key=${m} className=${metric === m ? "on" : ""} onClick=${() => setMetric(m)}>${l}</button>`)}</div>
        <span className="small muted">chọn tối đa 4 sweep; trục θ cách đều theo lưới</span>
      </div>
      ${chosen.length ? html`<${LineChart} x=${thetas.map((_, i) => i)} xLabels=${thetas.map((t) => String(t))} height=${300} series=${sweepSeries} marks=${marks}
        yFormat=${(v) => (metric === "N" ? fmtInt(v) : fmtUSD(v, 0))} yLabel=${metric === "N" ? "chuyến / cửa sổ" : "USD"} />` : html`<div className="empty">chưa có sweep nào trong runs/</div>`}
      <div className="grid cols-3" style=${{ marginTop: 10 }}>
        ${Object.entries(groups).map(([g, list]) => html`<div key=${g}><div className="small ink2" style=${{ marginBottom: 4 }}><b>runs/${g}</b></div>
          ${list.map((s) => html`<label key=${s.key} className="check small" style=${{ display: "flex" }}><input type="checkbox" checked=${selected.includes(s.key)} onChange=${() => toggle(s.key)} />
            <span>${s.name} <span className="muted">· ${s.n_seeds} seed · θ* = ${s.argmax_theta}${s.budget_B_usd ? ` · B ${fmtUSD(s.budget_B_usd, 0)}` : ""}</span></span></label>`)}</div>`)}
      </div>
    </div>
    ${pt.map((t) => {
      const rows = [...t.rows].sort((a, b) => (b.N_mean || 0) - (a.N_mean || 0));
      const ref = rows.find((r) => r.dN_vs_ref === 0);
      return html`<div className="card" key=${t.key}>
        <div className="card-head"><h2>N(π) của các chính sách dưới cùng B</h2><span className="hint">runs/${t.key} · ΔN so với ${ref ? ref.label : "tham chiếu"}, ghép cặp theo seed ± SE</span></div>
        <${BarChart} horizontal height=${Math.max(220, rows.length * 24 + 50)} categories=${rows.map((r) => r.label)} errors=${rows.map((r) => r.dN_vs_ref_se)} yFormat=${(v) => fmtSigned(v, 0)}
          series=${[{ name: "ΔN so với tham chiếu", color: S(1), values: rows.map((r) => r.dN_vs_ref) }]} legend=${false} />
        <${Table} rows=${rows} maxHeight=${320} columns=${[{ key: "label", label: "Nhãn" }, { key: "policy", label: "Chính sách" }, { key: "score_fn", label: "Hàm điểm" }, { key: "theta", label: "θ", num: true, fmt: (v) => (v == null ? "–" : fmtNum(v, 2)) },
          { key: "kappa", label: "κ", num: true, fmt: (v) => (v == null ? "–" : fmtNum(v, 3)) }, { key: "N_mean", label: "N ± SE", num: true, fmt: (v, r) => `${fmtNum(v, 1)} ± ${fmtNum(r.N_se, 1)}` },
          { key: "V_mean", label: "V (USD)", num: true, fmt: (v) => fmtNum(v, 0) }, { key: "spent_mean", label: "Chi (USD)", num: true, fmt: (v) => fmtNum(v, 0) }, { key: "share_cells_off", label: "% ô tắt", num: true, fmt: (v) => fmtPct(v) }]} />
      </div>`;
    })}
    <div className="grid cols-2">
      ${tp.map((c) => html`<div className="card" key=${c.key}>
        <div className="card-head"><h2>Đường throughput (A1)</h2><span className="hint">runs/${c.key} · ${c.fleet_size} xe luôn online, giờ tham chiếu</span></div>
        <${LineChart} x=${c.rows.map((r) => r.demand_scale)} height=${230} xFormat=${(v) => "×" + fmtNum(v, 2)} yLabel="chuyến / giờ"
          series=${[{ name: "hoàn thành / giờ", color: S(1), y: c.rows.map((r) => r.completed_per_h), dots: true }, { name: "lượt đặt / giờ", color: S(2), y: c.rows.map((r) => r.requests_per_h), dash: true }]} />
        <${LineChart} x=${c.rows.map((r) => r.demand_scale)} height=${170} xFormat=${(v) => "×" + fmtNum(v, 2)} yFormat=${(v) => fmtNum(v, 1)} yLabel="phút"
          series=${[{ name: "ETA đón trung bình (phút)", color: S(3), y: c.rows.map((r) => r.mean_pickup_eta_min), format: (v) => fmtNum(v, 2) }]} legend=${false} />
        <p className="small muted">Throughput tăng rồi giảm khi cầu vượt cung (wild goose chase): căn cứ để cắt voucher ở vùng căng.</p>
      </div>`)}
      <div className="card">
        <div className="card-head"><h2>GTE = N(all_on) − N(all_off)</h2><span className="hint">không ngân sách, ghép cặp theo seed</span></div>
        <div className="stack">${gte.map((g) => html`<div key=${g.key}>
          <div className="small ink2"><b>runs/${g.key}</b> · ${g.n_seeds} seed</div>
          <div className="grid cols-3"><${StatTile} label="N(all_on)" value=${fmtNum(g.N_on, 1)} /><${StatTile} label="N(all_off)" value=${fmtNum(g.N_off, 1)} /><${StatTile} label="GTE ± SE" value=${fmtSigned(g.GTE, 1)} sub=${`± ${fmtNum(g.GTE_se, 1)}`} /></div></div>`)}
          ${gte.length ? null : html`<div className="empty">không có bảng gte</div>`}</div>
      </div>
    </div>
    <div className="card">
      <div className="card-head"><h2>Hình trong notebook kết quả</h2><span className="hint">docs/figures/</span></div>
      ${figs.length ? html`<div className="figure-grid">${figs.map((f) => html`<div key=${f.name}><a href=${f.url} target="_blank"><img src=${f.url} alt=${f.name} loading="lazy" /></a><div className="cap">${f.name}</div></div>`)}</div>` : html`<div className="empty">chưa có hình</div>`}
    </div>
    <div className="card">
      <div className="card-head"><h2>Mọi bảng policy_results trong runs/</h2><button className="btn sm" onClick=${() => setShowEv(!showEv)}>${showEv ? "ẩn" : `hiện ${ev.length} bảng`}</button></div>
      ${showEv ? html`<${Table} maxHeight=${480} rows=${ev.flatMap((t) => t.rows.map((r) => ({ ...r, key: t.key })))} columns=${[{ key: "key", label: "Thư mục" }, { key: "policy", label: "Chính sách" }, { key: "theta", label: "θ", num: true, fmt: (v) => (v == null ? "–" : fmtNum(v, 2)) }, { key: "n_seeds", label: "seed", num: true },
        { key: "N_mean", label: "N ± SE", num: true, fmt: (v, r) => `${fmtNum(v, 1)}${r.N_se != null ? ` ± ${fmtNum(r.N_se, 1)}` : ""}` }, { key: "V_mean", label: "V", num: true, fmt: (v) => fmtNum(v, 0) }, { key: "spent_mean", label: "Chi", num: true, fmt: (v) => fmtNum(v, 0) }, { key: "budget_B_usd", label: "B/kỳ", num: true, fmt: (v) => (v == null ? "–" : fmtNum(v, 0)) }, { key: "share_cells_off", label: "% ô tắt", num: true, fmt: (v) => fmtPct(v) }]} />` : null}
    </div>
  </div>`;
}
