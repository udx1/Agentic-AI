/* The three detailed tab screens, wireframed.
   Each is shell-agnostic content; the shell wraps them. */

/* ============ TAB 1 — IMPORT PURCHASES ============ */
function ScreenImport({ anno }) {
  const cols = ["Date", "Store", "Item", "Category", "Qty", "Price"];
  const colFlex = [1.1, 1.2, 1.8, 1.3, 0.6, 0.7];
  return (
    <div className="wf-screen">
      <div className="wf-screen__hd">
        <div>
          <Bar w={210} h={20} dark />
          <Bar w={300} h={11} mt={9} />
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <Btn icon="search" ghost>Filter</Btn>
          <Btn icon="upload" primary>Upload CSV</Btn>
        </div>
      </div>

      <NoteRow anno={anno} notes={["Big drag-&-drop zone · parses CSV in-browser, no backend", "History table cols: date · store · item · category · qty · price"]} />

      {/* dropzone */}
      <Block dashed h={170} r={12} center style={{ marginBottom: 6 }}>
        <span className="wf-drop__icon"><Icon type="upload" size={30} /></span>
        <Bar w={230} h={13} mt={6} dark />
        <Bar w={150} h={10} mt={4} />
        <Btn sm style={{ marginTop: 12 }}>Choose file</Btn>
      </Block>

      {/* status chips */}
      <div style={{ display: "flex", gap: 10, marginTop: 4, marginBottom: 18, flexWrap: "wrap" }}>
        <span className="wf-chip wf-chip--ok"><Icon type="check" size={13} /> Sample data loaded · 142 rows</span>
        <span className="wf-chip">Columns mapped: 6 / 6</span>
        <span className="wf-chip">Jan – Jun 2026</span>
      </div>

      {/* history table */}
      <Panel title="Purchase history" icon="list"
        action={<Cap>142 rows · newest first</Cap>}>
          {/* head */}
          <div className="wf-trow wf-trow--head">
            {cols.map((c, i) => (
              <div key={c} style={{ flex: colFlex[i], textAlign: i >= 4 ? "right" : "left" }}>
                <span className="wf-th">{c}</span>
              </div>
            ))}
          </div>
          {/* rows */}
          {Array.from({ length: 7 }).map((_, r) => (
            <div className="wf-trow" key={r}>
              {colFlex.map((f, i) => (
                <div key={i} style={{ flex: f, display: "flex", justifyContent: i >= 4 ? "flex-end" : "flex-start" }}>
                  <Bar w={i >= 4 ? 34 : `${58 + ((r + i) % 4) * 9}%`} h={9} dark={i === 5} />
                </div>
              ))}
            </div>
          ))}
      </Panel>
    </div>
  );
}

/* ============ TAB 2 — DASHBOARD ============ */
function ScreenDashboard({ anno }) {
  const kpis = [
    { label: "Total spend", big: true },
    { label: "Trips" },
    { label: "Avg basket" },
    { label: "Items tracked" },
  ];
  return (
    <div className="wf-screen">
      <div className="wf-screen__hd">
        <div>
          <Bar w={170} h={20} dark />
          <Bar w={250} h={11} mt={9} />
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <span className="wf-chip">This month ▾</span>
          <Btn icon="bars" ghost>Export</Btn>
        </div>
      </div>

      <NoteRow anno={anno} notes={["HERO: spend split across categories (donut)", "Repurchase frequency = how often each item is bought"]} />

      {/* KPI row */}
      <div className="wf-kpis">
        {kpis.map((k, i) => (
          <div className="wf-kpi" key={i}>
            <Cap>{k.label}</Cap>
            <Bar w={k.big ? 96 : 64} h={k.big ? 22 : 18} mt={8} dark />
            <Bar w={48} h={8} mt={8} />
          </div>
        ))}
      </div>

      {/* charts grid */}
      <div className="wf-dash-grid">
        <Panel title="Spend by category" icon="donut" style={{ height: "100%" }}
          action={<Cap>donut</Cap>}>
          <div className="wf-donut-row">
            <WDonut />
            <WLegend rows={6} />
          </div>
        </Panel>

        <Panel title="Repurchase frequency" icon="bars" style={{ height: "100%" }}
          action={<Cap>how often each item is bought</Cap>}>
          <WBars rows={6} />
        </Panel>
      </div>

      {/* trend strip */}
      <Panel title="Spend over time" icon="bars" bodyStyle={{ paddingTop: 18 }}
        action={<Cap>weekly</Cap>}>
        <div className="wf-trend">
          {[40, 62, 50, 78, 58, 84, 70, 92, 66, 80, 74, 96].map((h, i) => (
            <div key={i} className="wf-ph" style={{ width: "100%", height: h + "%", borderRadius: "4px 4px 0 0", background: i === 11 ? "var(--accent)" : undefined }} />
          ))}
        </div>
      </Panel>
    </div>
  );
}

