/* ============================================================
   Grocery Tracker — data layer (plain JS)
   Sample data generation, CSV parsing, aggregations, prediction.
   Exposes window.GT
   ============================================================ */
(function () {
  const TODAY = new Date("2026-06-01T00:00:00");
  const START = new Date("2026-01-01T00:00:00");
  const DAY = 86400000;

  /* category palette — curated, distinguishable, grocery-toned */
  const CATEGORIES = {
    "Produce":          "#16a34a",
    "Dairy & eggs":     "#eab308",
    "Bakery":           "#d97706",
    "Meat & seafood":   "#e2566b",
    "Pantry":           "#0d9488",
    "Beverages":        "#0ea5e9",
    "Snacks":           "#8b5cf6",
    "Frozen":           "#38bdf8",
    "Household":        "#64748b",
  };

  const STORES = ["Whole Foods", "Trader Joe's", "Costco", "Safeway", "Target"];

  /* catalog: [item, category, intervalDays, basePrice, typicalQty] */
  const CATALOG = [
    ["Bananas", "Produce", 5, 1.89, 2],
    ["Apples", "Produce", 7, 4.49, 1],
    ["Baby Spinach", "Produce", 6, 3.99, 1],
    ["Tomatoes", "Produce", 8, 2.99, 1],
    ["Avocados", "Produce", 5, 4.99, 1],
    ["Carrots", "Produce", 11, 1.79, 1],
    ["Bell Peppers", "Produce", 9, 3.49, 1],
    ["Whole Milk", "Dairy & eggs", 4, 3.79, 1],
    ["Large Eggs", "Dairy & eggs", 6, 4.29, 1],
    ["Greek Yogurt", "Dairy & eggs", 7, 5.49, 2],
    ["Butter", "Dairy & eggs", 15, 4.99, 1],
    ["Cheddar Cheese", "Dairy & eggs", 10, 6.49, 1],
    ["Sourdough Bread", "Bakery", 5, 4.49, 1],
    ["Bagels", "Bakery", 9, 3.99, 1],
    ["Chicken Breast", "Meat & seafood", 7, 9.99, 1],
    ["Ground Beef", "Meat & seafood", 10, 7.49, 1],
    ["Atlantic Salmon", "Meat & seafood", 13, 12.99, 1],
    ["Pasta", "Pantry", 16, 1.99, 2],
    ["Jasmine Rice", "Pantry", 22, 8.99, 1],
    ["Olive Oil", "Pantry", 32, 11.99, 1],
    ["Cereal", "Pantry", 12, 4.79, 1],
    ["Coffee Beans", "Pantry", 14, 13.99, 1],
    ["Peanut Butter", "Pantry", 21, 5.29, 1],
    ["Orange Juice", "Beverages", 8, 4.99, 1],
    ["Sparkling Water", "Beverages", 6, 5.99, 1],
    ["Tortilla Chips", "Snacks", 9, 3.99, 1],
    ["Dark Chocolate", "Snacks", 12, 3.49, 1],
    ["Frozen Berries", "Frozen", 14, 6.99, 1],
    ["Frozen Pizza", "Frozen", 12, 5.99, 1],
    ["Paper Towels", "Household", 19, 9.99, 1],
    ["Dish Soap", "Household", 26, 3.99, 1],
    ["Laundry Detergent", "Household", 36, 12.99, 1],
    ["Trash Bags", "Household", 28, 8.49, 1],
  ];

  /* seeded RNG for stable-but-varied sample data */
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function fmtDate(d) {
    return d.toISOString().slice(0, 10);
  }

  /* generate the sample purchase history as realistic multi-item shopping trips */
  function generateSample() {
    const rnd = mulberry32(20260601);
    const round2 = (n) => Math.round(n * 100) / 100;
    // each item tracks when it's next due to be bought
    const state = CATALOG.map(([item, cat, interval, price, qty]) => ({
      item, cat, interval, price, qty,
      next: START.getTime() + rnd() * interval * DAY,
    }));
    const rows = [];
    let id = 0;
    let day = START.getTime();
    while (day <= TODAY.getTime() - DAY) {
      day += (2 + Math.floor(rnd() * 4)) * DAY; // a shopping trip every 2–5 days
      if (day > TODAY.getTime() - DAY) break;
      const store = STORES[Math.floor(rnd() * STORES.length)];
      const dateStr = fmtDate(new Date(day));
      state.forEach((s) => {
        if (s.next > day) return;
        const priceVar = s.price * (1 + (rnd() - 0.5) * 0.16); // ±8%
        const q = s.qty + (rnd() < 0.18 ? 1 : 0);              // occasional bulk
        rows.push({ id: id++, date: dateStr, store, item: s.item, category: s.cat, quantity: q, price: round2(priceVar) });
        const jitter = 1 + (rnd() - 0.5) * 0.5;                // ±25% interval jitter
        s.next = day + s.interval * jitter * DAY;
      });
    }
    rows.sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0));
    return rows;
  }

  /* ---- CSV ---- */
  const HEADER_MAP = {
    date: "date", store: "store", shop: "store", merchant: "store",
    item: "item", product: "item", name: "item", description: "item",
    category: "category", cat: "category", type: "category",
    quantity: "quantity", qty: "quantity", count: "quantity",
    price: "price", cost: "price", amount: "price", total: "price",
  };

  function parseCSV(text) {
    const res = Papa.parse(text.trim(), { header: true, skipEmptyLines: true });
    const rows = [];
    let id = 0;
    res.data.forEach((raw) => {
      const norm = {};
      Object.keys(raw).forEach((k) => {
        const key = HEADER_MAP[String(k).trim().toLowerCase()];
        if (key) norm[key] = raw[k];
      });
      if (!norm.item && !norm.date) return;
      const d = norm.date ? new Date(norm.date) : null;
      rows.push({
        id: id++,
        date: d && !isNaN(d) ? fmtDate(d) : String(norm.date || ""),
        store: (norm.store || "—").toString().trim(),
        item: (norm.item || "—").toString().trim(),
        category: (norm.category || "Uncategorized").toString().trim(),
        quantity: Math.max(1, parseFloat(norm.quantity) || 1),
        price: Math.max(0, parseFloat(String(norm.price).replace(/[^0-9.\-]/g, "")) || 0),
      });
    });
    rows.sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0));
    return rows;
  }

  function toCSV(rows) {
    const head = "date,store,item,category,quantity,price";
    const body = rows
      .slice()
      .reverse()
      .map((r) => `${r.date},${r.store},"${r.item}",${r.category},${r.quantity},${r.price.toFixed(2)}`)
      .join("\n");
    return head + "\n" + body;
  }

  /* ---- helpers ---- */
  const lineTotal = (r) => r.price * r.quantity;
  const money = (n) =>
    "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const moneyShort = (n) =>
    n >= 1000 ? "$" + (n / 1000).toFixed(1) + "k" : "$" + n.toFixed(0);

  function maxDate(rows) {
    return rows.reduce((m, r) => (r.date > m ? r.date : m), rows[0] ? rows[0].date : fmtDate(TODAY));
  }

  /* period filter: 'all' | 30 | 90 (days back from latest date) */
  function filterPeriod(rows, period) {
    if (period === "all") return rows;
    const end = new Date(maxDate(rows));
    const cutoff = end.getTime() - period * DAY;
    return rows.filter((r) => new Date(r.date).getTime() >= cutoff);
  }

  /* ---- aggregations ---- */
  function kpis(rows) {
    const total = rows.reduce((s, r) => s + lineTotal(r), 0);
    const trips = new Set(rows.map((r) => r.date + "|" + r.store)).size;
    const items = new Set(rows.map((r) => r.item)).size;
    return {
      total,
      trips,
      avgBasket: trips ? total / trips : 0,
      items,
      units: rows.reduce((s, r) => s + r.quantity, 0),
    };
  }

  function spendByCategory(rows) {
    const m = {};
    rows.forEach((r) => (m[r.category] = (m[r.category] || 0) + lineTotal(r)));
    return Object.entries(m)
      .map(([name, value]) => ({ name, value: Math.round(value * 100) / 100, color: CATEGORIES[name] || "#94a3b8" }))
      .sort((a, b) => b.value - a.value);
  }

  function repurchaseFrequency(rows, limit = 8) {
    const m = {};
    rows.forEach((r) => {
      if (!m[r.item]) m[r.item] = { item: r.item, category: r.category, count: 0 };
      m[r.item].count += 1;
    });
    return Object.values(m)
      .map((x) => ({ ...x, color: CATEGORIES[x.category] || "#94a3b8" }))
      .sort((a, b) => b.count - a.count)
      .slice(0, limit);
  }

  function spendOverTime(rows) {
    // weekly buckets
    const m = {};
    rows.forEach((r) => {
      const d = new Date(r.date);
      const day = d.getDay();
      const monday = new Date(d.getTime() - ((day + 6) % 7) * DAY);
      const key = fmtDate(monday);
      m[key] = (m[key] || 0) + lineTotal(r);
    });
    return Object.entries(m)
      .map(([week, total]) => ({ week, total: Math.round(total * 100) / 100 }))
      .sort((a, b) => (a.week < b.week ? -1 : 1));
  }

  /* ---- prediction: avg interval vs. days since last purchase ---- */
  function predictNextWeek(rows, horizon = 7) {
    const byItem = {};
    rows.forEach((r) => {
      if (!byItem[r.item]) byItem[r.item] = { item: r.item, category: r.category, dates: [], qtys: [], prices: [] };
      byItem[r.item].dates.push(r.date);
      byItem[r.item].qtys.push(r.quantity);
      byItem[r.item].prices.push(r.price);
    });

    const latest = new Date(maxDate(rows)).getTime();
    const median = (arr) => {
      const s = arr.slice().sort((a, b) => a - b);
      return s[Math.floor(s.length / 2)];
    };
    const avg = (arr) => arr.reduce((a, b) => a + b, 0) / arr.length;

    const items = [];
    Object.values(byItem).forEach((it) => {
      if (it.dates.length < 2) return; // need a pattern
      const ds = it.dates.slice().sort();
      const gaps = [];
      for (let i = 1; i < ds.length; i++) {
        gaps.push((new Date(ds[i]) - new Date(ds[i - 1])) / DAY);
      }
      const interval = Math.round(avg(gaps));
      if (interval <= 0) return;
      const last = new Date(ds[ds.length - 1]).getTime();
      const daysSince = Math.round((latest - last) / DAY);
      const dueIn = interval - daysSince; // days until next expected purchase
      if (dueIn > horizon) return;        // not needed within horizon
      const qty = median(it.qtys);
      const price = avg(it.prices);
      items.push({
        item: it.item,
        category: it.category,
        color: CATEGORIES[it.category] || "#94a3b8",
        interval,
        daysSince,
        dueIn,
        qty,
        estPrice: price * qty,
        bought: it.dates.length,
      });
    });

    items.sort((a, b) => a.dueIn - b.dueIn);
    // group by category, preserving due-order within
    const groups = {};
    items.forEach((it) => {
      (groups[it.category] = groups[it.category] || []).push(it);
    });
    const grouped = Object.entries(groups)
      .map(([category, list]) => ({ category, color: CATEGORIES[category] || "#94a3b8", items: list }))
      .sort((a, b) => Math.min(...a.items.map((i) => i.dueIn)) - Math.min(...b.items.map((i) => i.dueIn)));

    return { items, grouped, estTotal: items.reduce((s, i) => s + i.estPrice, 0) };
  }

  window.GT = {
    TODAY, CATEGORIES, STORES,
    generateSample, parseCSV, toCSV,
    lineTotal, money, moneyShort, maxDate, filterPeriod,
    kpis, spendByCategory, repurchaseFrequency, spendOverTime, predictNextWeek,
  };
})();
