/* Shared hi-fi UI atoms: Icon set + Card. Exported to window. */

function GIcon({ type, size = 18, className = "", stroke = 1.8 }) {
  const p = {
    width: size, height: size, viewBox: "0 0 24 24", fill: "none",
    stroke: "currentColor", strokeWidth: stroke, strokeLinecap: "round",
    strokeLinejoin: "round", className,
  };
  switch (type) {
    case "upload": return <svg {...p}><path d="M12 15V4m0 0L8 8m4-4l4 4" /><path d="M5 15v3a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-3" /></svg>;
    case "download": return <svg {...p}><path d="M12 4v11m0 0l-4-4m4 4l4-4" /><path d="M5 18v1a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1" /></svg>;
    case "donut": return <svg {...p}><circle cx="12" cy="12" r="8.5" /><circle cx="12" cy="12" r="3.2" /></svg>;
    case "bars": return <svg {...p}><path d="M4 20V11M10 20V5M16 20V14M22 20H2" /></svg>;
    case "list": return <svg {...p}><path d="M9 6h11M9 12h11M9 18h11" /><circle cx="4.5" cy="6" r="1" fill="currentColor" stroke="none" /><circle cx="4.5" cy="12" r="1" fill="currentColor" stroke="none" /><circle cx="4.5" cy="18" r="1" fill="currentColor" stroke="none" /></svg>;
    case "check": return <svg {...p}><path d="M5 12.5l4.5 4.5L19 6.5" /></svg>;
    case "search": return <svg {...p}><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.2-4.2" /></svg>;
    case "leaf": return <svg {...p}><path d="M4 19c11 1.5 16-5 16-15C8 4 3 9 4 19z" /><path d="M4 19C8 13 11 10 17 8" /></svg>;
    case "cart": return <svg {...p}><circle cx="9" cy="20" r="1.4" /><circle cx="18" cy="20" r="1.4" /><path d="M2 3h2.2l2.3 12.2a1.5 1.5 0 0 0 1.5 1.2h8.8a1.5 1.5 0 0 0 1.5-1.2L21 7H5.5" /></svg>;
    case "trash": return <svg {...p}><path d="M4 7h16M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2m2 0v12a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V7" /></svg>;
    case "calendar": return <svg {...p}><rect x="3.5" y="4.5" width="17" height="16" rx="2.5" /><path d="M3.5 9h17M8 3v3M16 3v3" /></svg>;
    case "trend": return <svg {...p}><path d="M3 17l5-5 4 3 8-9" /><path d="M17 6h4v4" /></svg>;
    case "clock": return <svg {...p}><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></svg>;
    case "chevron": return <svg {...p}><path d="M6 9l6 6 6-6" /></svg>;
    case "sort": return <svg {...p}><path d="M8 4v16M8 20l-3-3M8 4l3 3M16 20V4M16 4l3 3M16 20l-3-3" /></svg>;
    case "store": return <svg {...p}><path d="M4 9.5V20a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1V9.5" /><path d="M3 4h18l1 5a3 3 0 0 1-6 0 3 3 0 0 1-6 0 3 3 0 0 1-6 0z" /></svg>;
    case "x": return <svg {...p}><path d="M6 6l12 12M18 6L6 18" /></svg>;
    case "sparkle": return <svg {...p}><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" /></svg>;
    default: return <svg {...p}><rect x="4" y="4" width="16" height="16" rx="3" /></svg>;
  }
}

function Card({ children, className = "", ...rest }) {
  return (
    <div className={"rounded-2xl border border-neutral-200/80 bg-white " + className} {...rest}>
      {children}
    </div>
  );
}

function CardHead({ icon, title, sub, action }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-neutral-100 px-5 py-4">
      <div className="flex items-center gap-2.5 min-w-0">
        {icon && <span className="text-green-600"><GIcon type={icon} size={18} /></span>}
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-neutral-800 leading-tight">{title}</h3>
          {sub && <p className="text-xs text-neutral-400 mt-0.5 truncate">{sub}</p>}
        </div>
      </div>
      {action}
    </div>
  );
}

Object.assign(window, { GIcon, Card, CardHead });
