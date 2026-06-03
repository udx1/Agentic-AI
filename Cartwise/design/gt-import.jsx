/* TAB 1 — Import Purchases: real CSV upload, parsing, searchable/sortable table. */

function StatusChip({ icon, children, tone = "default" }) {
  const tones = {
    default: "bg-neutral-100 text-neutral-600",
    ok: "bg-green-50 text-green-700 ring-1 ring-green-200",
    info: "bg-sky-50 text-sky-700 ring-1 ring-sky-100",
  };
  return (
    <span className={"inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold " + tones[tone]}>
      {icon && <GIcon type={icon} size={14} />}{children}
    </span>
  );
}

function ScreenImport({ rows, source, onData, onReset }) {
  const [dragOver, setDragOver] = React.useState(false);
  const [error, setError] = React.useState("");
  const [query, setQuery] = React.useState("");
  const [sort, setSort] = React.useState({ key: "date", dir: "desc" });
  const [limit, setLimit] = React.useState(40);
  const fileRef = React.useRef(null);

  const handleFile = (file) => {
    setError("");
    if (!file) return;
    if (!/\.csv$/i.test(file.name) && file.type !== "text/csv") {
      setError("Please choose a .csv file.");
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const parsed = GT.parseCSV(e.target.result);
        if (!parsed.length) { setError("No valid rows found. Expected columns: date, store, item, category, quantity, price."); return; }
        onData(parsed, file.name);
        setLimit(40);
      } catch (err) {
        setError("Couldn't parse that file. " + err.message);
      }
    };
    reader.readAsText(file);
  };

  const onDrop = (e) => {
    e.preventDefault(); setDragOver(false);
    handleFile(e.dataTransfer.files && e.dataTransfer.files[0]);
  };

  const downloadSample = () => {
    const blob = new Blob([GT.toCSV(rows)], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "grocery-purchases-sample.csv"; a.click();
    URL.revokeObjectURL(url);
  };

  const dateRange = React.useMemo(() => {
    if (!rows.length) return "—";
    const fmt = (s) => new Date(s).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    return fmt(rows[rows.length - 1].date) + " – " + fmt(rows[0].date);
  }, [rows]);

  const filtered = React.useMemo(() => {
    let r = rows;
    if (query.trim()) {
      const q = query.toLowerCase();
      r = r.filter((x) => (x.item + " " + x.store + " " + x.category).toLowerCase().includes(q));
    }
    const { key, dir } = sort;
    const mul = dir === "asc" ? 1 : -1;
    r = r.slice().sort((a, b) => {
      let av = a[key], bv = b[key];
      if (key === "price" || key === "quantity") return (av - bv) * mul;
      return (av < bv ? -1 : av > bv ? 1 : 0) * mul;
    });
    return r;
  }, [rows, query, sort]);

  const setSortKey = (key) =>
    setSort((s) => ({ key, dir: s.key === key && s.dir === "desc" ? "asc" : "desc" }));

  const cols = [
    { key: "date", label: "Date", align: "left", w: "w-28" },
    { key: "store", label: "Store", align: "left", w: "" },
    { key: "item", label: "Item", align: "left", w: "" },
    { key: "category", label: "Category", align: "left", w: "" },
    { key: "quantity", label: "Qty", align: "right", w: "w-16" },
    { key: "price", label: "Price", align: "right", w: "w-24" },
  ];

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900">Import purchases</h1>
          <p className="mt-1 text-sm text-neutral-500">Upload a CSV of your grocery receipts. Everything is parsed in your browser — nothing leaves this page.</p>
        </div>
        <div className="flex gap-2.5">
          <button onClick={downloadSample} className="inline-flex items-center gap-2 rounded-xl border border-neutral-200 bg-white px-4 py-2.5 text-sm font-semibold text-neutral-700 transition hover:bg-neutral-50">
            <GIcon type="download" size={16} /> Sample CSV
          </button>
          <button onClick={() => fileRef.current && fileRef.current.click()} className="inline-flex items-center gap-2 rounded-xl bg-green-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-green-700">
            <GIcon type="upload" size={16} /> Upload CSV
          </button>
        </div>
      </div>

      <input ref={fileRef} type="file" accept=".csv,text/csv" className="hidden"
        onChange={(e) => handleFile(e.target.files[0])} />

      {/* dropzone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => fileRef.current && fileRef.current.click()}
        className={"group flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed px-6 py-10 text-center transition " +
          (dragOver ? "border-green-500 bg-green-50" : "border-neutral-300 bg-neutral-50/60 hover:border-green-400 hover:bg-green-50/40")}
      >
        <span className={"flex h-14 w-14 items-center justify-center rounded-full transition " + (dragOver ? "bg-green-600 text-white" : "bg-white text-green-600 ring-1 ring-neutral-200 group-hover:ring-green-300")}>
          <GIcon type="upload" size={26} />
        </span>
        <p className="mt-1 text-sm font-semibold text-neutral-700">{dragOver ? "Drop to import" : "Drag & drop your CSV here"}</p>
        <p className="text-xs text-neutral-400">or click to browse · columns: date, store, item, category, quantity, price</p>
      </div>

      {error && (
        <div className="mt-3 flex items-center gap-2 rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700 ring-1 ring-rose-100">
          <GIcon type="x" size={16} /> {error}
        </div>
      )}

      {/* status */}
      <div className="mt-4 flex flex-wrap items-center gap-2.5">
        <StatusChip icon="check" tone="ok">
          {source === "sample" ? "Sample data loaded" : "Imported"} · {rows.length} rows
        </StatusChip>
        <StatusChip icon="calendar">{dateRange}</StatusChip>
        {source !== "sample" && (
          <button onClick={onReset} className="inline-flex items-center gap-1.5 rounded-full bg-neutral-100 px-3 py-1.5 text-xs font-semibold text-neutral-500 transition hover:bg-neutral-200 hover:text-neutral-700">
            <GIcon type="trash" size={13} /> Reset to sample
          </button>
        )}
      </div>

      {/* table */}
      <Card className="mt-6 overflow-hidden">
        <CardHead icon="list" title="Purchase history" sub={`${filtered.length} of ${rows.length} rows`}
          action={
            <div className="relative">
              <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400"><GIcon type="search" size={15} /></span>
              <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search items, stores…"
                className="w-44 rounded-lg border border-neutral-200 bg-neutral-50 py-2 pl-9 pr-3 text-sm text-neutral-700 outline-none transition focus:border-green-400 focus:bg-white sm:w-56" />
            </div>
          } />
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-100 bg-neutral-50/70 text-left">
                {cols.map((c) => (
                  <th key={c.key} className={"px-5 py-3 " + (c.align === "right" ? "text-right" : "text-left") + " " + c.w}>
                    <button onClick={() => setSortKey(c.key)}
                      className={"inline-flex items-center gap-1 text-[11px] font-bold uppercase tracking-wide transition " + (sort.key === c.key ? "text-green-700" : "text-neutral-400 hover:text-neutral-600")}>
                      {c.label}
                      {sort.key === c.key && <GIcon type="chevron" size={12} className={sort.dir === "asc" ? "rotate-180" : ""} />}
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, limit).map((r) => (
                <tr key={r.id} className="border-b border-neutral-50 transition hover:bg-neutral-50/60">
                  <td className="whitespace-nowrap px-5 py-3 text-neutral-500">
                    {new Date(r.date).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                  </td>
                  <td className="px-5 py-3 text-neutral-600">{r.store}</td>
                  <td className="px-5 py-3 font-medium text-neutral-800">{r.item}</td>
                  <td className="px-5 py-3">
                    <span className="inline-flex items-center gap-1.5 text-neutral-500">
                      <span className="h-2 w-2 rounded-full" style={{ background: GT.CATEGORIES[r.category] || "#94a3b8" }} />
                      {r.category}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right tabular-nums text-neutral-500">{r.quantity}</td>
                  <td className="px-5 py-3 text-right font-semibold tabular-nums text-neutral-800">{GT.money(r.price)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length > limit && (
          <div className="border-t border-neutral-100 p-3 text-center">
            <button onClick={() => setLimit((l) => l + 40)} className="rounded-lg px-4 py-2 text-sm font-semibold text-green-700 transition hover:bg-green-50">
              Show 40 more ({filtered.length - limit} remaining)
            </button>
          </div>
        )}
      </Card>
    </div>
  );
}

Object.assign(window, { ScreenImport });