/* ============ TAB 3 — PREDICT NEXT WEEK ============ */
function ScreenPredict({ anno }) {
  const groups = [
    { cat: "Produce", items: [["due now", true], ["every 7 days", true], ["every 10 days", false]] },
    { cat: "Dairy & eggs", items: [["due now", true], ["every 5 days", true]] },
    { cat: "Pantry", items: [["every 2 weeks", false], ["running low", true]] },
    { cat: "Household", items: [["every 3 weeks", false]] },
  ];
  return (
    <div className="wf-screen">
      <div className="wf-screen__hd">
        <div>
          <Bar w={240} h={20} dark />
          <Bar w={290} h={11} mt={9} />
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <span className="wf-chip">Week of Jun 8 ▾</span>
          <Btn icon="check" primary>Add all to list</Btn>
        </div>
      </div>

      <NoteRow anno={anno} notes={["Checklist shopping list · tick = add to cart", "Items & frequency predicted from purchase history"]} />

      <div className="wf-predict-grid">
        {/* checklist */}
        <Panel title="Predicted shopping list" icon="list"
          action={<Cap>9 items · est. total</Cap>}>
          {groups.map((g, gi) => (
            <div key={gi} className="wf-cat-group">
              <div className="wf-cat-hd">
                <span className="wf-cat-name">{g.cat}</span>
                <span className="wf-cat-line" />
              </div>
              {g.items.map(([freq, checked], ii) => (
                <div className="wf-check-row" key={ii}>
                  <span className={"wf-check" + (checked ? " wf-check--on" : "")}>
                    {checked && <Icon type="check" size={12} color="#fff" />}
                  </span>
                  <div style={{ flex: 1 }}>
                    <Bar w={`${52 + ((gi + ii) % 4) * 10}%`} h={11} dark />
                  </div>
                  <span className={"wf-freq" + (freq === "due now" || freq === "running low" ? " wf-freq--due" : "")}>{freq}</span>
                  <div className="wf-stepper"><span>−</span><span className="wf-stepper__n" /><span>+</span></div>
                  <Bar w={32} h={10} dark style={{ flexShrink: 0 }} />
                </div>
              ))}
            </div>
          ))}
        </Panel>

        {/* side: prediction logic */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <Panel title="How we predicted" icon="leaf">
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {["Avg days between buys", "Last purchased", "Typical quantity"].map((t, i) => (
                <div key={i}>
                  <Cap>{t}</Cap>
                  <Bar w={`${70 - i * 8}%`} h={10} mt={6} />
                </div>
              ))}
            </div>
          </Panel>
          <Panel title="Estimated total" icon="donut">
            <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
              <Bar w={110} h={26} dark />
              <Cap>vs last week</Cap>
            </div>
            <Bar w="80%" h={9} mt={14} />
          </Panel>
          <Btn primary icon="check" style={{ justifyContent: "center" }}>Export list</Btn>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { ScreenImport, ScreenDashboard, ScreenPredict });
