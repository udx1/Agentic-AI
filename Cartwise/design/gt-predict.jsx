/* TAB 3 — Predict Next Week: checklist generated from the frequency model. */

function ScreenPredict({ rows, goImport, horizon = 7 }) {
  const pred = React.useMemo(() => GT.predictNextWeek(rows, horizon), [rows, horizon]);

  // checked state: default-check items due within 2 days
  const [checked, setChecked] = React.useState(() => {
    const s = {};
    pred.items.forEach((i) => { s[i.item] = i.dueIn <= 2; });
    return s;
  });
  const [qty, setQty] = React.useState(() => {
    const s = {}; pred.items.forEach((i) => { s[i.item] = i.qty; }); return s;
  });

  // resync when data changes
  React.useEffect(() => {
    const s = {}, q = {};
    pred.items.forEach((i) => { s[i.item] = i.dueIn <= 2; q[i.item] = i.qty; });
    setChecked(s); setQty(q);
  }, [rows, horizon]);

  const toggle = (item) => setChecked((c) => ({ ...c, [item]: !c[item] }));
  const bump = (item, d) => setQty((q) => ({ ...q, [item]: Math.max(1, (q[item] || 1) + d) }));
  const allOn = pred.items.length && pred.items.every((i) => checked[i.item]);
  const setAll = (on) => {
    const s = {}; pred.items.forEach((i) => { s[i.item] = on; }); setChecked(s);
  };

  const selected = pred.items.filter((i) => checked[i.item]);
  const selTotal = selected.reduce((s, i) => s + (i.estPrice / i.qty) * (qty[i.item] || i.qty), 0);

  const freqLabel = (n) => (n <= 7 ? `every ${n} days` : n <= 13 ? `every ${n} days` : `every ${Math.round(n / 7)} wks`);
  const statusOf = (i) =>
    i.dueIn <= 0 ? { t: "due now", due: true } : i.dueIn === 1 ? { t: "due tomorrow", due: true } : { t: `in ${i.dueIn} days`, due: false };

  const exportList = () => {
    const lines = ["Shopping list — week of " + new Date(GT.maxDate(rows)).toLocaleDateString("en-US", { month: "long", day: "numeric" }), ""];
    pred.grouped.forEach((g) => {
      const items = g.items.filter((i) => checked[i.item]);
      if (!items.length) return;
      lines.push(g.category.toUpperCase());
      items.forEach((i) => lines.push(`  [ ] ${i.item}  ×${qty[i.item] || i.qty}   ~${GT.money((i.estPrice / i.qty) * (qty[i.item] || i.qty))}`));
      lines.push("");
    });
    lines.push(`Estimated total: ${GT.money(selTotal)}`);
    const blob = new Blob([lines.join("\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "shopping-list.txt"; a.click();
    URL.revokeObjectURL(url);
  };

  const weekOf = new Date(new Date(GT.maxDate(rows)).getTime() + 86400000 * 7)
    .toLocaleDateString("en-US", { month: "short", day: "numeric" });
  if (!pred.items.length) {
    return (
      <div className="mx-auto max-w-2xl py-16 text-center">
        <span className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-neutral-100 text-neutral-400"><GIcon type="sparkle" size={24} /></span>
        <h2 className="text-lg font-semibold text-neutral-700">Not enough history yet</h2>
        <p className="mx-auto mt-2 max-w-sm text-sm text-neutral-500">We need at least a couple of purchases per item to spot a pattern. Import more history to get predictions.</p>
        <button onClick={goImport} className="mt-5 rounded-xl bg-green-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-green-700">Go to Import</button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900">Predict next week</h1>
          <p className="mt-1 text-sm text-neutral-500">Items you're likely to need by the week of {weekOf}, based on how often you usually buy them.</p>
        </div>
        <button onClick={() => setAll(!allOn)} className="inline-flex items-center gap-2 rounded-xl border border-neutral-200 bg-white px-4 py-2.5 text-sm font-semibold text-neutral-700 transition hover:bg-neutral-50">
          <GIcon type="check" size={16} /> {allOn ? "Clear all" : "Select all"}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* checklist */}
        <Card className="lg:col-span-2">
          <CardHead icon="cart" title="Predicted shopping list" sub={`${pred.items.length} items likely needed`}
            action={<span className="rounded-full bg-green-50 px-2.5 py-1 text-xs font-bold text-green-700">{selected.length} selected</span>} />
          <div className="px-5 py-2">
            {pred.grouped.map((g) => (
              <div key={g.category} className="border-b border-neutral-50 py-4 last:border-0">
                <div className="mb-1 flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: g.color }} />
                  <span className="text-[11px] font-bold uppercase tracking-wide text-neutral-400">{g.category}</span>
                </div>
                {g.items.map((i) => {
                  const st = statusOf(i);
                  const on = !!checked[i.item];
                  const q = qty[i.item] || i.qty;
                  return (
                    <div key={i.item} className="flex items-center gap-3 py-2">
                      <button onClick={() => toggle(i.item)}
                        className={"flex h-5 w-5 shrink-0 items-center justify-center rounded-md border-2 transition " + (on ? "border-green-600 bg-green-600 text-white" : "border-neutral-300 hover:border-green-400")}>
                        {on && <GIcon type="check" size={13} stroke={2.6} />}
                      </button>
                      <div className="min-w-0 flex-1">
                        <div className={"truncate text-sm font-medium " + (on ? "text-neutral-800" : "text-neutral-500")}>{i.item}</div>
                        <div className="mt-0.5 flex items-center gap-2 text-[11px] text-neutral-400">
                          <GIcon type="clock" size={11} /> {freqLabel(i.interval)} · last bought {i.daysSince}d ago
                        </div>
                      </div>
                      <span className={"hidden shrink-0 rounded-md px-2 py-1 font-mono text-[10px] font-semibold sm:inline " + (st.due ? "bg-green-50 text-green-700" : "bg-neutral-100 text-neutral-500")}>{st.t}</span>
                      <div className="flex shrink-0 items-center gap-1.5 rounded-lg border border-neutral-200 px-1">
                        <button onClick={() => bump(i.item, -1)} className="px-1.5 py-1 text-neutral-400 hover:text-neutral-700">−</button>
                        <span className="w-4 text-center text-sm font-semibold tabular-nums text-neutral-700">{q}</span>
                        <button onClick={() => bump(i.item, 1)} className="px-1.5 py-1 text-neutral-400 hover:text-neutral-700">+</button>
                      </div>
                      <span className="w-16 shrink-0 text-right text-sm font-semibold tabular-nums text-neutral-700">{GT.money((i.estPrice / i.qty) * q)}</span>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </Card>

        {/* side rail */}
        <div className="flex flex-col gap-4">
          <Card className="overflow-hidden">
            <div className="bg-green-600 px-5 py-5 text-white">
              <div className="text-xs font-medium uppercase tracking-wide text-green-100">Estimated total</div>
              <div className="mt-1 text-3xl font-bold tracking-tight">{GT.money(selTotal)}</div>
              <div className="mt-1 text-sm text-green-100">{selected.length} of {pred.items.length} items selected</div>
            </div>
            <div className="p-4">
              <button onClick={exportList} disabled={!selected.length}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-neutral-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-neutral-800 disabled:opacity-40">
                <GIcon type="download" size={16} /> Export shopping list
              </button>
            </div>
          </Card>

          <Card className="p-5">
            <div className="flex items-center gap-2 text-sm font-semibold text-neutral-800">
              <span className="text-green-600"><GIcon type="sparkle" size={16} /></span> How we predicted
            </div>
            <ul className="mt-3 space-y-3 text-sm text-neutral-500">
              <li className="flex gap-2.5"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-green-500" />We measure the <b className="font-semibold text-neutral-700">average days between purchases</b> for each item.</li>
              <li className="flex gap-2.5"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-green-500" />Compared against <b className="font-semibold text-neutral-700">days since you last bought it</b>.</li>
              <li className="flex gap-2.5"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-green-500" />Items due within <b className="font-semibold text-neutral-700">the next {horizon} days</b> land on this list.</li>
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { ScreenPredict });
