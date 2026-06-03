/* Recharts-based chart components. Recharts loaded as UMD global. */
const {
  ResponsiveContainer, PieChart, Pie, Cell,
  BarChart, Bar: RBar, XAxis, YAxis, CartesianGrid, Tooltip,
  AreaChart, Area, LabelList,
} = Recharts;

const GTfmt = window.GT;

/* ---- shared tooltip ---- */
function ChartTip({ active, payload, label, fmt }) {
  if (!active || !payload || !payload.length) return null;
  const p = payload[0];
  return (
    <div className="rounded-lg border border-neutral-200 bg-white px-3 py-2 shadow-lg text-sm">
      <div className="font-semibold text-neutral-800">{p.payload.name || p.payload.item || label}</div>
      <div className="text-neutral-500">{fmt ? fmt(p.value, p.payload) : p.value}</div>
    </div>
  );
}

/* ---- DONUT: spend by category ---- */
function SpendDonut({ data, total }) {
  return (
    <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-center sm:gap-8">
      <div className="relative shrink-0" style={{ width: 220, height: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data} dataKey="value" nameKey="name"
              cx="50%" cy="50%" innerRadius={68} outerRadius={104}
              paddingAngle={2} stroke="none" startAngle={90} endAngle={-270}
            >
              {data.map((d, i) => <Cell key={i} fill={d.color} />)}
            </Pie>
            <Tooltip content={<ChartTip fmt={(v) => GTfmt.money(v)} />} />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xs font-medium uppercase tracking-wide text-neutral-400">Total spend</span>
          <span className="text-2xl font-bold text-neutral-800">{GTfmt.money(total)}</span>
        </div>
      </div>
      <div className="flex w-full flex-col gap-2.5">
        {data.map((d) => (
          <div key={d.name} className="flex items-center gap-3 text-sm">
            <span className="h-3 w-3 shrink-0 rounded-sm" style={{ background: d.color }} />
            <span className="truncate text-neutral-600">{d.name}</span>
            <span className="ml-auto font-semibold text-neutral-800">{GTfmt.money(d.value)}</span>
            <span className="w-12 text-right text-xs text-neutral-400">
              {total ? Math.round((d.value / total) * 100) : 0}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---- BARS: repurchase frequency (horizontal) ---- */
function RepurchaseBars({ data }) {
  const h = Math.max(220, data.length * 38);
  return (
    <ResponsiveContainer width="100%" height={h}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 30, left: 8, bottom: 4 }} barCategoryGap={10}>
        <CartesianGrid horizontal={false} stroke="#f0f0ef" />
        <XAxis type="number" domain={[0, "dataMax"]} tick={{ fontSize: 11, fill: "#9ca3af" }} axisLine={false} tickLine={false} allowDecimals={false} />
        <YAxis
          type="category" dataKey="item" width={118}
          tick={{ fontSize: 12, fill: "#4b5563" }} axisLine={false} tickLine={false}
        />
        <Tooltip cursor={{ fill: "#f6f7f6" }} content={<ChartTip fmt={(v) => v + " purchases"} />} />
        <RBar dataKey="count" radius={[0, 5, 5, 0]} maxBarSize={22} isAnimationActive={false}>
          {data.map((d, i) => <Cell key={i} fill={d.color} />)}
          <LabelList dataKey="count" position="right" style={{ fontSize: 11, fill: "#6b7280", fontWeight: 600 }} />
        </RBar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/* ---- AREA: spend over time (weekly) ---- */
function TrendArea({ data }) {
  const fmtWeek = (w) => {
    const d = new Date(w);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };
  return (
    <ResponsiveContainer width="100%" height={170}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="gtTrend" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#16a34a" stopOpacity={0.22} />
            <stop offset="100%" stopColor="#16a34a" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid vertical={false} stroke="#f0f0ef" />
        <XAxis dataKey="week" tickFormatter={fmtWeek} tick={{ fontSize: 11, fill: "#9ca3af" }} axisLine={false} tickLine={false} minTickGap={24} />
        <YAxis tickFormatter={(v) => GTfmt.moneyShort(v)} tick={{ fontSize: 11, fill: "#9ca3af" }} axisLine={false} tickLine={false} width={44} />
        <Tooltip
          content={({ active, payload }) =>
            active && payload && payload.length ? (
              <div className="rounded-lg border border-neutral-200 bg-white px-3 py-2 text-sm shadow-lg">
                <div className="font-semibold text-neutral-800">{GTfmt.money(payload[0].value)}</div>
                <div className="text-neutral-500">Week of {fmtWeek(payload[0].payload.week)}</div>
              </div>
            ) : null
          }
        />
        <Area type="monotone" dataKey="total" stroke="#16a34a" strokeWidth={2.5} fill="url(#gtTrend)" dot={false} activeDot={{ r: 4, fill: "#16a34a" }} isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

Object.assign(window, { SpendDonut, RepurchaseBars, TrendArea });
