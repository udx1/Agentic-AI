/* Main wireframe app: shell comparison section + live detailed frame + tweaks. */

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "navStyle": "top",
  "accent": "#16a34a",
  "density": "comfortable",
  "fill": "solid",
  "annotations": true
}/*EDITMODE-END*/;

const SHELL_OPTIONS = [
  { kind: "top", label: "Top tab bar", recommended: true,
    note: "Familiar web pattern. All 3 tabs visible up top, content gets full width. Scales cleanly to desktop." },
  { kind: "side", label: "Left sidebar",
    note: "Roomy for desktop dashboards. Nav + account live on the left; easy to add filters or saved views later." },
  { kind: "bottom", label: "Bottom tab bar",
    note: "Native mobile-app feel. Thumb-reachable nav — best if this is primarily a phone experience." },
  { kind: "pill", label: "Floating pill",
    note: "Minimal, modern. A floating segmented control keeps chrome light and focus on the data." },
];

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [screen, setScreen] = React.useState("dashboard");

  // apply tweaks to root via CSS vars / data attrs
  React.useEffect(() => {
    const r = document.documentElement;
    r.style.setProperty("--accent", t.accent);
    r.dataset.density = t.density;
    r.dataset.fill = t.fill;
  }, [t.accent, t.density, t.fill]);

  const anno = t.annotations;
  const ScreenComp = screen === "import" ? ScreenImport : screen === "predict" ? ScreenPredict : ScreenDashboard;

  return (
    <div className="wf-doc">
      {/* ===== document header ===== */}
      <header className="wf-doc__hd">
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span className="wf-logo wf-logo--lg"><Icon type="leaf" size={20} color="#fff" /></span>
          <div>
            <h1>Grocery Tracker — Wireframes</h1>
            <p>Low-fi structure & flow · 3 tabs · {SHELL_OPTIONS.length} app-shell directions</p>
          </div>
        </div>
        <span className="wf-stamp">WIREFRAME · not final visuals</span>
      </header>

      {/* ===== SECTION 1: shell comparison ===== */}
      <section className="wf-section">
        <div className="wf-section__hd">
          <span className="wf-section__num">01</span>
          <div>
            <h2>App shell — choose a navigation direction</h2>
            <p>Same Dashboard content, four ways to navigate the 3 tabs. Pick one to preview full-size below.</p>
          </div>
        </div>
        <div className="wf-mini-row">
          {SHELL_OPTIONS.map((o) => (
            <button
              key={o.kind}
              className={"wf-mini-pick" + (t.navStyle === o.kind ? " is-active" : "")}
              onClick={() => setTweak("navStyle", o.kind)}
            >
              <ShellMini kind={o.kind} title={o.label} note={o.note} recommended={o.recommended} />
            </button>
          ))}
        </div>
      </section>

      {/* ===== SECTION 2: live full-size frame ===== */}
      <section className="wf-section">
        <div className="wf-section__hd">
          <span className="wf-section__num">02</span>
          <div>
            <h2>Screens — full-size walkthrough</h2>
            <p>Now showing the <b>{SHELL_OPTIONS.find((s) => s.kind === t.navStyle)?.label}</b> shell. Switch tabs to see each screen.</p>
          </div>
          <div className="wf-seg" role="tablist">
            {TABS.map((tab) => (
              <button key={tab.id} className={"wf-seg__btn" + (screen === tab.id ? " is-active" : "")} onClick={() => setScreen(tab.id)}>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="wf-stage">
          <ShellWrap nav={t.navStyle} active={screen} onNav={setScreen}>
            <ScreenComp anno={anno} />
          </ShellWrap>
        </div>
      </section>

      <footer className="wf-doc__ft">
        <span>Next step after wireframes: build the working React + Recharts + Tailwind prototype with real CSV parsing.</span>
      </footer>

      {/* ===== Tweaks ===== */}
      <TweaksPanel>
        <TweakSection label="Navigation" />
        <TweakRadio label="Shell" value={t.navStyle}
          options={["top", "side", "bottom", "pill"]}
          onChange={(v) => setTweak("navStyle", v)} />
        <TweakSection label="Wireframe style" />
        <TweakColor label="Accent" value={t.accent}
          options={["#16a34a", "#4d7c0f", "#0d9488", "#65a30d"]}
          onChange={(v) => setTweak("accent", v)} />
        <TweakRadio label="Density" value={t.density}
          options={["comfortable", "compact"]}
          onChange={(v) => setTweak("density", v)} />
        <TweakRadio label="Fill" value={t.fill}
          options={["solid", "hatched"]}
          onChange={(v) => setTweak("fill", v)} />
        <TweakToggle label="Annotations" value={t.annotations}
          onChange={(v) => setTweak("annotations", v)} />
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
