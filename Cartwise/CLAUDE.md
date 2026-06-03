# Project: Cartwise

## Project Overview
A Streamlit app to track grocery purchases and forecast future purchases,
built from a Claude-designed prototype.

Most households do big grocery runs over the weekend and quick errands during the week. Figuring out what to buy falls on the individual to mentally track what's in the pantry and what's run out. There is incredible value hidden in those weekly grocery receipts — by tracking purchases over time, we can uncover consumption patterns, spending habits, price trends, and store comparisons.

The app uses historical data to predict what needs to be purchased next week and help optimize budget, timing, and store choice.

### MVP Features (Phase 1)
1. **Receipt Import** — Upload a CSV file (`data/Purchase_data.csv`).
2. **Spending Dashboard** — Visual breakdown of spend by category, store, and
   time period using Plotly charts.
3. **Purchase Prediction (stub)** — 
A  prediction tab showing top recurring items by i) measuring the
average days between purchases for each item.
ii) Compared against days since last bought it
iii) Items due within the next 7 days
land on this list. Full ML forecasting is Phase 2.

### Data Schema (`Purchase_data.csv`)
| Column   | Type       | Description                        |
|----------|------------|------------------------------------|
| date     | YYYY-MM-DD | Transaction date                   |
| store    | str        | Store or vendor name               |
| item     | str        | Product name                       |
| category | str        | Product category                   |
| quantity | float      | Product quantity                   |
| unit     | str        | Unit of measurement (e.g. lbs, oz) |
| price    | float      | Item price in USD                  |

### Current Phase
Phase 1 — Data ingestion and spending dashboard. Prediction tab is a stub showing top recurring items by purchase frequency (no ML yet).
Phase 2 — Full purchase forecasting using time-series or recurrence modeling.

Stack:
- Python 3.14
- Streamlit (UI framework)
- UV (package and project manager — replaces pip/venv)
- plotly



## Package Management — UV (CRITICAL)
This project uses UV exclusively. Never use `pip install` or `python -m venv`.

Initialize the project (already done):
```bash
uv init
```

Add a dependency:
```bash
uv add streamlit
uv add pandas plotly  # add multiple at once
```

Remove a dependency:
```bash
uv remove <package>
```

Run any Python script or command:
```bash
uv run python script.py
uv run streamlit run app.py
```

Sync the environment (after cloning or pulling):
```bash
uv sync
```

The lock file is `uv.lock` — always commit it to git.
Never edit `pyproject.toml` manually for dependencies; use `uv add/remove`.

## Running the App
```bash
uv run streamlit run app.py
```
Default port: 8501. To use a different port:
```bash
uv run streamlit run app.py --server.port 8502
```

## UI Design Handoff

The UI was prototyped as a React/JSX app in Claude. All design files are in
the project root. Implement the Streamlit app to match the prototype closely.
Do not redesign — if something is unclear, ask before deviating.

### Prototype Files (Source of Truth)
| File | Purpose |
|---|---|
| `gt-app.jsx` | App shell, tab structure, and navigation |
| `gt-dashboard.jsx` | Spending dashboard layout and components |
| `gt-import.jsx` | Receipt/CSV upload and data preview |
| `gt-predict.jsx` | Purchase prediction tab |
| `gt-charts.jsx` | Chart component definitions |
| `gt-ui.jsx` | Shared UI components (cards, metrics, buttons) |
| `gt-data.js` | Data transformations — use for processing logic |
| `screenshots/` | Visual reference for each tab |

### Translation Rules (JSX → Streamlit)
- `st.tabs()` maps the top-level tab navigation in `gt-app.jsx`
- React component layout (rows/columns) → `st.columns()`
- Metric/KPI cards → `st.metric()`
- Chart components in `gt-charts.jsx` → `st.plotly_chart()` equivalents
- Sidebar filters defined in dashboard → `st.sidebar`
- `gt-ui.jsx` shared components → reusable functions in `components/`
- `tweaks-panel.jsx` is a design tool — do not implement in Streamlit

### What to Preserve
- Tab names and order from `gt-app.jsx`
- Chart types and data groupings from `gt-charts.jsx`
- KPI metrics and layout structure from `gt-dashboard.jsx`
- Upload flow and validation logic from `gt-import.jsx`

### Color & Theme
- Extract the color palette from `gt-ui.jsx` or `Grocery Tracker.html`
- Apply via `.streamlit/config.toml` (primaryColor, backgroundColor, etc.)

- `README.md` — Design documentation, read before starting implementation

## Project Structure
Organize code into these folders. Create them if they don't exist.

