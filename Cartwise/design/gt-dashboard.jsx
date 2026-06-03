/* TAB 2 — Dashboard: KPIs + spend donut + repurchase bars + trend, with period filter. */

function KpiCard({ label, value, sub, icon, accent }) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-neutral-400">{label}</span>
        <span className={"flex h-8 w-8 items-center justify-center rounded-lg " + (accent ? "bg-green-50 text-green-600" : "bg-neutral-100 text-neutral-400")}>
          <GIcon type={icon} size={16} />
        </span>
      </div>
      <div className="mt-3 text-[26px] font-bold leading-none tracking-tight text-neutral-900">{value}</div>
      {sub && <div className="mt-2 text-xs text-neutral-400">{sub}</div>}
    </Card>
  );
}

function PeriodToggle({ value, onChange }) {
  const opts = [{ v: 30, l: "30 days" }, { v: 90, l: "90 days" }, { v: "all", l: "All time" }];
  return (
    <div className="inline-flex rounded-xl bg-neutral-100 p-1">
      {opts.map((o) => (
        <button key={o.v} onClick={() => onChange(o.v)}
          className={"rounded-lg px-3.5 py-1.5 text-sm font-semibold transition " +
            (value === o.v ? "bg-white text-neutral-800 shadow-sm" : "text-neutral-500 hover:text-neutral-700")}>
          {o.l}
        </button>
      ))}
    </div>
  );
}

function ScreenDashboard({ rows, period, onPeriod, topN = 8 }) {
  const view = React.useMemo(() => GT.filterPeriod(rows, period), [rows, period]);
  const k = React.useMemo(() => GT.kpis(view), [view]);
  const byCat = React.useMemo(() => GT.spendByCategory(view), [view]);
  const freq = React.useMemo(() => GT.repurchaseFrequency(view, topN), [view, topN]);
  const trend = React.useMemo(() => GT.spendOverTime(view), [view]);
  const topItem = freq[0];

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900">Dashboard</h1>
          <p className="mt-1 text-sm text-neutral-500">Where your grocery money goes and what you buy most often.</p>
        </div>
        <PeriodToggle value={period} onChange={onPeriod} />
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard label="Total spend" value={GT.money(k.total)} sub={`${k.units} items across ${k.trips} trips`} icon="cart" accent />
        <KpiCard label="Shopping trips" value={k.trips} sub="distinct store visits" icon="store" />
        <KpiCard label="Avg. basket" value={GT.money(k.avgBasket)} sub="spend per trip" icon="trend" />
        <KpiCard label="Items tracked" value={k.items} sub="unique products" icon="list" />
      </div>

      {/* charts */}
      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHead icon="donut" title="Spend by category" sub="share of total grocery spend" />
          <div className="p-5">
            {byCat.length ? <SpendDonut data={byCat} total={k.total} /> : <Empty />}
          </div>
        </Card>
        <Card className="lg:col-span-2">
          <CardHead icon="bars" title="Repurchase frequency"
            sub={topItem ? `most bought: ${topItem.item}` : "how often items are bought"} />
          <div className="p-5 pr-3">
            {freq.length ? <RepurchaseBars data={freq} /> : <Empty />}
          </div>
        </Card>
      </div>

      {/* trend */}
      <Card className="mt-4">
        <CardHead icon="trend" title="Spend over time" sub="weekly totals"
          action={<span className="text-xs font-medium text-neutral-400">{trend.length} weeks</span>} />
        <div className="p-5">
          {trend.length ? <TrendArea data={trend} /> : <Empty />}
        </div>
      </Card>
    </div>
  );
}

function Empty() {
  return <div className="flex h-40 items-center justify-center text-sm text-neutral-400">No data in this period.</div>;
}

Object.assign(window, { ScreenDashboard });
