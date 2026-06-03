/* App shell (top tab bar) + state + tweaks. */

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "startTab": "dashboard",
  "defaultPeriod": "90",
  "predictWindow": 7,
  "topItems": 8
}/*EDITMODE-END*/;

const NAV = [
  { id: "import", label: "Import", icon: "upload" },
  { id: "dashboard", label: "Dashboard", icon: "donut" },
  { id: "predict", label: "Predict", icon: "cart" },
];

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [rows, setRows] = React.useState(() => GT.generateSample());
  const [source, setSource] = React.useState("sample");
  const [tab, setTab] = React.useState(t.startTab);
  const [period, setPeriod] = React.useState(t.defaultPeriod === "all" ? "all" : Number(t.defaultPeriod));

  // honor startTab / defaultPeriod ONLY when the user actually changes the tweak
  // (not on mount or when useTweaks settles its stored value — that would yank
  //  the user off whatever tab they navigated to)
  const prevStart = React.useRef(t.startTab);
  const prevPeriod = React.useRef(t.defaultPeriod);
  React.useEffect(() => {
    if (t.startTab !== prevStart.current) { prevStart.current = t.startTab; setTab(t.startTab); }
  }, [t.startTab]);
  React.useEffect(() => {
    if (t.defaultPeriod !== prevPeriod.current) {
      prevPeriod.current = t.defaultPeriod;
      setPeriod(t.defaultPeriod === "all" ? "all" : Number(t.defaultPeriod));
    }
  }, [t.defaultPeriod]);

  const onData = (parsed, name) => { setRows(parsed); setSource(name || "import"); setTab("dashboard"); };
  const onReset = () => { setRows(GT.generateSample()); setSource("sample"); };

  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-900">
      {/* top bar */}
      <header className="sticky top-0 z-20 border-b border-neutral-200/80 bg-white">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-4 px-5">
          <div className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-green-600 text-white shadow-sm"><GIcon type="leaf" size={20} /></span>
            <div className="leading-tight">
              <div className="text-[15px] font-bold tracking-tight">Cartwise</div>
              <div className="text-[11px] text-neutral-400">grocery tracker</div>
            </div>
          </div>

          <nav className="ml-2 flex items-center gap-1 sm:ml-6">
            {NAV.map((n) => {
              const on = tab === n.id;
              return (
                <button key={n.id} onClick={() => setTab(n.id)}
                  className="flex items-center gap-2 rounded-xl px-3.5 py-2 text-sm font-semibold transition sm:px-4 hover:bg-neutral-100"
                  style={on
                    ? { background: "#f0fdf4", color: "#15803d" }
                    : { color: "#6b7280" }}>
                  <GIcon type={n.icon} size={17} />
                  <span className="hidden sm:inline">{n.label}</span>
                </button>
              );
            })}
          </nav>

          <div className="ml-auto hidden items-center gap-2 text-xs text-neutral-400 md:flex">
            <span className={"h-2 w-2 rounded-full " + (source === "sample" ? "bg-amber-400" : "bg-green-500")} />
            {source === "sample" ? "Sample data" : "Your data"}
          </div>
        </div>
      </header>

      <main className="px-5 py-8">
        {tab === "import" && <ScreenImport rows={rows} source={source} onData={onData} onReset={onReset} />}
        {tab === "dashboard" && <ScreenDashboard rows={rows} period={period} onPeriod={setPeriod} topN={t.topItems} />}
        {tab === "predict" && <ScreenPredict rows={rows} horizon={t.predictWindow} goImport={() => setTab("import")} />}
      </main>

      <TweaksPanel>
        <TweakSection label="Defaults" />
        <TweakRadio label="Start on" value={t.startTab}
          options={["import", "dashboard", "predict"]}
          onChange={(v) => setTweak("startTab", v)} />
        <TweakRadio label="Dashboard period" value={t.defaultPeriod}
          options={["30", "90", "all"]}
          onChange={(v) => setTweak("defaultPeriod", v)} />
        <TweakSection label="Charts & prediction" />
        <TweakSlider label="Predict window" value={t.predictWindow} min={5} max={21} step={1} unit=" days"
          onChange={(v) => setTweak("predictWindow", v)} />
        <TweakSlider label="Top items in chart" value={t.topItems} min={5} max={12} step={1}
          onChange={(v) => setTweak("topItems", v)} />
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