project-root/
├── app.py              ← Streamlit entry point: page config, global CSS, top nav, tab routing
├── components/         ← One file per tab (upload.py, dashboard.py, predict.py) + __init__.py
├── utils/              ← data.py: load/clean, aggregations, prediction, cross-reload store
├── scripts/            ← gen_sample_data.py: regenerates data/Purchase_data.csv
├── data/               ← Purchase_data.csv (the committed sample dataset)
├── design/             ← Prototype JSX files, screenshots, HANDOFF.md (read-only reference)
└── .streamlit/
    └── config.toml     ← Theme and configuration

`main.py` is the unused `uv init` stub — ignore it. Run the app with
`uv run streamlit run app.py`.


## Current State
Phase 1 is built and matches the prototype across all three tabs (Import,
Dashboard, Predict). The earlier UI/parity issues have been resolved.

## Data Flow
1. `app.py` bootstraps `st.session_state.df` once per session. Because the tab
   nav reloads the page (see gotchas), it restores a previously uploaded
   dataset from the cross-reload store *before* falling back to the sample.
2. `utils/data.py` is the single data layer:
   - `load_sample()` reads `data/Purchase_data.csv`; `load_upload(file)` parses
     an uploaded CSV (returns `(df, error)`); `_clean()` normalizes columns,
     coerces types, and sorts newest-first.
   - Aggregations: `filter_period`, `kpis`, `spend_by_category`,
     `repurchase_frequency`, `spend_over_time`.
   - `predict_next_week(df, horizon=7, min_items=10)` — avg-interval vs
     days-since heuristic. Keeps items due within `horizon`, but **tops up to
     at least `min_items`** with the next-soonest items when fewer qualify.
   - Cross-reload store: `remember/recall/forget` backed by
     `@st.cache_resource` — survives the full-page reloads that tab navigation
     triggers (single-user local app, so a shared store is intentional).
3. `CATEGORY_COLORS` only knows the prototype's 9 category names. Uploaded data
   with other category names falls back to gray (`#94a3b8`). If custom-category
   coloring is wanted, extend the palette or auto-assign colors.

## Sample Data
`data/Purchase_data.csv` (417 rows, Jan–May 2026, 9 categories) is generated by
`scripts/gen_sample_data.py` — a faithful Python port of the prototype's seeded
generator (`gt-data.js` mulberry32 + generateSample, seed `20260601`). It is
byte-faithful: the 90-day view reproduces the screenshots exactly ($1,758.84 /
25 trips / 33 items). **If the sample file is ever broken or changed, regenerate
it** with `uv run python scripts/gen_sample_data.py` (it prints validation KPIs).
The CSV has 6 columns (no `unit`); the loader only requires
date/store/item/category/quantity/price.

## Streamlit Rendering Gotchas (learned the hard way — keep in mind for edits)
- **Tab nav reloads the page.** Nav uses `<a href="?tab=...">` anchors, which
  Streamlit does NOT intercept — clicking reloads and clears `session_state`.
  That's why uploaded data is persisted via the cross-reload store. Don't assume
  `session_state` survives a tab switch.
- **`st.html()` sanitizes (DOMPurify).** It strips inline `<svg>`, `data:` URIs
  on `<a href>`, and `onclick` handlers. So: render icons as **base64 data-URI
  CSS backgrounds** (see `_nav_icon` in app.py and the leaf logo), and do real
  downloads with **`st.download_button`** (not a `data:` link).
- **HTML in `st.markdown` is markdown-parsed first.** Two recurring traps:
  - An opening tag whose attributes **span a newline** breaks HTML-block
    detection and leaks stray `</div>` as literal text. Keep tags single-line.
  - `display:flex` on a container makes **each loose text run and inline `<b>`
    a separate flex item** (odd gaps mid-sentence). Wrap row text in one
    `<span>`; the container should have only block-level flex children.
- **Raw `<table>` gets Streamlit's default table borders/padding** (looks like a
  boxed grid). Build list/legend layouts with **flex `<div>`s** instead (see the
  dashboard spend-by-category legend).
- **Fonts:** a global CSS override in `app.py` sets the prototype's system font
  stack (Segoe UI / `ui-sans-serif`) on the app containers; Plotly charts set
  `font=dict(family=_FONT)` in their layouts. Inline styles that need monospace
  keep their own family.
- **Bordered card full-bleed:** dividers inside `st.container(border=True)` don't
  perfectly reach the card's side borders (residual element-container padding).
  Known minor cosmetic limitation on the Import history table.