# Handoff: Grocery Tracker & Planner ("Cartwise")

## Overview
A browser-based grocery spend tracker and shopping planner with three tabs:
1. **Import** — upload a CSV of purchases (parsed entirely client-side, no backend), view a searchable/sortable purchase-history table.
2. **Dashboard** — visualize spend with KPIs, a spend-by-category donut (the hero), a repurchase-frequency bar chart, and a weekly spend-trend area chart, all filterable by time period.
3. **Predict Next Week** — an auto-generated shopping checklist of items likely needed in the next 7 days, derived from each item's purchase frequency.

The app loads with realistic hardcoded sample data so every view is populated immediately.

## About the Design Files
The files in this bundle are **design references built in HTML/React (via in-browser Babel) + Tailwind (Play CDN) + Recharts (UMD)**. They are a working prototype demonstrating intended look, data model, and behavior — **not production code to ship as-is**.

The task is to **recreate this prototype in a real codebase** using a proper toolchain. Recommended target stack (matches the prototype's intent):
- **React 18 + Vite** (or Next.js) with real ES module imports
- **Tailwind CSS** installed via PostCSS/CLI (NOT the Play CDN)
- **Recharts** installed from npm
- **PapaParse** from npm for CSV parsing

If the team already has an established frontend environment, recreate the designs using its existing patterns and component library instead.

The prototype's `gt-data.js` (data model, sample-data generator, aggregations, prediction algorithm) is essentially framework-agnostic and can be ported almost verbatim into a real module — it is the most directly reusable file.

## Fidelity
**High-fidelity.** Final colors, typography, spacing, layout, and interactions are all specified. Recreate the UI faithfully. The one caveat: the prototype uses a couple of workarounds for CDN/in-browser quirks that you should NOT carry over (see "Implementation Gotchas" at the end) — with a real build, you can write idiomatic code instead.

---

## Design Tokens

### Colors
| Token | Hex | Usage |
|---|---|---|
| Primary green (brand) | `#16a34a` | logo, primary buttons, active accents, donut "Produce" slice, trend line |
| Green hover | `#15803d` / `green-700` | active nav text, primary button hover |
| Green tint (active bg) | `#f0fdf4` / `green-50` | active nav pill bg, "due" badges, selected pill |
| Ink (primary text) | `#171717` / `neutral-900` | headings |
| Body text | `#404040`–`#525252` / `neutral-600/700` | body, table cells |
| Muted text | `#9ca3af` / `neutral-400` | captions, axis labels |
| Page background | `#fafafa` / `neutral-50` | app background |
| Card background | `#ffffff` | all cards/panels |
| Border | `#e5e5e5` / `neutral-200` (≈80% opacity) | card borders, dividers |
| Amber dot | `#fbbf24` / `amber-400` | "Sample data" status indicator |
| Rose | `#e11d48` / rose-50/700 | upload error message |

### Category palette (donut, dots, bars) — keyed by category name
| Category | Hex |
|---|---|
| Produce | `#16a34a` |
| Dairy & eggs | `#eab308` |
| Bakery | `#d97706` |
| Meat & seafood | `#e2566b` |
| Pantry | `#0d9488` |
| Beverages | `#0ea5e9` |
| Snacks | `#8b5cf6` |
| Frozen | `#38bdf8` |
| Household | `#64748b` |
| (fallback / Uncategorized) | `#94a3b8` |

### Typography
- **Font family:** system UI sans stack — `ui-sans-serif, system-ui, -apple-system, "Segoe UI", "Helvetica Neue", Arial, sans-serif`. (No webfont. Helvetica-like.) Monospace for small "frequency" tags: `ui-monospace, SFMono-Regular, Menlo, monospace`.
- **Scale:**
  - Page H1: 24px / `text-2xl`, weight 700, tracking-tight
  - Card title: 14px / `text-sm`, weight 600
  - KPI value: 26px, weight 700
  - Body/table: 14px / `text-sm`
  - Captions, axis labels, sub-labels: 11–12px, `neutral-400`
  - Section/column labels: 11px, weight 700, uppercase, letter-spacing 0.06em

### Spacing / radius / shadow
- Card radius: 16px (`rounded-2xl`); buttons/inputs: 12px (`rounded-xl`); pills: full.
- Card padding: 20px body (`p-5`); header 16–20px.
- Grid gaps: 16px (`gap-4`).
- Card border: `1px solid neutral-200/80`. Subtle shadows only (`shadow-sm`); buttons use `shadow-sm`.
- Content max width: `max-w-6xl` (1152px), centered, with `px-5 py-8` page padding.

---

## Screens / Views

### Global shell
- **Top bar** (sticky, `z-20`, white, bottom border, height 64px): left = logo (green rounded square w/ leaf glyph) + "Cartwise" / "grocery tracker"; center-left = nav (3 buttons: Import, Dashboard, Predict — each icon + label, label hidden below `sm`); right = data-source indicator (amber dot + "Sample data", or green dot + "Your data" once a CSV is imported; hidden below `md`).
- **Active nav state:** background `#f0fdf4`, text `#15803d`. Inactive: text `#6b7280`, hover bg `neutral-100`.
- Main content area below, `px-5 py-8`.

### Tab 1 — Import
- **Header row:** H1 "Import purchases" + sub "Upload a CSV of your grocery receipts. Everything is parsed in your browser — nothing leaves this page." Right side: "Sample CSV" (outline button, download icon) and "Upload CSV" (green button, upload icon).
- **Dropzone:** large dashed-border rounded box (`border-2 border-dashed`, ~py-10). Centered: 56px circle with upload icon, "Drag & drop your CSV here", and sub "or click to browse · columns: date, store, item, category, quantity, price". Hover/drag-over: border + bg turn green (`green-500`/`green-50`), icon circle fills green. Clicking anywhere in the zone opens the file picker. On drop or selection: read file as text, parse, replace data.
- **Error state:** if not a `.csv` or no valid rows, show a rose-tinted message bar below the dropzone.
- **Status chips row:** green check chip "Sample data loaded · N rows" (or "Imported · N rows"), a calendar chip with the date range (e.g. "Jan 2, 2026 – May 29, 2026"). When data is user-imported, also show a "Reset to sample" pill (trash icon) that restores sample data.
- **Purchase history table** (card): header has list icon, "Purchase history", "N of M rows" sub, and a search input (magnifier icon) filtering by item/store/category. Columns: **Date, Store, Item, Category, Qty, Price**. Each column header is a sort toggle (click to sort; chevron indicates asc/desc; active column text green). Category cell shows a colored dot + name. Qty and Price right-aligned, tabular-nums; Price bold. Rows hover `neutral-50`. Paginated client-side: show 40 rows, "Show 40 more (X remaining)" button at the bottom.

### Tab 2 — Dashboard
- **Header row:** H1 "Dashboard" + sub "Where your grocery money goes and what you buy most often." Right: period toggle (segmented control: **30 days / 90 days / All time**, default 90). Active segment = white bg + `shadow-sm`.
- **KPI row** (4 cards, `grid-cols-2 lg:grid-cols-4`): each card has an uppercase label, a small icon chip top-right (first card's chip is green-tinted), a 26px bold value, and a small sub-line:
  - Total spend → `$X,XXX.XX`, sub "N items across M trips", cart icon (green chip)
  - Shopping trips → integer, sub "distinct store visits", store icon
  - Avg. basket → `$XX.XX`, sub "spend per trip", trend icon
  - Items tracked → integer, sub "unique products", list icon
- **Charts grid** (`lg:grid-cols-5`): 
  - **Spend by category** (col-span-3): donut icon header. Body = donut chart (innerRadius 68, outerRadius 104, 2° padding angle, slices colored by category palette) with a centered overlay reading "TOTAL SPEND" + the total. To the right, a legend list: colored square, category name, `$value`, and `%` of total. Donut is the visual hero.
  - **Repurchase frequency** (col-span-2): bars icon header, sub "most bought: <top item>". Horizontal bar chart, top 8 items by purchase count, bars colored by category, value label at the end of each bar. Y-axis = item names (width ~118px), X-axis = integer count.
- **Spend over time** (full-width card): trend icon header, "weekly totals", "N weeks" on the right. Area chart of weekly spend totals, green line (`#16a34a`, width 2.5) with a subtle vertical green gradient fill (0.22 → 0 opacity), no dots, X = week ("MMM D"), Y = `$` short format ("$1.2k").

### Tab 3 — Predict Next Week
- **Header row:** H1 "Predict next week" + sub "Items you're likely to need by the week of <date>, based on how often you usually buy them." Right: "Select all" / "Clear all" toggle button (check icon).
- **Layout:** `lg:grid-cols-3` — checklist spans 2, side rail spans 1.
- **Predicted shopping list** (card, col-span-2): header cart icon, "Predicted shopping list", "N items likely needed" sub, and a green pill "N selected" on the right. Body grouped by category: each group has a colored dot + uppercase category name, then item rows. **Item row:** checkbox (rounded square; checked = green fill + white check), item name (bold when checked, muted when not) with a sub-line "clock-icon · every N days · last bought Nd ago", a frequency/status badge ("due now" / "due tomorrow" / "in N days"; "due"-state badges are green, others gray; hidden below `sm`), a quantity stepper (− / value / +, min 1), and an estimated price (right-aligned, bold, updates with quantity).
- **Side rail:**
  - **Estimated total** card: green header band showing "ESTIMATED TOTAL", big `$X.XX` (sum of selected items × their qty), and "N of M items selected". Below, a dark "Export shopping list" button (download icon; disabled when nothing selected) — exports a `.txt` grouped list.
  - **How we predicted** card: sparkle icon title + 3 bullet points explaining the algorithm (avg days between purchases, vs. days since last bought, items due within the next N days).
- **Empty state:** if fewer than 2 purchases exist for any item (no patterns), show a centered empty state with a sparkle icon, "Not enough history yet", explanation, and a "Go to Import" button.

---

## Interactions & Behavior
- **Tab navigation:** clicking a nav button switches the active tab and re-skins the highlight. After a successful CSV import, auto-navigate to Dashboard.
- **CSV upload:** accept `.csv`; read via FileReader as text; parse with PapaParse (`header: true, skipEmptyLines: true`); map flexible header names (see HEADER_MAP in `gt-data.js`); normalize dates to `YYYY-MM-DD`, coerce quantity (≥1) and price (strip non-numeric). Replace the dataset; do not persist (fresh sample on every reload — per product decision).
- **Table:** live search filter; click-to-sort on every column (toggles desc→asc); "show more" pagination in 40-row increments.
- **Dashboard period filter:** filters all KPIs and charts to last 30 / 90 days (relative to the latest date in the data) or all time.
- **Predict checklist:** items due within 2 days are checked by default; checkboxes toggle; quantity steppers adjust per-item qty (min 1); estimated total recomputes live; "Select/Clear all"; export selected items to a downloadable text file.
- **Charts:** Recharts with tooltips. (In the prototype, chart entrance animation is disabled — see gotchas.)
- **Responsive:** grids collapse (`grid-cols-2`/`lg:grid-cols-4` etc.), nav labels hide below `sm`, donut + legend stack on narrow widths. Designed for `max-w-6xl`.

## State Management
Single top-level component (`App`) owns:
- `rows` — array of purchase records (init from `generateSample()`).
- `source` — `"sample"` or imported filename (drives the data-source indicator and "Reset to sample").
- `tab` — `"import" | "dashboard" | "predict"`.
- `period` — `30 | 90 | "all"`.
Predict screen owns local `checked` (map of item→bool) and `qty` (map of item→number), re-synced when `rows` or the prediction window change.
All derived data (KPIs, category spend, frequency, weekly trend, prediction) is computed with memoized selectors from `rows` — see `gt-data.js`. No data fetching; everything is client-side.

### Configurable parameters (exposed as "Tweaks" in the prototype; make these config/props/constants)
- `startTab` (default dashboard), `defaultPeriod` (default 90), `predictWindow` in days (default 7), `topItems` in the repurchase chart (default 8).

## The Prediction Algorithm (port from `gt-data.js` → `predictNextWeek`)
For each item with ≥2 purchases: sort its purchase dates, compute the **average gap (interval)** between consecutive purchases; find the **last purchase date** and **days since** (relative to the latest date in the dataset); `dueIn = interval − daysSince`. Include the item if `dueIn ≤ horizon` (default 7 days). Estimate quantity = median of past quantities; estimated price = average unit price × qty. Group results by category, sorting groups and items by `dueIn` ascending. `due now` when `dueIn ≤ 0`.

## Assets
- **No external image assets.** The logo and all icons are inline SVGs (simple geometric stroke icons — see `GIcon` in `gt-ui.jsx`, and the leaf/cart glyphs). Recreate with your icon library (e.g. lucide-react has equivalents: upload, download, pie/donut→`PieChart`, bar→`BarChart3`, list, check, search, leaf, shopping-cart, trash, calendar, trending-up, clock, chevron-down, store, x, sparkles).

## Files (all in the project root — modular source)
- `HANDOFF.md` — this spec.
- `Grocery Tracker.html` — entry point; loads libraries, Tailwind config, and mounts the app by importing the modules below.
- `gt-data.js` — **data model, sample-data generator, CSV parse/export, aggregations, prediction algorithm.** The most directly portable file — lift it almost verbatim into a real module.
- `gt-ui.jsx` — shared atoms: `GIcon` (inline-SVG icon set), `Card`, `CardHead`.
- `gt-charts.jsx` — Recharts components: `SpendDonut`, `RepurchaseBars`, `TrendArea`.
- `gt-import.jsx` — Import screen.
- `gt-dashboard.jsx` — Dashboard screen (KPIs, period toggle, chart layout).
- `gt-predict.jsx` — Predict Next Week screen (checklist + side rail).
- `gt-app.jsx` — app shell, top nav, state, and the tweakable config defaults (`startTab`, `defaultPeriod`, `predictWindow`, `topItems` — turn these into real config/props).
- `tweaks-panel.jsx` — prototype-only dev scaffolding; NOT needed in the real app.
- `screenshots/` — rendered reference images of each tab (dashboard, dashboard-charts, import, import-table, predict).

> Note: the `Grocery Tracker Wireframes.html` + `wf-*.jsx` files in the root are the earlier low-fi wireframes — kept for history, not part of this handoff.

## Implementation Gotchas (prototype workarounds you should NOT copy)
1. **Tailwind via Play CDN race:** the prototype drives the active-nav background with inline styles to dodge a Play-CDN class-toggling race. With a real Tailwind build, just use conditional utility classes (e.g. `clsx`) normally.
2. **Recharts animation disabled:** `isAnimationActive={false}` was set on bars/area to avoid a mount-measurement race in the CDN/iframe environment. With a real build inside a properly-sized container you can re-enable animations.
3. **`console.error` filter** for Recharts' `defaultProps` deprecation warning is a CDN-noise workaround — drop it; pin a Recharts version where it's resolved or ignore.
4. **In-browser Babel + window globals:** the prototype shares components via `window` because each `<script type="text/babel">` is isolated. In a real build, use proper ES `import`/`export`.
5. **Sample data** is generated with a seeded RNG for stable-but-varied output; keep it for demos/tests or replace with fixtures.
