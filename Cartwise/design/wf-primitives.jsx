/* Wireframe primitives — low-fi grayscale building blocks.
   All exported to window at the bottom for cross-script use. */
const { useState } = React;

/* ---- text placeholder bar (a "line of text") ---- */
function Bar({ w = "100%", h = 10, mt = 0, dark = false, style = {} }) {
  return (
    <div
      className={"wf-ph" + (dark ? " wf-ph--dark" : "")}
      style={{ width: w, height: h, borderRadius: 3, marginTop: mt, ...style }}
    />
  );
}

/* ---- generic filled block ---- */
function Block({ w = "100%", h = 40, r = 6, dashed = false, children, style = {}, center = false }) {
  return (
    <div
      className={dashed ? "wf-dash" : "wf-ph"}
      style={{
        width: w, height: h, borderRadius: r,
        display: center ? "flex" : "block",
        alignItems: "center", justifyContent: "center",
        flexDirection: "column", gap: 6, ...style,
      }}
    >
      {children}
    </div>
  );
}

/* ---- small caption / field label (real text, muted) ---- */
function Cap({ children, style = {} }) {
  return <div className="wf-cap" style={style}>{children}</div>;
}

/* ---- annotation callout (monospace note about the design) ---- */
function Note({ children, side = "left", style = {} }) {
  return (
    <div className={"wf-note wf-note--" + side} data-anno style={style}>
      <span className="wf-note__dot" />
      <span>{children}</span>
    </div>
  );
}

/* ---- inline row of annotation notes (sits in normal flow, never clipped) ---- */
function NoteRow({ anno, notes = [] }) {
  if (!anno) return null;
  return (
    <div className="wf-noterow" data-anno>
      {notes.map((n, i) => <Note key={i}>{n}</Note>)}
    </div>
  );
}

/* ---- simple geometric icons (no complex SVG) ---- */
function Icon({ type = "square", size = 16, color = "currentColor", stroke = 1.6 }) {
  const c = { width: size, height: size, stroke: color, fill: "none", strokeWidth: stroke, strokeLinecap: "round", strokeLinejoin: "round" };
  switch (type) {
    case "upload":
      return (<svg viewBox="0 0 24 24" style={c}><path d="M12 16V4M12 4l-5 5M12 4l5 5" /><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3" /></svg>);
    case "check":
      return (<svg viewBox="0 0 24 24" style={c}><path d="M5 12.5l4.5 4.5L19 6.5" /></svg>);
    case "donut":
      return (<svg viewBox="0 0 24 24" style={c}><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="3" /></svg>);
    case "bars":
      return (<svg viewBox="0 0 24 24" style={c}><path d="M4 20V10M10 20V5M16 20V13M22 20H2" /></svg>);
    case "list":
      return (<svg viewBox="0 0 24 24" style={c}><path d="M8 7h12M8 12h12M8 17h12M4 7h.01M4 12h.01M4 17h.01" /></svg>);
    case "circle":
      return (<svg viewBox="0 0 24 24" style={c}><circle cx="12" cy="12" r="8" /></svg>);
    case "diamond":
      return (<svg viewBox="0 0 24 24" style={c}><path d="M12 3l9 9-9 9-9-9z" /></svg>);
    case "leaf":
      return (<svg viewBox="0 0 24 24" style={c}><path d="M5 19c10 1 14-5 14-14C8 4 4 9 5 19z" /><path d="M5 19C8 14 11 11 16 9" /></svg>);
    case "search":
      return (<svg viewBox="0 0 24 24" style={c}><circle cx="11" cy="11" r="6" /><path d="M20 20l-4-4" /></svg>);
    default:
      return (<svg viewBox="0 0 24 24" style={c}><rect x="4" y="4" width="16" height="16" rx="3" /></svg>);
  }
}

/* ---- wireframe DONUT chart (grayscale slices, one accent) ---- */
function WDonut({ size = 190, thickness = 34 }) {
  // grayscale segments + one accent segment
  const segs = [
    { v: 32, c: "var(--accent)" },
    { v: 22, c: "#cfcfcf" },
    { v: 16, c: "#dcdcdc" },
    { v: 14, c: "#bdbdbd" },
    { v: 9,  c: "#e4e4e4" },
    { v: 7,  c: "#d0d0d0" },
  ];
  let acc = 0;
  const stops = segs.map((s) => {
    const start = acc; acc += s.v;
    return `${s.c} ${start}% ${acc}%`;
  }).join(", ");
  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <div style={{
        width: size, height: size, borderRadius: "50%",
        background: `conic-gradient(${stops})`,
      }} />
      <div style={{
        position: "absolute", inset: thickness, borderRadius: "50%",
        background: "var(--paper)", display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center", gap: 4,
      }}>
        <Bar w={42} h={8} />
        <Bar w={60} h={14} dark />
      </div>
    </div>
  );
}

/* ---- wireframe legend rows ---- */
function WLegend({ rows = 6 }) {
  const accentIdx = 0;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 11, minWidth: 150 }}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 9 }}>
          <span style={{
            width: 11, height: 11, borderRadius: 3, flexShrink: 0,
            background: i === accentIdx ? "var(--accent)" : ["#cfcfcf", "#dcdcdc", "#bdbdbd", "#e4e4e4", "#d0d0d0"][(i - 1) % 5],
          }} />
          <Bar w={70 - i * 6} h={9} />
          <Bar w={26} h={9} style={{ marginLeft: "auto" }} dark />
        </div>
      ))}
    </div>
  );
}

/* ---- wireframe BAR chart (horizontal, repurchase frequency) ---- */
function WBars({ rows = 6, labelW = 90 }) {
  const widths = [92, 74, 63, 50, 38, 27, 20];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 13, width: "100%" }}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Bar w={labelW - i * 3} h={9} style={{ flexShrink: 0 }} />
          <div style={{ flex: 1, height: 16, position: "relative" }}>
            <div className="wf-ph" style={{
              width: widths[i] + "%", height: "100%", borderRadius: 3,
              background: i === 0 ? "var(--accent)" : undefined,
            }} />
          </div>
          <Bar w={22} h={9} dark style={{ flexShrink: 0 }} />
        </div>
      ))}
    </div>
  );
}

/* ---- panel / card wrapper with a header label ---- */
function Panel({ title, icon, children, style = {}, bodyStyle = {}, action }) {
  return (
    <section className="wf-panel" style={style}>
      {(title || action) && (
        <header className="wf-panel__hd">
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {icon && <span className="wf-panel__icon"><Icon type={icon} size={15} /></span>}
            <span className="wf-panel__title">{title}</span>
          </div>
          {action}
        </header>
      )}
      <div className="wf-panel__bd" style={bodyStyle}>{children}</div>
    </section>
  );
}

/* ---- pill button placeholder ---- */
function Btn({ children, primary = false, ghost = false, icon, sm = false, style = {} }) {
  return (
    <span
      className={"wf-btn" + (primary ? " wf-btn--primary" : "") + (ghost ? " wf-btn--ghost" : "") + (sm ? " wf-btn--sm" : "")}
      style={style}
    >
      {icon && <Icon type={icon} size={sm ? 13 : 15} color="currentColor" />}
      {children}
    </span>
  );
}

Object.assign(window, { Bar, Block, Cap, Note, NoteRow, Icon, WDonut, WLegend, WBars, Panel, Btn });
