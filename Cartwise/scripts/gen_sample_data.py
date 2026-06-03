"""Generate data/Purchase_data.csv as a faithful Python port of the prototype's
seeded sample generator (design/gt-data.js → mulberry32 + generateSample).

Run from the project root:  uv run python scripts/gen_sample_data.py

The seed (20260601) and catalog reproduce the same ~417-row dataset shown in
the design screenshots ($1,758.84 / 25 trips / 33 items over the 90-day view).
"""
import csv
import math
from datetime import date, timedelta
from pathlib import Path

DAY = 86_400_000  # ms per day, matching the JS source
_EPOCH = date(1970, 1, 1)


def _days_since_epoch(y: int, m: int, d: int) -> int:
    return (date(y, m, d) - _EPOCH).days


START_MS = _days_since_epoch(2026, 1, 1) * DAY
TODAY_MS = _days_since_epoch(2026, 6, 1) * DAY

CATEGORIES = {
    "Produce": "#16a34a", "Dairy & eggs": "#eab308", "Bakery": "#d97706",
    "Meat & seafood": "#e2566b", "Pantry": "#0d9488", "Beverages": "#0ea5e9",
    "Snacks": "#8b5cf6", "Frozen": "#38bdf8", "Household": "#64748b",
}

STORES = ["Whole Foods", "Trader Joe's", "Costco", "Safeway", "Target"]

# [item, category, intervalDays, basePrice, typicalQty]
CATALOG = [
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
]

_MASK = 0xFFFFFFFF


def _u32(x: int) -> int:
    return x & _MASK


def _i32(x: int) -> int:
    x &= _MASK
    return x - 0x100000000 if x & 0x80000000 else x


def _imul(a: int, b: int) -> int:
    # JS Math.imul: low 32 bits of the product, as a signed int32
    return _i32((_u32(a) * _u32(b)) & _MASK)


def mulberry32(seed: int):
    """Exact port of the mulberry32 PRNG used in gt-data.js."""
    state = _i32(seed)

    def rng() -> float:
        nonlocal state
        a = _i32(state + 0x6D2B79F5)          # a = (a + 0x6D2B79F5) | 0
        state = a
        ua = _u32(a)
        t = _imul(ua ^ (ua >> 15), 1 | ua)    # Math.imul(a ^ (a>>>15), 1 | a)
        ut = _u32(t)
        inner = _imul(ut ^ (ut >> 7), 61 | ut)
        t = _u32(_u32(t + inner) ^ ut)        # (t + ...) ^ t  → uint32
        return (t ^ (t >> 14)) / 4294967296.0

    return rng


def _js_round(n: float) -> int:
    # JS Math.round: round half toward +infinity
    return math.floor(n + 0.5)


def _round2(n: float) -> float:
    return _js_round(n * 100) / 100


def _fmt(day_ms: int) -> str:
    return (_EPOCH + timedelta(days=day_ms // DAY)).isoformat()


def generate_sample() -> list[dict]:
    rnd = mulberry32(20260601)
    state = [
        {"item": item, "cat": cat, "interval": interval, "price": price, "qty": qty,
         "next": START_MS + rnd() * interval * DAY}
        for item, cat, interval, price, qty in CATALOG
    ]
    rows: list[dict] = []
    day = START_MS
    while day <= TODAY_MS - DAY:
        day += (2 + math.floor(rnd() * 4)) * DAY     # a trip every 2–5 days
        if day > TODAY_MS - DAY:
            break
        store = STORES[math.floor(rnd() * len(STORES))]
        date_str = _fmt(day)
        for s in state:
            if s["next"] > day:
                continue
            price_var = s["price"] * (1 + (rnd() - 0.5) * 0.16)   # ±8%
            q = s["qty"] + (1 if rnd() < 0.18 else 0)             # occasional bulk
            rows.append({
                "date": date_str, "store": store, "item": s["item"],
                "category": s["cat"], "quantity": q, "price": _round2(price_var),
            })
            jitter = 1 + (rnd() - 0.5) * 0.5                       # ±25% interval jitter
            s["next"] = day + s["interval"] * jitter * DAY
    # newest first, matching generateSample()'s sort
    rows.sort(key=lambda r: r["date"], reverse=True)
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    # Mirror toCSV(): oldest-first body, header without a unit column.
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "store", "item", "category", "quantity", "price"])
        for r in reversed(rows):
            w.writerow([r["date"], r["store"], r["item"], r["category"],
                        r["quantity"], f"{r['price']:.2f}"])


def _validate(rows: list[dict]) -> None:
    """Print the 90-day KPIs so they can be checked against the screenshots."""
    max_date = max(r["date"] for r in rows)
    cutoff = (date.fromisoformat(max_date) - timedelta(days=90)).isoformat()
    view = [r for r in rows if r["date"] >= cutoff]
    total = sum(r["price"] * r["quantity"] for r in view)
    trips = len({(r["date"], r["store"]) for r in view})
    items = len({r["item"] for r in view})
    units = sum(r["quantity"] for r in view)
    by_cat: dict[str, float] = {}
    for r in view:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + r["price"] * r["quantity"]
    print(f"rows total: {len(rows)}  | date range: {min(r['date'] for r in rows)} → {max_date}")
    print(f"90-day → total ${total:,.2f} | trips {trips} | items {items} | units {units} "
          f"| avg ${total/trips:,.2f}")
    print("90-day spend by category:")
    for cat, val in sorted(by_cat.items(), key=lambda kv: -kv[1]):
        print(f"  {cat:16} ${val:,.2f}")


if __name__ == "__main__":
    rows = generate_sample()
    out = Path(__file__).resolve().parent.parent / "data" / "Purchase_data.csv"
    write_csv(rows, out)
    print(f"Wrote {len(rows)} rows → {out}")
    _validate(rows)
