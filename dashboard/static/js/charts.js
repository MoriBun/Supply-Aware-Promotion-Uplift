// SVG charts following the dataviz method: thin marks, hairline solid grid, one axis per chart,
// crosshair tooltip on lines, per-mark tooltip on bars and heat cells, legend for >= 2 series.
import { html, useState, useRef, useMemo, useWidth, fmtNum, fmtInt, cssVar, clamp } from "./lib.js";

function niceTicks(min, max, n = 5) {
  if (!(max > min)) { max = min + 1; }
  const span = max - min;
  const step0 = span / Math.max(1, n);
  const p = Math.pow(10, Math.floor(Math.log10(step0)));
  const cand = [1, 2, 2.5, 5, 10].map((m) => m * p);
  const step = cand.find((s) => span / s <= n + 1) || cand[cand.length - 1];
  const t0 = Math.ceil(min / step) * step;
  const out = [];
  for (let v = t0; v <= max + 1e-9; v += step) out.push(+v.toFixed(10));
  return out;
}

const M = { top: 10, right: 14, bottom: 30, left: 48 };

export function Legend({ items }) {
  if (!items || items.length < 2) return null;
  return html`<div className="legend">${items.map((it) => html`<span key=${it.name}>
    ${it.kind === "line" ? html`<i className="line-key" style=${{ background: it.color }}></i>` : html`<i className="swatch" style=${{ background: it.color }}></i>`}${it.name}</span>`)}</div>`;
}

/**
 * LineChart: x numeric (or ordinal via xLabels), series [{name, color, y, band:{lo,hi}, dash, dots}],
 * hlines [{y,label,color}], bands [{x0,x1}] shaded x ranges, marks [{x,y,label,color}].
 */
