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
3. **Purchase Prediction (stub)** — A placeholder prediction tab showing top recurring items by frequency. The repurchasing gives an idea of usage and consumption. Full ML forecasting is Phase 2.

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
├── app.py              ← Streamlit entry point, keep thin
├── components/         ← One file per tab (upload.py, dashboard.py, predict.py)
├── utils/              ← Data processing and helper functions
├── data/               ← Sample data files (not committed if large)
├── design/             ← Prototype JSX files and screenshots (read-only reference)
└── .streamlit/
    └── config.toml     ← Theme and configuration


## Current State
Initial app build is completed.
There are some UI issues, not matching with prototype.
Fixes are currently in progress.