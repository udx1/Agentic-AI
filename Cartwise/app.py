import base64
import streamlit as st
from components import upload, dashboard, predict

st.set_page_config(
    page_title="Cartwise",
    page_icon="🛒",
    layout="wide",
)

# ── Active tab from query params (default: dashboard) ─────────────────
_tab = st.query_params.get("tab", "dashboard")
if _tab not in ("import", "dashboard", "predict"):
    _tab = "dashboard"

# ── Bootstrap session data (safe to run on every tab) ─────────────────
# Tab links reload the page (clearing session_state), so restore any
# previously uploaded dataset from the cross-reload store first.
if "df" not in st.session_state:
    from utils.data import load_sample, recall
    _saved_df, _saved_source = recall()
    if _saved_df is not None:
        st.session_state.df = _saved_df
        st.session_state.source = _saved_source
    else:
        st.session_state.df = load_sample()
        st.session_state.source = "sample"

_source = st.session_state.get("source", "sample")
_dot_color = "#f59e0b" if _source == "sample" else "#16a34a"
_dot_label = "Sample data" if _source == "sample" else "Your data"

# ── Global CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Match the prototype's system font stack (Tailwind default sans) instead of
   Streamlit's Source Sans Pro. Unstyled inline HTML inherits from these
   containers; explicit monospace/plotly fonts keep their own family. */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"],
.stMarkdown, .stHeading, h1, h2, h3, h4, p, label, button, input, textarea {
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
}

/* Hide Streamlit chrome */
[data-testid="stHeader"]  { display: none !important; }
#MainMenu                 { visibility: hidden; }
footer                    { visibility: hidden; }
.stDeployButton           { display: none !important; }

/* Page body — remove ALL top spacing so nav bar sits flush */
.main .block-container,
.block-container,
[data-testid="stAppViewBlockContainer"],
[data-testid="stVerticalBlock"].block-container {
    padding-top: 0 !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 58rem;
}
/* Remove the gap Streamlit adds above the first element */
.main .block-container > div:first-child { margin-top: 0 !important; }

/* File uploader: styled dropzone */
[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed #d1d5db !important;
    border-radius: 16px !important;
    background: rgba(249, 250, 251, 0.6) !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #86efac !important;
    background: rgba(240, 253, 244, 0.4) !important;
    cursor: pointer;
}
[data-testid="stFileUploaderDropzone"] button {
    background: #16a34a !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    border: none !important;
    padding: 8px 18px !important;
}
[data-testid="stFileUploaderDropzone"] button:hover {
    background: #15803d !important;
}
[data-testid="stFileUploaderDropzone"] small { display: none !important; }

/* Metrics */
[data-testid="stMetricDelta"] { font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# ── SVG icon helpers ──────────────────────────────────────────────────
# Returned as a base64 data-URI (not inline SVG): st.html()'s sanitizer strips
# inline <svg>, so nav icons must ride in as a CSS background image.
def _nav_icon(key: str, color: str, size: int = 17) -> str:
    paths = {
        "upload": (
            '<path d="M12 15V4m0 0L8 8m4-4l4 4"/>'
            '<path d="M5 15v3a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-3"/>'
        ),
        "donut": (
            '<circle cx="12" cy="12" r="8.5"/>'
            '<circle cx="12" cy="12" r="3.2"/>'
        ),
        "cart": (
            '<circle cx="9" cy="20" r="1.4"/>'
            '<circle cx="18" cy="20" r="1.4"/>'
            '<path d="M2 3h2.2l2.3 12.2a1.5 1.5 0 0 0 1.5 1.2h8.8'
            'a1.5 1.5 0 0 0 1.5-1.2L21 7H5.5"/>'
        ),
        "leaf": (
            '<path d="M4 19c11 1.5 16-5 16-15C8 4 3 9 4 19z"/>'
            '<path d="M4 19C8 13 11 10 17 8"/>'
        ),
    }
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round">{paths.get(key, "")}</svg>'
    )
    b64 = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"


# ── Top navigation bar ────────────────────────────────────────────────
_NAV = [
    ("import",    "Import",    "upload"),
    ("dashboard", "Dashboard", "donut"),
    ("predict",   "Predict",   "cart"),
]

nav_links = ""
for tab_key, label, icon_key in _NAV:
    active = _tab == tab_key
    bg    = "#f0fdf4" if active else "transparent"
    color = "#15803d" if active else "#6b7280"
    icon_uri = _nav_icon(icon_key, color)
    nav_links += (
        f'<a href="?tab={tab_key}" target="_parent" style="'
        f'display:inline-flex;align-items:center;gap:7px;'
        f'background:{bg};color:{color};border-radius:12px;'
        f'padding:7px 16px;font-size:14px;font-weight:600;'
        f'text-decoration:none;white-space:nowrap;">'
        f'<span style="display:inline-block;width:17px;height:17px;flex-shrink:0;'
        f'background:url({icon_uri}) no-repeat center/contain;"></span>'
        f'{label}</a>'
    )

# Leaf icon as base64 SVG — same approach as button icons (avoids iframe sanitizer stripping inline SVG)
_leaf_b64 = base64.b64encode(
    b"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none'"
    b" stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
    b"<path d='M4 19c11 1.5 16-5 16-15C8 4 3 9 4 19z'/>"
    b"<path d='M4 19C8 13 11 10 17 8'/></svg>"
).decode()

st.html(f"""
<style>
  body {{ margin:0; padding:0; overflow:hidden; }}
  .bar {{
    background:white; border-bottom:1px solid #e5e7eb;
    height:60px; display:flex; align-items:center;
    padding:0 24px; gap:24px; box-sizing:border-box; width:100%;
  }}
  .brand {{ display:flex; align-items:center; gap:10px; flex-shrink:0; }}
  .logo-box {{
    width:36px; height:36px; border-radius:10px;
    background: #16a34a url("data:image/svg+xml;base64,{_leaf_b64}") no-repeat center/20px 20px;
    flex-shrink:0;
  }}
  .brand-text .name {{ font-size:15px; font-weight:700; color:#111827; letter-spacing:-0.3px; }}
  .brand-text .sub  {{ font-size:11px; color:#9ca3af; }}
  .nav {{ display:flex; align-items:center; gap:2px; flex:1; padding-left:8px; }}
  .src {{ margin-left:auto; display:flex; align-items:center; gap:6px;
          font-size:12px; color:#9ca3af; flex-shrink:0; }}
  .dot {{ width:8px; height:8px; border-radius:50%; background:{_dot_color}; flex-shrink:0; }}
</style>
<div class="bar">
  <div class="brand">
    <div class="logo-box"></div>
    <div class="brand-text">
      <div class="name">Cartwise</div>
      <div class="sub">grocery tracker</div>
    </div>
  </div>
  <nav class="nav">{nav_links}</nav>
  <div class="src"><div class="dot"></div>{_dot_label}</div>
</div>
""")

# ── Tab content ───────────────────────────────────────────────────────
st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

if _tab == "import":
    upload.render()
elif _tab == "predict":
    predict.render(df=st.session_state.get("df"))
else:
    dashboard.render(df=st.session_state.get("df"))
