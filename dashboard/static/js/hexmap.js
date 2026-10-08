// Hex map with the driver animation: SVG for the cells (promotion state, slack), canvas for drivers,
// waiting riders and event pulses. Frames come from /api/runs/{id}/frames (one per tick); between two
// frames a moving driver is interpolated along the display vector between its origin and target cell.
import { html, useState, useEffect, useRef, useMemo, api, cssVar, driverColors, fmtClock, fmtNum, fmtInt,
  seqColor, SEQ, clamp, DRIVER_LABEL } from "./lib.js";

const SQRT3 = Math.sqrt(3);
const EV = { request: 0, match: 1, pickup: 2, complete: 3, abandon: 4, cancel: 5, offer: 6, blocked: 7 };

export function emptyFrames() {
  return { t: [], status: [], cell: [], origin: [], move_start: [], busy_until: [], idle: [], enroute: [], ontrip: [],
    waiting: [], order_counts: [], session_counts: [], ledger: [], events: [] };
}

function appendFrames(F, chunk) {
  for (const k of Object.keys(F)) if (chunk[k]) for (const v of chunk[k]) F[k].push(v);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** Progressive loading of a run's frames: one loop per run id that keeps fetching while frames are missing
 *  (the run may still be in progress); it reads the latest server count from a ref, so it never stalls. */
export function useFrames(runId, nFramesServer, running) {
  const framesRef = useRef(emptyFrames());
  const latest = useRef({ nFramesServer, running });
  latest.current = { nFramesServer, running };
  const [loaded, setLoaded] = useState(0);
  useEffect(() => {
    framesRef.current = emptyFrames();
    setLoaded(0);
    if (!runId) return undefined;
    let alive = true;
    const F = framesRef.current;
    (async () => {
      while (alive) {
        const start = F.t.length;
        const { nFramesServer: nS, running: inProgress } = latest.current;
        if (start >= nS && !inProgress) { await sleep(700); continue; }
        let r;
        try { r = await api(`/api/runs/${runId}/frames?start=${start}&count=240`); } catch (e) { await sleep(2000); continue; }
        if (!alive) break;
        if (r.frames === 0) { await sleep(r.done ? 700 : 1200); continue; }
        appendFrames(F, r);
        setLoaded(F.t.length);
      }
    })();
    return () => { alive = false; };
  }, [runId]);
  return { framesRef, loaded };
}

/** Playback clock: tau = continuous frame index; speed = simulated minutes per real second. */
export function usePlayer(tick_s = 60) {
  const ref = useRef({ tau: 0, playing: false, speed: 10, nFrames: 0, follow: false, last: null });
  const [ui, setUi] = useState({ tau: 0, playing: false, speed: 10, follow: false });
  useEffect(() => {
    let raf;
    let lastUi = 0;
    const loop = (ts) => {
      const p = ref.current;
      const maxTau = Math.max(0, p.nFrames - 1);
      if (p.playing) {
        const dt = p.last == null ? 0 : Math.min(0.25, (ts - p.last) / 1000);
        p.tau += dt * p.speed * 60 / tick_s;
        if (p.tau >= maxTau) { p.tau = maxTau; if (!p.follow) p.playing = false; }
      } else if (p.follow) { p.tau = maxTau; }
      p.last = ts;
      if (ts - lastUi > 90) { lastUi = ts; setUi({ tau: p.tau, playing: p.playing, speed: p.speed, follow: p.follow }); }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [tick_s]);
  const set = (patch) => {
    Object.assign(ref.current, patch);
    const p = ref.current;
    setUi({ tau: p.tau, playing: p.playing, speed: p.speed, follow: p.follow });
  };
  return { ref, ui, set };
}

export function fitGeometry(geometry, width, height, margin = 30) {
  const xs = geometry.cells.map((c) => c.x), ys = geometry.cells.map((c) => c.y);
  const minx = Math.min(...xs) - SQRT3 / 2, maxx = Math.max(...xs) + SQRT3 / 2;
  const miny = Math.min(...ys) - 1, maxy = Math.max(...ys) + 1;
  const scale = Math.min((width - 2 * margin) / (maxx - minx), (height - 2 * margin) / (maxy - miny));
  const ox = (width - (maxx + minx) * scale) / 2, oy = (height - (maxy + miny) * scale) / 2;
  return { scale, ox, oy, px: (x) => ox + x * scale, py: (y) => oy + y * scale };
}

function hexPoints(cx, cy, r) {
  const pts = [];
  for (let k = 0; k < 6; k++) { const a = (Math.PI / 180) * (60 * k - 30); pts.push(`${(cx + r * Math.cos(a)).toFixed(1)},${(cy + r * Math.sin(a)).toFixed(1)}`); }
  return pts.join(" ");
}

const GOLD = 0.6180339887;
function jitter(d) { const a = d * 2.39996323; const r = 0.52 * Math.sqrt((d * GOLD) % 1); return [r * Math.cos(a), r * Math.sin(a)]; }

/** Position (hex units) of driver d at display time tDisp using frame k. Returns [x, y, status] or null. */
export function driverPos(F, k, d, tDisp, cells, disp, jit) {
  const st = F.status[k][d];
  if (st === 0) return null;
  const c = F.cell[k][d];
  if (c < 0) return null;
  const [jx, jy] = jit[d];
  if (st === 1) return [cells[c].x + jx, cells[c].y + jy, st];
  const o = F.origin[k][d];
  if (o < 0 || o === c) return [cells[c].x + jx, cells[c].y + jy, st];
  const ms = F.move_start[k][d], bu = F.busy_until[k][d];
  let p = bu > ms ? (tDisp - ms) / (bu - ms) : 1;
  p = clamp(p, 0, 1);
  const v = disp[o][c];
  if (p < 0.5) return [cells[o].x + p * v[0] + jx, cells[o].y + p * v[1] + jy, st];
  return [cells[c].x - (1 - p) * v[0] + jx, cells[c].y - (1 - p) * v[1] + jy, st];
}

export function phaseOf(t, clock) {
  if (!clock) return "";
  if (t < clock.window_start_s) return "warm-up (không tính)";
  if (t < clock.window_end_s) return "cửa sổ đánh giá";
  return "cool-down (đóng đơn còn mở)";
}

/**
 * HexMap. framesRef: frames; player: playback ref (reads tau at 60 fps); k/tDisp: current frame and time (state);
 * slots: cell_matrix of /slots; mode: "promo" | "slack" | "waiting" | "cluster"; pulses: Set of groups.
 */
export function HexMap({ geometry, slots, framesRef, player, k, tDisp, mode, selected, onSelect, pulses, width, height,
  theta, clock, slackCap = 3 }) {
  const canvasRef = useRef(null);
  const [hover, setHover] = useState(null);
  const fit = useMemo(() => fitGeometry(geometry, width, height), [geometry, width, height]);
  const cells = geometry.cells;
  const jit = useMemo(() => Array.from({ length: geometry.n_drivers }, (_, d) => jitter(d)), [geometry.n_drivers]);
  const slotS = clock ? clock.slot_s : 900;
  const slotIdx = slots && slots.n_slots ? Math.min(slots.n_slots - 1, Math.max(0, Math.floor(tDisp / slotS))) : -1;
  const promo = slotIdx >= 0 ? slots.promo_on[slotIdx] : null;
  const sHat = slotIdx >= 0 ? slots.s_hat[slotIdx] : null;
  const cluster = slotIdx >= 0 ? slots.cluster_id[slotIdx] : null;
  const seq = useMemo(() => SEQ(), []);
  const series = useMemo(() => ["--s1", "--s2", "--s3", "--s4", "--s5", "--s6", "--s7", "--s8"].map(cssVar), []);
  const F = framesRef.current;
  const haveFrame = F.t.length > 0 && k >= 0 && k < F.t.length;
  const waiting = haveFrame ? F.waiting[k] : null;

  const fillOf = (c) => {
    const on = promo ? !!promo[c] : true;
    if (mode === "slack") { const v = sHat ? sHat[c] : null; return v == null ? cssVar("--surface-2") : seqColor(Math.min(v, slackCap), slackCap, seq); }
    if (mode === "waiting") { const v = waiting ? waiting[c] : 0; return v > 0 ? seqColor(Math.min(v, 6), 6, seq) : cssVar("--surface-2"); }
    if (mode === "cluster") { const id = cluster ? cluster[c] : -1; return id < 0 ? cssVar("--surface-2") : series[id % 8] + "55"; }
    return on ? "var(--promo-on)" : cssVar("--surface-2");
  };

  // canvas: drivers, waiting riders and pulses at 60 fps
  useEffect(() => {
    const cv = canvasRef.current;
    if (!cv) return undefined;
    const dpr = window.devicePixelRatio || 1;
    cv.width = width * dpr; cv.height = height * dpr;
    const ctx = cv.getContext("2d");
    const colors = driverColors();
    const surface = cssVar("--surface");
    const magenta = cssVar("--s5"), yellow = cssVar("--s4"), red = cssVar("--s8"), orange = cssVar("--s2"), blue = cssVar("--s1"), gray = cssVar("--muted");
    let raf;
    const draw = () => {
      const Fr = framesRef.current;
      const p = player.current;
      const n = Fr.t.length;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, width, height);
      if (n > 0) {
        const kk = clamp(Math.floor(p.tau), 0, n - 1);
        const frac = clamp(p.tau - kk, 0, 1);
        const tick = n > 1 ? Fr.t[1] - Fr.t[0] : 60;
        const tD = Fr.t[kk] + frac * tick;
        const s = fit.scale;
        // pulses: events of the last L ticks, L grows with speed so they stay visible
        if (pulses.size) {
          const L = clamp(Math.round(p.speed * 0.5), 1, 30);
          for (let j = Math.max(0, kk - L + 1); j <= kk; j++) {
            const age = clamp((p.tau - j) / L, 0, 1);
            const a = 1 - age;
            const evs = Fr.events[j] || [];
            evs.forEach((e, idx) => {
              const code = e[0], ca = e[1], cb = e[2];
              if (ca < 0) return;
              const cx = fit.px(cells[ca].x), cy = fit.py(cells[ca].y);
              if (code === EV.match && pulses.has("match") && cb >= 0) {
                const v = geometry.disp[ca][cb];
                ctx.strokeStyle = orange; ctx.globalAlpha = 0.8 * a; ctx.lineWidth = 2;
                ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + v[0] * s, cy + v[1] * s); ctx.stroke();
              } else if (code === EV.complete && pulses.has("match")) {
                ctx.strokeStyle = blue; ctx.globalAlpha = 0.7 * a; ctx.lineWidth = 1.5;
                ctx.beginPath(); ctx.arc(cx, cy, s * (0.18 + 0.4 * age), 0, 2 * Math.PI); ctx.stroke();
              } else if ((code === EV.offer || code === EV.blocked) && pulses.has("offer")) {
                const ang = idx * 2.39996323, rr = s * 0.62 * Math.sqrt((idx * GOLD) % 1);
                const x = cx + rr * Math.cos(ang), y = cy + rr * Math.sin(ang) - 6 * age;
                ctx.globalAlpha = 0.95 * a;
                if (code === EV.offer) { ctx.fillStyle = yellow; ctx.fillRect(x - 3, y - 2, 6, 4); }
                else { ctx.strokeStyle = red; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(x - 3, y - 3); ctx.lineTo(x + 3, y + 3); ctx.moveTo(x + 3, y - 3); ctx.lineTo(x - 3, y + 3); ctx.stroke(); }
              } else if ((code === EV.cancel || code === EV.abandon) && pulses.has("cancel")) {
                ctx.strokeStyle = code === EV.cancel ? orange : gray; ctx.globalAlpha = 0.9 * a; ctx.lineWidth = 2;
                const r = 5 + 4 * age;
                ctx.beginPath(); ctx.moveTo(cx - r, cy - r); ctx.lineTo(cx + r, cy + r); ctx.moveTo(cx + r, cy - r); ctx.lineTo(cx - r, cy + r); ctx.stroke();
              } else if (code === EV.request && pulses.has("request")) {
                const ang = idx * 2.39996323 + 1, rr = s * 0.7;
                ctx.fillStyle = magenta; ctx.globalAlpha = 0.9 * a;
                ctx.beginPath(); ctx.arc(cx + rr * Math.cos(ang), cy + rr * Math.sin(ang), 3 + 3 * age, 0, 2 * Math.PI); ctx.fill();
              }
            });
          }
          ctx.globalAlpha = 1;
        }
        // waiting riders: small magenta rings around the cell centre (one per waiting order, up to 8)
        const W = Fr.waiting[kk];
        for (let c = 0; c < cells.length; c++) {
          const w = W[c];
          if (!w) continue;
          const cx = fit.px(cells[c].x), cy = fit.py(cells[c].y);
          const m = Math.min(8, w);
          for (let i = 0; i < m; i++) {
            const ang = -Math.PI / 2 + i * (2 * Math.PI / 8);
            ctx.strokeStyle = magenta; ctx.lineWidth = 2;
            ctx.beginPath(); ctx.arc(cx + 0.78 * s * Math.cos(ang), cy + 0.78 * s * Math.sin(ang), 3.2, 0, 2 * Math.PI); ctx.stroke();
          }
        }
        // drivers
        const r = clamp(s * 0.085, 3, 6);
        for (let d = 0; d < geometry.n_drivers; d++) {
          const pos = driverPos(Fr, kk, d, tD, cells, geometry.disp, jit);
          if (!pos) continue;
          const st = pos[2];
          const col = st === 1 ? colors.idle : st === 2 ? colors.en_route : st === 3 ? colors.on_trip : colors.repositioning;
          const x = fit.px(pos[0]), y = fit.py(pos[1]);
          ctx.beginPath(); ctx.arc(x, y, r + 1.5, 0, 2 * Math.PI); ctx.fillStyle = surface; ctx.fill();
          ctx.beginPath(); ctx.arc(x, y, r, 0, 2 * Math.PI); ctx.fillStyle = col; ctx.fill();
        }
      }
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [geometry, fit, width, height, pulses, framesRef, player, jit, cells]);

  const hexR = fit.scale * 0.985;
  const ink2 = cssVar("--ink-2");
  const hatchId = "hatch-off";
  const tip = hover != null ? (() => {
    const c = hover;
    const on = promo ? !!promo[c] : null;
    const s = sHat ? sHat[c] : null;
    const lines = [`Ô ${c}  (q ${cells[c].q}, r ${cells[c].r})`];
    if (on != null) lines.push(`Voucher: ${on ? "BẬT" : "TẮT"}${theta != null ? ` · ŝ = ${s == null ? "–" : fmtNum(s, 2)} so với θ = ${fmtNum(theta, 2)}` : ""}`);
    if (haveFrame) lines.push(`Xe: rảnh ${F.idle[k][c]}, đi đón ${F.enroute[k][c]}, chở khách ${F.ontrip[k][c]} · khách chờ ${F.waiting[k][c]}`);
    if (slotIdx >= 0 && slots.n_offers[slotIdx] && slots.n_offers[slotIdx][c] != null) lines.push(`Slot này: ${slots.n_offers[slotIdx][c]} voucher, ${slots.n_requests[slotIdx][c]} đặt, ${slots.n_completed[slotIdx][c]} hoàn thành`);
    lines.push(`Trọng số cầu ${fmtNum(cells[c].weight, 2)} · ${fmtInt(cells[c].riders_home)} rider ở đây`);
    return lines;
  })() : null;

  return html`<div className="map-wrap" style=${{ width, height }}>
    <svg width=${width} height=${height} viewBox=${`0 0 ${width} ${height}`}>
      <defs>
        <pattern id=${hatchId} patternUnits="userSpaceOnUse" width="8" height="8" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="8" stroke=${cssVar("--axis")} strokeWidth="1.5" />
        </pattern>
      </defs>
      ${cells.map((c) => {
        const cx = fit.px(c.x), cy = fit.py(c.y);
        const on = promo ? !!promo[c.id] : true;
        const cls = "hex" + (selected === c.id ? " sel" : "") + (hover === c.id ? " hover" : "");
        return html`<g key=${c.id}>
          <polygon className=${cls} points=${hexPoints(cx, cy, hexR)} fill=${fillOf(c.id)}
            onMouseEnter=${() => setHover(c.id)} onMouseLeave=${() => setHover((h) => (h === c.id ? null : h))}
            onClick=${() => onSelect && onSelect(selected === c.id ? null : c.id)} />
          ${mode === "promo" && !on ? html`<polygon points=${hexPoints(cx, cy, hexR)} fill=${`url(#${hatchId})`} opacity="0.55" style=${{ pointerEvents: "none" }} />` : null}
          <text className="cell-id" x=${cx} y=${cy - hexR * 0.55} textAnchor="middle">${c.id}</text>
          ${mode === "slack" && sHat ? html`<text className="cell-val" x=${cx} y=${cy + hexR * 0.72} textAnchor="middle">${sHat[c.id] == null ? "–" : fmtNum(Math.min(sHat[c.id], 99), 1)}</text>` : null}
          ${mode === "cluster" && cluster && cluster[c.id] >= 0 ? html`<text className="cell-val" x=${cx} y=${cy + hexR * 0.72} textAnchor="middle">cụm ${cluster[c.id]}</text>` : null}
          ${mode === "promo" && !on ? html`<text className="cell-val" x=${cx} y=${cy + hexR * 0.72} textAnchor="middle" style=${{ fill: ink2 }}>TẮT</text>` : null}
        </g>`;
      })}
    </svg>
    <canvas ref=${canvasRef} style=${{ width, height }}></canvas>
    <div className="clock"><b>${fmtClock(tDisp)}</b> <span className="muted small">· slot ${slotIdx >= 0 ? slotIdx : "–"}</span></div>
    <div className="phase">${phaseOf(tDisp, clock)}</div>
    ${tip ? html`<div className="tooltip" style=${{ left: Math.min(fit.px(cells[hover].x) + 20, width - 260), top: Math.max(4, fit.py(cells[hover].y) - 20) }}>
      ${tip.map((l, i) => html`<div key=${i} className=${i === 0 ? "t-head" : ""}>${l}</div>`)}</div>` : null}
  </div>`;
}

/** Static hex map: one value per cell on the sequential ramp (e.g. slots cut per cell), with labels. */
export function HexStatic({ geometry, values, max = null, format = (v) => fmtInt(v), width = 420, height = 360, title = "" }) {
  const fit = useMemo(() => fitGeometry(geometry, width, height, 22), [geometry, width, height]);
  const seq = useMemo(() => SEQ(), []);
  const vmax = max != null ? max : Math.max(1, ...values.filter((v) => v != null));
  const r = fit.scale * 0.985;
  return html`<div>
    ${title ? html`<div className="chart-title">${title}</div>` : null}
    <svg width=${width} height=${height} viewBox=${`0 0 ${width} ${height}`} style=${{ display: "block", maxWidth: "100%", height: "auto" }}>
      ${geometry.cells.map((c) => {
        const cx = fit.px(c.x), cy = fit.py(c.y);
        const v = values[c.id];
        const fill = v == null || v === 0 ? cssVar("--surface-2") : seqColor(v, vmax, seq);
        const dark = v != null && v / vmax > 0.55;
        return html`<g key=${c.id}><title>${`Ô ${c.id}: ${format(v)}`}</title>
          <polygon points=${hexPoints(cx, cy, r)} fill=${fill} stroke="var(--surface)" strokeWidth="2" />
          <text x=${cx} y=${cy - r * 0.35} textAnchor="middle" style=${{ fontSize: 9, fill: dark ? "#fff" : cssVar("--muted") }}>${c.id}</text>
          <text x=${cx} y=${cy + r * 0.35} textAnchor="middle" style=${{ fontSize: 11, fontWeight: 600, fill: dark ? "#fff" : cssVar("--ink-2") }}>${v == null ? "–" : format(v)}</text></g>`;
      })}
    </svg>
    <div className="legend"><span><i className="swatch" style=${{ background: "linear-gradient(90deg, var(--seq-100), var(--seq-700))" }}></i>0 → ${format(vmax)}</span></div>
  </div>`;
}

export function MapLegend({ mode, hasCluster = false }) {
  const col = driverColors();
  return html`<div className="legend">
    ${["idle", "en_route", "on_trip", "repositioning"].map((s) => html`<span key=${s}><i className="dot" style=${{ background: col[s] }}></i>${DRIVER_LABEL[s]}</span>`)}
    <span><i className="dot" style=${{ background: "transparent", border: `2px solid ${cssVar("--s5")}`, width: 8, height: 8 }}></i>khách đang chờ ghép</span>
    ${mode === "promo" ? html`<span><i className="swatch" style=${{ background: "var(--promo-on)", border: "1px solid var(--border)" }}></i>ô đang bật voucher</span>` : null}
    ${mode === "promo" ? html`<span><i className="swatch" style=${{ background: "repeating-linear-gradient(45deg, var(--axis) 0 1.5px, transparent 1.5px 6px)", border: "1px solid var(--border)" }}></i>ô bị cắt (ŝ ${"<"} θ)</span>` : null}
    ${mode === "slack" ? html`<span><i className="swatch" style=${{ background: "linear-gradient(90deg, var(--seq-100), var(--seq-700))" }}></i>ŝ thấp → cao (cắt ở 3)</span>` : null}
    ${mode === "waiting" ? html`<span><i className="swatch" style=${{ background: "linear-gradient(90deg, var(--seq-100), var(--seq-700))" }}></i>số khách chờ 0 → 6+ (còn chờ ở cuối tick, chưa có xe)</span>` : null}
    ${mode === "cluster" ? (hasCluster ? html`<span><i className="swatch" style=${{ background: "linear-gradient(90deg, var(--s1), var(--s2), var(--s3), var(--s4))" }}></i>mỗi màu một cụm switchback</span>`
      : html`<span className="muted">chỉ có dữ liệu cụm khi chính sách là experiment (cluster_switchback)</span>`) : null}
  </div>`;
}
