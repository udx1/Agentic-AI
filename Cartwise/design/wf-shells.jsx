/* App-shell exploration: 4 distinct nav directions.
   ShellMini = small comparison thumbnail. ShellWrap = full-size frame around a screen. */

const TABS = [
  { id: "import", label: "Import", icon: "upload" },
  { id: "dashboard", label: "Dashboard", icon: "donut" },
  { id: "predict", label: "Predict", icon: "list" },
];

/* tiny brand lockup */
function Brand({ size = "md" }) {
  const s = size === "sm";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: s ? 6 : 8 }}>
      <span className="wf-logo" style={{ width: s ? 18 : 24, height: s ? 18 : 24 }}>
        <Icon type="leaf" size={s ? 12 : 15} color="#fff" />
      </span>
      {!s && <Bar w={70} h={11} dark />}
    </div>
  );
}

/* ---------- MINIATURE comparison frames (schematic dashboard inside) ---------- */
function MiniBody() {
  return (
    <div className="wf-mini__body">
      <div className="wf-mini__kpis">
        {[0, 1, 2].map((i) => <div key={i} className="wf-ph wf-mini__kpi" />)}
      </div>
      <div className="wf-mini__charts">
        <div className="wf-mini__donut" />
        <div className="wf-mini__bars">
          {[80, 60, 45, 30].map((w, i) => <div key={i} className="wf-ph" style={{ width: w + "%", height: 7, borderRadius: 2, background: i === 0 ? "var(--accent)" : undefined }} />)}
        </div>
      </div>
    </div>
  );
}
function MiniTab({ active, icon }) {
  return <span className={"wf-mini__tab" + (active ? " is-active" : "")}><Icon type={icon} size={11} color={active ? "var(--accent)" : "#9a9a9a"} /></span>;
}

function ShellMini({ kind, title, note, recommended }) {
  return (
    <div className="wf-mini-card">
      <div className="wf-mini-card__hd">
        <Bar w={120} h={12} dark />
        {recommended && <span className="wf-tag">suggested</span>}
      </div>
      <div className={"wf-mini wf-mini--" + kind}>
        {kind === "top" && (
          <>
            <div className="wf-mini__topbar">
              <Brand size="sm" />
              <div className="wf-mini__tabs">{TABS.map((t, i) => <MiniTab key={t.id} icon={t.icon} active={i === 1} />)}</div>
            </div>
            <MiniBody />
          </>
        )}
        {kind === "side" && (
          <div style={{ display: "flex", height: "100%" }}>
            <div className="wf-mini__side">
              <Brand size="sm" />
              <div style={{ display: "flex", flexDirection: "column", gap: 7, marginTop: 10 }}>
                {TABS.map((t, i) => <MiniTab key={t.id} icon={t.icon} active={i === 1} />)}
              </div>
            </div>
            <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
              <div className="wf-mini__sidetop"><Bar w={60} h={8} /></div>
              <MiniBody />
            </div>
          </div>
        )}
        {kind === "bottom" && (
          <>
            <div className="wf-mini__topbar wf-mini__topbar--slim"><Bar w={70} h={9} dark /></div>
            <MiniBody />
            <div className="wf-mini__bottombar">{TABS.map((t, i) => <MiniTab key={t.id} icon={t.icon} active={i === 1} />)}</div>
          </>
        )}
        {kind === "pill" && (
          <>
            <div className="wf-mini__topbar wf-mini__topbar--slim"><Brand size="sm" /></div>
            <MiniBody />
            <div className="wf-mini__pill">{TABS.map((t, i) => <MiniTab key={t.id} icon={t.icon} active={i === 1} />)}</div>
          </>
        )}
      </div>
      <Cap style={{ marginTop: 12, lineHeight: 1.5 }}>{note}</Cap>
    </div>
  );
}

/* ---------- FULL-SIZE shell wrapper around a real screen ---------- */
function ShellWrap({ nav, active, onNav, children }) {
  const tabBtn = (t, vertical = false) => (
    <button
      key={t.id}
      className={"wf-tab" + (active === t.id ? " is-active" : "") + (vertical ? " wf-tab--v" : "")}
      onClick={() => onNav(t.id)}
    >
      <Icon type={t.icon} size={16} color={active === t.id ? "var(--accent)" : "#8a8a8a"} />
      <span>{t.label}</span>
    </button>
  );

  if (nav === "side") {
    return (
      <div className="wf-frame wf-frame--side">
        <aside className="wf-sidebar">
          <div style={{ padding: "4px 6px 18px" }}><Brand /></div>
          <nav style={{ display: "flex", flexDirection: "column", gap: 4 }}>{TABS.map((t) => tabBtn(t, true))}</nav>
          <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: 10 }}>
            <div className="wf-sb-card"><Cap>Tracking 142 purchases</Cap><Bar w="70%" h={8} mt={8} /></div>
            <div className="wf-avatar" />
          </div>
        </aside>
        <main className="wf-main">{children}</main>
      </div>
    );
  }

  if (nav === "bottom") {
    return (
      <div className="wf-frame wf-frame--bottom">
        <header className="wf-topbar wf-topbar--slim">
          <Brand />
          <div className="wf-avatar" />
        </header>
        <main className="wf-main wf-main--padbottom">{children}</main>
        <nav className="wf-bottombar">{TABS.map((t) => (
          <button key={t.id} className={"wf-btab" + (active === t.id ? " is-active" : "")} onClick={() => onNav(t.id)}>
            <Icon type={t.icon} size={20} color={active === t.id ? "var(--accent)" : "#9a9a9a"} />
            <span>{t.label}</span>
          </button>
        ))}</nav>
      </div>
    );
  }

  if (nav === "pill") {
    return (
      <div className="wf-frame wf-frame--pill">
        <header className="wf-topbar wf-topbar--slim"><Brand /><div className="wf-avatar" /></header>
        <main className="wf-main">{children}</main>
        <nav className="wf-pillnav">{TABS.map((t) => (
          <button key={t.id} className={"wf-ptab" + (active === t.id ? " is-active" : "")} onClick={() => onNav(t.id)}>
            <Icon type={t.icon} size={16} color={active === t.id ? "#fff" : "#8a8a8a"} />
            <span>{t.label}</span>
          </button>
        ))}</nav>
      </div>
    );
  }

  /* default: top tabs */
  return (
    <div className="wf-frame wf-frame--top">
      <header className="wf-topbar">
        <Brand />
        <nav className="wf-tabs">{TABS.map((t) => tabBtn(t))}</nav>
        <div className="wf-avatar" />
      </header>
      <main className="wf-main">{children}</main>
    </div>
  );
}

Object.assign(window, { ShellMini, ShellWrap, Brand, TABS });
