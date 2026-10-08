// Shared runtime: React + htm (no build step), fetch helpers, number/time formatting, palette.
export const React = window.React;
export const ReactDOM = window.ReactDOM;
export const html = window.htm.bind(React.createElement);
export const { useState, useEffect, useRef, useMemo, useCallback } = React;

export async function api(path, opts = {}) {
  const init = { headers: { "Content-Type": "application/json" }, ...opts };
  if (init.body && typeof init.body !== "string") init.body = JSON.stringify(init.body);
  const r = await fetch(path, init);
  const text = await r.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch (e) { data = { detail: text }; }
  if (!r.ok) throw new Error((data && (data.detail || data.error)) ? JSON.stringify(data.detail || data.error) : `HTTP ${r.status}`);
  return data;
}

/** GET `path` (null = disabled); `poll` in ms re-fetches; returns {data, error, loading, reload}. */
export function useApi(path, deps = [], { poll = 0 } = {}) {
  const [state, setState] = useState({ data: null, error: null, loading: !!path });
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!path) { setState({ path, data: null, error: null, loading: false }); return; }
    let alive = true;
    let timer = null;
    const go = async () => {
      try {
        const data = await api(path);
        if (alive) setState({ path, data, error: null, loading: false });
      } catch (e) {
        if (alive) setState((s) => ({ path, data: s.path === path ? s.data : null, error: String(e.message || e), loading: false }));
      }
      if (alive && poll > 0) timer = setTimeout(go, poll);
    };
    setState((s) => s.path === path ? { ...s, loading: s.data == null } : { path, data: null, error: null, loading: true });
    go();
    return () => { alive = false; if (timer) clearTimeout(timer); };
  }, [path, poll, n, ...deps]);
  const current = !path ? { data: null, error: null, loading: false } : state.path === path ? state : { data: null, error: null, loading: true };
  return { ...current, reload: () => setN((k) => k + 1) };
}

// --- formatting (vi-VN: dot thousands, comma decimals) ---
const nfInt = new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 0 });
export const fmtInt = (x) => (x == null || Number.isNaN(x) ? "–" : nfInt.format(Math.round(x)));
export const fmtNum = (x, d = 1) => (x == null || Number.isNaN(x) ? "–" : new Intl.NumberFormat("vi-VN", { minimumFractionDigits: d, maximumFractionDigits: d }).format(x));
export const fmtUSD = (x, d = 0) => (x == null || Number.isNaN(x) ? "–" : fmtNum(x, d) + " USD");
export const fmtPct = (x, d = 1) => (x == null || Number.isNaN(x) ? "–" : fmtNum(100 * x, d) + " %");
export const fmtSigned = (x, d = 1) => (x == null ? "–" : (x > 0 ? "+" : "") + fmtNum(x, d));
export function fmtClock(t_s) {
  if (t_s == null) return "–";
  const day = Math.floor(t_s / 86400);
  const s = t_s - day * 86400;
  const hh = String(Math.floor(s / 3600)).padStart(2, "0");
  const mm = String(Math.floor((s % 3600) / 60)).padStart(2, "0");
  return `Ngày ${day} · ${hh}:${mm}`;
}
export const fmtHM = (t_s) => {
  const s = ((t_s % 86400) + 86400) % 86400;
  return `${String(Math.floor(s / 3600)).padStart(2, "0")}:${String(Math.floor((s % 3600) / 60)).padStart(2, "0")}`;
};
export function fmtDur(s) {
  if (s == null) return "–";
  if (s < 60) return `${fmtNum(s, 1)} s`;
  const m = Math.floor(s / 60);
  return `${m} ph ${Math.round(s - 60 * m)} s`;
}
export const compact = (x) => {
  if (x == null || Number.isNaN(x)) return "–";
  const a = Math.abs(x);
  if (a >= 1e6) return fmtNum(x / 1e6, 2) + "M";
  if (a >= 1e4) return fmtNum(x / 1e3, 1) + "K";
  return Number.isInteger(x) ? fmtInt(x) : fmtNum(x, a < 10 ? 2 : 1);
};

// --- palette (reference instance of the dataviz skill; dark steps via CSS variables) ---
export const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
export const SERIES = () => ["--s1", "--s2", "--s3", "--s4", "--s5", "--s6", "--s7", "--s8"].map(cssVar);
export const SEQ = () => ["--seq-100", "--seq-200", "--seq-300", "--seq-400", "--seq-500", "--seq-600", "--seq-700"].map(cssVar);
export const DRIVER_STATUS = ["offline", "idle", "en_route", "on_trip", "repositioning"];
export const DRIVER_LABEL = { offline: "offline", idle: "rảnh", en_route: "đang đi đón", on_trip: "chở khách", repositioning: "dịch chuyển" };
export const driverColors = () => ({ idle: cssVar("--s3"), en_route: cssVar("--s2"), on_trip: cssVar("--s1"), repositioning: cssVar("--muted") });
export const ORDER_STATUS = ["Waiting", "Matched", "OnTrip", "Completed", "Abandoned", "Cancelled", "Truncated"];
export const EVENT_TYPES = ["request", "match", "pickup", "complete", "abandon", "cancel", "offer", "blocked"];
export const EVENT_LABEL = { request: "đặt xe", match: "ghép xe", pickup: "đón", complete: "hoàn thành", abandon: "bỏ (hết kiên nhẫn)", cancel: "hủy khi xe đang đến", offer: "phát voucher", blocked: "hết ngân sách" };

/** Sequential blue ramp for a value in [0, vmax] (NaN -> surface). */
export function seqColor(v, vmax, seq) {
  if (v == null || Number.isNaN(v)) return cssVar("--surface-2");
  const t = Math.max(0, Math.min(1, v / vmax));
  return seq[Math.min(seq.length - 1, Math.floor(t * seq.length))];
}

export const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
export const sum = (a) => a.reduce((s, x) => s + (x || 0), 0);
export const mean = (a) => (a.length ? sum(a) / a.length : NaN);

export function useLocalStorage(key, initial) {
  const [v, setV] = useState(() => {
    try { const s = localStorage.getItem(key); return s != null ? JSON.parse(s) : initial; } catch (e) { return initial; }
  });
  const set = (x) => { setV(x); try { localStorage.setItem(key, JSON.stringify(x)); } catch (e) { /* ignore */ } };
  return [v, set];
}

/** Resize-aware width of a container (for responsive SVG charts). */
export function useWidth(ref, fallback = 600) {
  const [w, setW] = useState(fallback);
  const observed = useRef(null);
  const observer = useRef(null);
  // A loading/empty state can render before the measured node exists. Check
  // after every commit, but keep the observer until the actual node changes.
  useEffect(() => {
    if (observed.current === ref.current) return;
    observer.current?.disconnect();
    observed.current = ref.current;
    if (!ref.current) return;
    observer.current = new ResizeObserver(([entry]) => {
      if (entry.contentRect.width > 0) setW(entry.contentRect.width);
    });
    observer.current.observe(ref.current);
  });
  useEffect(() => () => {
    observer.current?.disconnect();
    observed.current = null;
  }, []);
  return w;
}
