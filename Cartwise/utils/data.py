import io
import pandas as pd
import streamlit as st

REQUIRED_COLS = {"date", "store", "item", "category", "quantity", "price"}
SAMPLE_PATH = "data/Purchase_data.csv"


# ── Cross-reload data store ───────────────────────────────────────────
# Tab navigation uses anchor links (?tab=…) that trigger a full page reload,
# which clears st.session_state. This process-lifetime cache survives those
# reloads so an uploaded dataset is retained for the whole session.
# (Single-user local app, so a shared store is the intended behaviour.)
@st.cache_resource
def _data_store() -> dict:
    return {}


def remember(df: pd.DataFrame, source: str) -> None:
    store = _data_store()
    store["df"] = df
    store["source"] = source


def recall() -> tuple[pd.DataFrame | None, str | None]:
    store = _data_store()
    return store.get("df"), store.get("source")


def forget() -> None:
    store = _data_store()
    store.pop("df", None)
    store.pop("source", None)

CATEGORY_COLORS = {
    "Produce":        "#16a34a",
    "Dairy & eggs":   "#eab308",
    "Bakery":         "#d97706",
    "Meat & seafood": "#e2566b",
    "Pantry":         "#0d9488",
    "Beverages":      "#0ea5e9",
    "Snacks":         "#8b5cf6",
    "Frozen":         "#38bdf8",
    "Household":      "#64748b",
}


def load_sample() -> pd.DataFrame:
    return _clean(pd.read_csv(SAMPLE_PATH))


def load_upload(file) -> tuple[pd.DataFrame, str | None]:
    """Parse an st.file_uploader object. Returns (df, error_message)."""
    try:
        raw = pd.read_csv(io.StringIO(file.read().decode("utf-8", errors="replace")))
    except Exception as exc:
        return pd.DataFrame(), f"Couldn't parse file: {exc}"

    missing = REQUIRED_COLS - {c.lower().strip() for c in raw.columns}
    if missing:
        return pd.DataFrame(), f"Missing required columns: {', '.join(sorted(missing))}"

    return _clean(raw), None


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.lower().strip() for c in df.columns]

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1)
    df["price"] = (
        df["price"].astype(str).str.replace(r"[^\d.\-]", "", regex=True)
    )
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
    df = df.dropna(subset=["date"])
    df = df.sort_values("date", ascending=False).reset_index(drop=True)
    return df


def summary(df: pd.DataFrame) -> dict:
    return {
        "rows": len(df),
        "date_min": df["date"].min(),
        "date_max": df["date"].max(),
        "stores": sorted(df["store"].dropna().unique().tolist()),
    }


def filter_period(df: pd.DataFrame, period) -> pd.DataFrame:
    """Filter to last N days relative to the latest date, or 'all'."""
    if period == "all":
        return df
    cutoff = df["date"].max() - pd.Timedelta(days=int(period))
    return df[df["date"] >= cutoff].copy()


def kpis(df: pd.DataFrame) -> dict:
    df2 = df.copy()
    df2["line_total"] = df2["price"] * df2["quantity"]
    total = df2["line_total"].sum()
    trips = df2.groupby([df2["date"].dt.date, "store"]).ngroups
    items = df2["item"].nunique()
    avg_basket = total / trips if trips > 0 else 0
    units = int(df2["quantity"].sum())
    return {
        "total": total,
        "trips": trips,
        "avg_basket": avg_basket,
        "items": items,
        "units": units,
    }


def spend_by_category(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    df2["line_total"] = df2["price"] * df2["quantity"]
    result = df2.groupby("category")["line_total"].sum().reset_index()
    result.columns = ["category", "value"]
    result = result.sort_values("value", ascending=False).reset_index(drop=True)
    result["color"] = result["category"].map(lambda c: CATEGORY_COLORS.get(c, "#94a3b8"))
    return result


def repurchase_frequency(df: pd.DataFrame, limit: int = 8) -> pd.DataFrame:
    result = df.groupby(["item", "category"]).size().reset_index(name="count")
    result = result.sort_values("count", ascending=False).head(limit).reset_index(drop=True)
    result["color"] = result["category"].map(lambda c: CATEGORY_COLORS.get(c, "#94a3b8"))
    return result


def spend_over_time(df: pd.DataFrame) -> pd.DataFrame:
    """Weekly spend totals, bucketed to Monday of each week."""
    df2 = df.copy()
    df2["line_total"] = df2["price"] * df2["quantity"]
    # Get the Monday of each date's week (dayofweek: 0=Mon, 6=Sun)
    df2["week"] = (df2["date"] - pd.to_timedelta(df2["date"].dt.dayofweek, unit="D")).dt.normalize()
    result = df2.groupby("week")["line_total"].sum().reset_index()
    result.columns = ["week", "total"]
    result = result.sort_values("week").reset_index(drop=True)
    return result


def predict_next_week(df: pd.DataFrame, horizon: int = 7, min_items: int = 10) -> dict:
    """Port of GT.predictNextWeek: avg-interval vs days-since heuristic.

    Returns {"items": [...], "grouped": [{"category", "color", "items": [...]}]}.
    Each item has: item, category, color, interval, days_since, due_in, qty, est_price, bought.
    Items with ≥2 purchases and due_in ≤ horizon are included; if fewer than
    `min_items` qualify, the next-soonest items are added so the list shows at
    least `min_items` (when that much purchase history exists).
    """
    by_item: dict = {}
    for _, row in df.iterrows():
        item = row["item"]
        if item not in by_item:
            by_item[item] = {
                "item": item,
                "category": str(row["category"]),
                "dates": [],
                "qtys": [],
                "prices": [],
            }
        by_item[item]["dates"].append(row["date"])
        by_item[item]["qtys"].append(float(row["quantity"]))
        by_item[item]["prices"].append(float(row["price"]))

    latest = df["date"].max()
    candidates = []
    for it in by_item.values():
        if len(it["dates"]) < 2:
            continue
        dates = sorted(it["dates"])
        gaps = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
        interval = round(sum(gaps) / len(gaps))
        if interval <= 0:
            continue
        last = dates[-1]
        days_since = (latest - last).days
        due_in = interval - days_since
        qtys_sorted = sorted(it["qtys"])
        qty = qtys_sorted[len(qtys_sorted) // 2]  # median
        avg_price = sum(it["prices"]) / len(it["prices"])
        candidates.append({
            "item": it["item"],
            "category": it["category"],
            "color": CATEGORY_COLORS.get(it["category"], "#94a3b8"),
            "interval": interval,
            "days_since": days_since,
            "due_in": due_in,
            "qty": max(1, int(qty)),
            "est_price": round(avg_price * qty, 2),
            "bought": len(it["dates"]),
        })

    # Soonest first; keep everything due within the horizon, but always show at
    # least `min_items` by topping up with the next-soonest candidates.
    candidates.sort(key=lambda x: x["due_in"])
    due = [c for c in candidates if c["due_in"] <= horizon]
    items = due if len(due) >= min_items else candidates[:min_items]

    groups: dict = {}
    for it in items:
        cat = it["category"]
        if cat not in groups:
            groups[cat] = {
                "category": cat,
                "color": CATEGORY_COLORS.get(cat, "#94a3b8"),
                "items": [],
            }
        groups[cat]["items"].append(it)

    grouped = list(groups.values())
    grouped.sort(key=lambda g: min(i["due_in"] for i in g["items"]))

    return {"items": items, "grouped": grouped}
