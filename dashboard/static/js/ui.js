// Local SVG icons, without an icon font or network dependency.
import { html } from "./lib.js";
const PATHS = {
  overview: ["M3 3h7v7H3z", "M14 3h7v7h-7z", "M3 14h7v7H3z", "M14 14h7v7h-7z"],
  sweep: ["M3 18l5-6 4 3 8-11", "M15 4h5v5", "M3 21h18"],
  run: ["M8 4l13 8-13 8z"],
  map: ["M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3z", "M9 3v15", "M15 6v15"],
  cells: ["M12 2l9 5v10l-9 5-9-5V7z", "M3 7l9 5 9-5", "M12 12v10"],
  distribution: ["M3 7V4h18v3a3 3 0 000 6v7H3v-7a3 3 0 000-6z", "M14 4v3m0 3v3m0 3v4"],
  results: ["M5 3h10l4 4v14H5z", "M14 3v5h5", "M8 12h8", "M8 16h5"],
  arrow: ["M5 12h14", "M14 7l5 5-5 5"],
  check: ["M5 12l4 4L19 6"],
  clock: ["M12 8v5l3 2", "M12 3a9 9 0 100 18 9 9 0 000-18"],
  search: ["M10 3a7 7 0 100 14 7 7 0 000-14", "M15 15l6 6"],
  refresh: ["M20 7a9 9 0 10.5 9", "M20 3v5h-5"],
  collapse: ["M15 18l-6-6 6-6"],
  expand: ["M9 18l6-6-6-6"],
  info: ["M12 3a9 9 0 100 18 9 9 0 000-18", "M12 11v6", "M12 7v1"],
};
export function Icon({ name, size = 18 }) {
  return html`<svg className="ui-icon" width=${size} height=${size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">${(PATHS[name] || PATHS.info).map((d, i) => html`<path key=${i} d=${d} />`)}</svg>`;
}
// Original artwork from Xanh SM's recruitment site; provenance in static/brand/README.md.
export function BrandMark() {
  return html`<span className="brand-artwork"><img className="brand-logo-full" src="/static/brand/xanh-sm-white.png" alt="" width="1328" height="348" /><img className="brand-logo-compact" src="/static/brand/favicon.png" alt="" width="192" height="192" /></span>`;
}

export function SectionHead({ eyebrow, title, description, children }) {
  return html`<div className="section-head"><div>${eyebrow ? html`<div className="eyebrow">${eyebrow}</div>` : null}<h2>${title}</h2>${description ? html`<p>${description}</p>` : null}</div><div className="row">${children}</div></div>`;
}