export function LineChart({ x, series, height = 220, yFormat = (v) => fmtNum(v, 0), xFormat = (v) => fmtNum(v, 0),
  xLabels = null, hlines = [], bands = [], marks = [], yDomain = null, yLabel = "", title = "", xTicks = null, legend = true }) {
  const ref = useRef(null);
  const width = useWidth(ref, 640);
  const [hover, setHover] = useState(null);
  const n = x ? x.length : 0;
  const pw = Math.max(50, width - M.left - M.right);
  const ph = height - M.top - M.bottom;
  const xmin = n ? Math.min(...x) : 0, xmax = n ? Math.max(...x) : 1;
  let ymin = Infinity, ymax = -Infinity;
  for (const s of series) {
    for (const v of s.y) if (v != null && Number.isFinite(v)) { ymin = Math.min(ymin, v); ymax = Math.max(ymax, v); }
    if (s.band) for (let i = 0; i < n; i++) { const lo = s.band.lo[i], hi = s.band.hi[i]; if (lo != null) ymin = Math.min(ymin, lo); if (hi != null) ymax = Math.max(ymax, hi); }
  }
  for (const h of hlines) if (h.y != null && Number.isFinite(h.y)) { ymin = Math.min(ymin, h.y); ymax = Math.max(ymax, h.y); }
  if (!Number.isFinite(ymin)) { ymin = 0; ymax = 1; }
  if (yDomain) { if (yDomain[0] != null) ymin = yDomain[0]; if (yDomain[1] != null) ymax = yDomain[1]; }
  else { if (ymin > 0 && ymin < 0.25 * ymax) ymin = 0; const pad = (ymax - ymin) * 0.08 || 1; ymax += pad; if (ymin !== 0) ymin -= pad; }
  const sx = (v) => M.left + (xmax > xmin ? (v - xmin) / (xmax - xmin) : 0.5) * pw;
  const sy = (v) => M.top + (1 - (v - ymin) / (ymax - ymin || 1)) * ph;
  const yt = niceTicks(ymin, ymax, 5);
  const xt = xTicks || (xLabels ? x : niceTicks(xmin, xmax, Math.min(8, Math.max(2, Math.floor(pw / 80)))));

  const path = (ys) => {
    let d = "", pen = false;
    for (let i = 0; i < n; i++) {
      const v = ys[i];
      if (v == null || !Number.isFinite(v)) { pen = false; continue; }
      d += (pen ? "L" : "M") + sx(x[i]).toFixed(1) + " " + sy(v).toFixed(1);
      pen = true;
    }
    return d;
  };
  const area = (lo, hi) => {
    const up = [], down = [];
    for (let i = 0; i < n; i++) if (lo[i] != null && hi[i] != null) { up.push([sx(x[i]), sy(hi[i])]); down.push([sx(x[i]), sy(lo[i])]); }
    if (!up.length) return "";
    return "M" + up.map((p) => p.map((v) => v.toFixed(1)).join(" ")).join("L") + "L" + down.reverse().map((p) => p.map((v) => v.toFixed(1)).join(" ")).join("L") + "Z";
  };
  const onMove = (e) => {
    const r = ref.current.getBoundingClientRect();
    const px = e.clientX - r.left;
    let best = -1, bd = Infinity;
    for (let i = 0; i < n; i++) { const d = Math.abs(sx(x[i]) - px); if (d < bd) { bd = d; best = i; } }
    setHover(best >= 0 ? { i: best, px, py: e.clientY - r.top } : null);
  };
  const ink = cssVar("--ink-2");
  return html`<div className="chart" ref=${ref} onMouseMove=${onMove} onMouseLeave=${() => setHover(null)}>
    ${title ? html`<div className="chart-title">${title}</div>` : null}
    <svg viewBox=${`0 0 ${width} ${height}`} width=${width} height=${height}>
      ${bands.map((b, i) => html`<rect key=${"b" + i} x=${sx(b.x0)} y=${M.top} width=${Math.max(0, sx(b.x1) - sx(b.x0))} height=${ph} fill=${b.color || "var(--promo-on)"} />`)}
      <g className="axis">
        ${yt.map((v) => html`<g key=${"y" + v}><line className="gridline" x1=${M.left} x2=${M.left + pw} y1=${sy(v)} y2=${sy(v)} /><text x=${M.left - 6} y=${sy(v) + 4} textAnchor="end">${yFormat(v)}</text></g>`)}
        ${xt.map((v, i) => html`<text key=${"x" + i} x=${sx(v)} y=${height - 8} textAnchor="middle">${xLabels ? xLabels[i] : xFormat(v)}</text>`)}
        <line x1=${M.left} x2=${M.left + pw} y1=${M.top + ph} y2=${M.top + ph} />
        ${yLabel ? html`<text x=${M.left} y=${M.top - 2} textAnchor="start" style=${{ fontSize: 11 }}>${yLabel}</text>` : null}
      </g>
      ${series.map((s) => s.band ? html`<path key=${"band" + s.name} d=${area(s.band.lo, s.band.hi)} fill=${s.color} opacity="0.12" />` : null)}
      ${hlines.map((h, i) => html`<g key=${"h" + i}><line x1=${M.left} x2=${M.left + pw} y1=${sy(h.y)} y2=${sy(h.y)} stroke=${h.color || ink} strokeWidth="1.5" strokeDasharray=${h.dash === false ? null : "5 4"} />
        ${h.label ? html`<text x=${M.left + pw - 2} y=${sy(h.y) - 4} textAnchor="end" style=${{ fontSize: 11, fill: ink }}>${h.label}</text>` : null}</g>`)}
      ${series.map((s) => html`<path key=${"l" + s.name} d=${path(s.y)} fill="none" stroke=${s.color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" strokeDasharray=${s.dash ? "4 3" : null} opacity=${s.opacity ?? 1} />`)}
      ${series.map((s) => s.dots ? s.y.map((v, i) => v == null ? null : html`<circle key=${"d" + s.name + i} cx=${sx(x[i])} cy=${sy(v)} r="4" fill=${s.color} stroke="var(--surface)" strokeWidth="2" />`) : null)}
      ${marks.map((m, i) => html`<g key=${"m" + i}><circle cx=${sx(m.x)} cy=${sy(m.y)} r="6" fill=${m.color || ink} stroke="var(--surface)" strokeWidth="2" />
        ${m.label ? html`<text x=${sx(m.x) + 9} y=${sy(m.y) - 8} style=${{ fontSize: 11, fill: ink, fontWeight: 600 }}>${m.label}</text>` : null}</g>`)}
      ${hover ? html`<g><line x1=${sx(x[hover.i])} x2=${sx(x[hover.i])} y1=${M.top} y2=${M.top + ph} stroke=${cssVar("--axis")} strokeWidth="1" />
        ${series.map((s) => (s.y[hover.i] == null ? null : html`<circle key=${"h" + s.name} cx=${sx(x[hover.i])} cy=${sy(s.y[hover.i])} r="4" fill=${s.color} stroke="var(--surface)" strokeWidth="2" />`))}</g>` : null}
    </svg>
    ${hover ? html`<div className="tooltip" style=${{ left: Math.min(hover.px + 12, width - 150), top: Math.max(0, hover.py - 10) }}>
      <div className="t-head">${xLabels ? xLabels[hover.i] : xFormat(x[hover.i])}</div>
      ${series.map((s) => html`<div className="t-row" key=${s.name}><span><i className="line-key" style=${{ background: s.color }}></i> ${s.name}</span><b>${s.y[hover.i] == null ? "–" : (s.format || yFormat)(s.y[hover.i])}</b></div>`)}
    </div>` : null}
    ${legend ? html`<${Legend} items=${series.map((s) => ({ name: s.name, color: s.color, kind: "line" }))} />` : null}
  </div>`;
}

/** BarChart: categories (labels), series [{name,color,values}], stacked or grouped; horizontal option. */
export function BarChart({ categories, series, height = 220, stacked = false, yFormat = (v) => fmtInt(v), title = "",
  hlines = [], horizontal = false, maxBar = 24, legend = true, labelEvery = 1, errors = null }) {
  const ref = useRef(null);
  const width = useWidth(ref, 640);
  const [hover, setHover] = useState(null);
  const n = categories.length;
  const left = horizontal ? 110 : M.left;
  const pw = Math.max(50, width - left - M.right);
  const ph = height - M.top - M.bottom;
  let vmax = 0, vmin = 0;
  for (let i = 0; i < n; i++) {
    if (stacked) { let pos = 0, neg = 0; for (const s of series) { const v = s.values[i] || 0; if (v >= 0) pos += v; else neg += v; } vmax = Math.max(vmax, pos); vmin = Math.min(vmin, neg); }
    else for (const s of series) { const v = s.values[i] || 0; vmax = Math.max(vmax, v + (errors ? (errors[i] || 0) : 0)); vmin = Math.min(vmin, v - (errors ? (errors[i] || 0) : 0)); }
  }
  for (const h of hlines) { vmax = Math.max(vmax, h.y); vmin = Math.min(vmin, h.y); }
  vmax = vmax * 1.08 || 1;
  if (vmin < 0) vmin *= 1.08;
  const ticks = niceTicks(vmin, vmax, 5);
  const len = horizontal ? pw : ph;
  const sv = (v) => (v - vmin) / (vmax - vmin) * len;
  const slot = (horizontal ? ph : pw) / Math.max(1, n);
  const groupW = Math.min(maxBar * (stacked ? 1 : series.length), slot * 0.72);
  const barW = stacked ? groupW : groupW / series.length;
  const ink = cssVar("--ink-2");
  const rects = [];
  for (let i = 0; i < n; i++) {
    let acc0 = 0, accNeg = 0;
    series.forEach((s, j) => {
      const v = s.values[i] || 0;
      let base, top;
      if (stacked) { if (v >= 0) { base = acc0; acc0 += v; } else { base = accNeg; accNeg += v; } top = base + v; }
      else { base = 0; top = v; }
      const c0 = M.top * 0 + i * slot + (slot - groupW) / 2 + (stacked ? 0 : j * barW);
      const a = Math.min(sv(base), sv(top)), b = Math.max(sv(base), sv(top));
      const thick = Math.max(0, barW - 2);
      let x, y, w, h;
      if (horizontal) { x = left + a; y = M.top + c0; w = Math.max(0, b - a); h = thick; }
      else { x = left + c0; y = M.top + ph - b; w = thick; h = Math.max(0, b - a); }
      rects.push({ i, j, x, y, w, h, color: s.color, v, name: s.name, err: errors ? errors[i] : null, top });
    });
  }
  const zero = horizontal ? left + sv(0) : M.top + ph - sv(0);
  return html`<div className="chart" ref=${ref} onMouseLeave=${() => setHover(null)}>
    ${title ? html`<div className="chart-title">${title}</div>` : null}
    <svg viewBox=${`0 0 ${width} ${height}`} width=${width} height=${height}>
      <g className="axis">
        ${ticks.map((v) => horizontal
          ? html`<g key=${"t" + v}><line className="gridline" x1=${left + sv(v)} x2=${left + sv(v)} y1=${M.top} y2=${M.top + ph} /><text x=${left + sv(v)} y=${height - 8} textAnchor="middle">${yFormat(v)}</text></g>`
          : html`<g key=${"t" + v}><line className="gridline" x1=${left} x2=${left + pw} y1=${M.top + ph - sv(v)} y2=${M.top + ph - sv(v)} /><text x=${left - 6} y=${M.top + ph - sv(v) + 4} textAnchor="end">${yFormat(v)}</text></g>`)}
        ${categories.map((c, i) => (i % labelEvery ? null : horizontal
          ? html`<text key=${"c" + i} x=${left - 8} y=${M.top + i * slot + slot / 2 + 4} textAnchor="end" style=${{ fill: ink }}>${c}</text>`
          : html`<text key=${"c" + i} x=${left + i * slot + slot / 2} y=${height - 8} textAnchor="middle">${c}</text>`))}
        ${horizontal ? html`<line x1=${zero} x2=${zero} y1=${M.top} y2=${M.top + ph} />` : html`<line x1=${left} x2=${left + pw} y1=${zero} y2=${zero} />`}
      </g>
      ${rects.map((r, k) => html`<rect key=${k} x=${r.x} y=${r.y} width=${r.w} height=${r.h} fill=${r.color} rx="3"
        opacity=${hover && (hover.i !== r.i) ? 0.55 : 1}
        onMouseEnter=${() => setHover({ i: r.i, px: r.x + r.w / 2, py: r.y })} />`)}
      ${errors ? rects.filter((r) => r.err != null).map((r, k) => horizontal
        ? html`<line key=${"e" + k} x1=${left + sv(r.top - r.err)} x2=${left + sv(r.top + r.err)} y1=${r.y + r.h / 2} y2=${r.y + r.h / 2} stroke=${ink} strokeWidth="1.5" />`
        : html`<line key=${"e" + k} x1=${r.x + r.w / 2} x2=${r.x + r.w / 2} y1=${M.top + ph - sv(r.top - r.err)} y2=${M.top + ph - sv(r.top + r.err)} stroke=${ink} strokeWidth="1.5" />`) : null}
      ${hlines.map((h, i) => horizontal
        ? html`<line key=${"h" + i} x1=${left + sv(h.y)} x2=${left + sv(h.y)} y1=${M.top} y2=${M.top + ph} stroke=${h.color || ink} strokeWidth="1.5" strokeDasharray="5 4" />`
        : html`<g key=${"h" + i}><line x1=${left} x2=${left + pw} y1=${M.top + ph - sv(h.y)} y2=${M.top + ph - sv(h.y)} stroke=${h.color || ink} strokeWidth="1.5" strokeDasharray="5 4" />
          ${h.label ? html`<text x=${left + pw - 2} y=${M.top + ph - sv(h.y) - 4} textAnchor="end" style=${{ fontSize: 11, fill: ink }}>${h.label}</text>` : null}</g>`)}
    </svg>
    ${hover ? html`<div className="tooltip" style=${{ left: Math.min(hover.px + 12, width - 160), top: Math.max(0, hover.py - 10) }}>
      <div className="t-head">${categories[hover.i]}</div>
      ${series.map((s) => html`<div className="t-row" key=${s.name}><span><i className="swatch" style=${{ background: s.color }}></i> ${s.name}</span><b>${(s.format || yFormat)(s.values[hover.i])}${errors && errors[hover.i] != null ? ` ± ${yFormat(errors[hover.i])}` : ""}</b></div>`)}
    </div>` : null}
    ${legend ? html`<${Legend} items=${series.map((s) => ({ name: s.name, color: s.color, kind: "rect" }))} />` : null}
  </div>`;
}

/** Heatmap: values[r][c]; color(v, r, c) -> css color; mark(r, c) -> bool draws an outline; tooltip(r, c) -> lines[]. */
export function Heatmap({ values, rowLabels, colLabels = null, color, mark = null, onClick = null, tooltip = null,
  cellH = 12, selectedRow = -1, colLabelEvery = 8, title = "" }) {
  const ref = useRef(null);
  const width = useWidth(ref, 800);
  const [hover, setHover] = useState(null);
  const R = values.length, C = R ? values[0].length : 0;
  const left = 36, top = colLabels ? 18 : 4;
  const cellW = Math.max(2, (width - left - 6) / Math.max(1, C));
  const height = top + R * cellH + 6;
  const ink = cssVar("--ink");
  const cells = useMemo(() => {
    const out = [];
    for (let r = 0; r < R; r++) for (let c = 0; c < C; c++) out.push({ r, c, fill: color(values[r][c], r, c), m: mark ? mark(r, c) : false });
    return out;
  }, [values, color, mark, R, C]);
  return html`<div className="chart" ref=${ref} onMouseLeave=${() => setHover(null)}>
    ${title ? html`<div className="chart-title">${title}</div>` : null}
    <svg viewBox=${`0 0 ${width} ${height}`} width=${width} height=${height}>
      <g className="axis">
        ${rowLabels.map((l, r) => html`<text key=${"r" + r} x=${left - 5} y=${top + r * cellH + cellH * 0.78} textAnchor="end" style=${{ fontSize: Math.min(11, cellH - 1), fontWeight: r === selectedRow ? 700 : 400, fill: r === selectedRow ? ink : null }}>${l}</text>`)}
        ${colLabels ? colLabels.map((l, c) => (c % colLabelEvery ? null : html`<text key=${"c" + c} x=${left + c * cellW} y=${12} textAnchor="start">${l}</text>`)) : null}
      </g>
      ${cells.map((k) => html`<rect key=${k.r + "-" + k.c} x=${left + k.c * cellW} y=${top + k.r * cellH} width=${Math.max(1, cellW - 1)} height=${cellH - 1} fill=${k.fill}
        stroke=${k.m ? ink : "none"} strokeWidth=${k.m ? 1 : 0}
        onMouseEnter=${(e) => { const b = ref.current.getBoundingClientRect(); setHover({ r: k.r, c: k.c, px: e.clientX - b.left, py: e.clientY - b.top }); }}
        onClick=${onClick ? () => onClick(k.r, k.c) : null} style=${{ cursor: onClick ? "pointer" : "default" }} />`)}
      ${selectedRow >= 0 ? html`<rect x=${left} y=${top + selectedRow * cellH - 1} width=${C * cellW} height=${cellH + 1} fill="none" stroke=${ink} strokeWidth="1.5" />` : null}
    </svg>
    ${hover && tooltip ? html`<div className="tooltip" style=${{ left: Math.min(hover.px + 12, width - 170), top: Math.max(0, hover.py - 10) }}>
      ${tooltip(hover.r, hover.c).map((line, i) => html`<div key=${i} className=${i === 0 ? "t-head" : ""}>${line}</div>`)}</div>` : null}
  </div>`;
}

export function StatTile({ label, value, sub = null, hero = false, delta = null, deltaGoodUp = true }) {
  const up = delta != null && delta > 0;
  const cls = delta == null ? "" : ((up === deltaGoodUp) ? "delta up" : "delta down");
  return html`<div className=${"tile" + (hero ? " hero" : "")}>
    <div className="label">${label}</div>
    <div className="value">${value}</div>
    ${sub != null ? html`<div className="sub">${sub}</div>` : null}
    ${delta != null ? html`<div className=${cls + " small"}>${delta > 0 ? "+" : ""}${fmtNum(delta, 1)}</div>` : null}
  </div>`;
}

/** Horizontal meter: segments [{value, color, label}] on a track of `max`. */
export function Meter({ segments, max, format = (v) => fmtNum(v, 0) }) {
  const total = Math.max(max || 0, segments.reduce((s, x) => s + (x.value || 0), 0)) || 1;
  return html`<div>
    <div className="meter">${segments.map((s, i) => html`<div key=${i} title=${s.label} style=${{ width: `${100 * (s.value || 0) / total}%`, background: s.color }}></div>`)}</div>
    <div className="legend">${segments.map((s, i) => html`<span key=${i}><i className="swatch" style=${{ background: s.color }}></i>${s.label} <b className="mono">${format(s.value)}</b></span>`)}
      ${max ? html`<span className="muted">trần ${format(max)}</span>` : null}</div>
  </div>`;
}

/** Simple table: columns [{key, label, fmt, num}], rows (objects). */
export function Table({ columns, rows, onRow = null, selectedKey = null, rowKey = null, maxHeight = null }) {
  const body = html`<table className="tbl"><thead><tr>${columns.map((c) => html`<th key=${c.key} className=${c.num ? "num" : ""}>${c.label}</th>`)}</tr></thead>
    <tbody>${rows.map((r, i) => {
      const k = rowKey ? rowKey(r) : i;
      return html`<tr key=${k} className=${(onRow ? "click " : "") + (selectedKey != null && selectedKey === k ? "sel" : "")} onClick=${onRow ? () => onRow(r) : null}>
        ${columns.map((c) => html`<td key=${c.key} className=${c.num ? "num" : ""}>${c.fmt ? c.fmt(r[c.key], r) : r[c.key]}</td>`)}</tr>`;
    })}</tbody></table>`;
  return html`<div className=${"scroll-x" + (maxHeight ? " scroll-y" : "")} style=${maxHeight ? { maxHeight } : null}>${body}</div>`;
}
