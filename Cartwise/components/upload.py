import base64
import streamlit as st
from utils.data import load_sample, load_upload, summary, remember, forget

_CAT_COLORS = {
    "Produce":        "#16a34a",
    "Dairy & eggs":   "#eab308",
    "Dairy":          "#eab308",
    "Bakery":         "#d97706",
    "Meat & seafood": "#e2566b",
    "Meat":           "#e2566b",
    "Protein":        "#e2566b",
    "Pantry":         "#0d9488",
    "Beverages":      "#0ea5e9",
    "Snacks":         "#8b5cf6",
    "Frozen":         "#38bdf8",
    "Household":      "#64748b",
}

# ── SVG icons (from gt-ui.jsx) ────────────────────────────────────────
_ICON_CHECK = (
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
    'style="vertical-align:middle;margin-right:5px;flex-shrink:0;">'
    '<path d="M5 12.5l4.5 4.5L19 6.5"/></svg>'
)
_ICON_CALENDAR = (
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
    'style="vertical-align:middle;margin-right:5px;flex-shrink:0;">'
    '<rect x="3.5" y="4.5" width="17" height="16" rx="2.5"/>'
    '<path d="M3.5 9h17M8 3v3M16 3v3"/></svg>'
)
_ICON_UPLOAD_WHITE = (
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="white" '
    'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M12 15V4m0 0L8 8m4-4l4 4"/>'
    '<path d="M5 15v3a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-3"/></svg>'
)
_ICON_UPLOAD_GREEN = (
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#16a34a" '
    'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M12 15V4m0 0L8 8m4-4l4 4"/>'
    '<path d="M5 15v3a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-3"/></svg>'
)
_ICON_DOWNLOAD = (
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M12 4v11m0 0l-4-4m4 4l4-4"/>'
    '<path d="M5 18v1a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1"/></svg>'
)


def _dot(cat: str) -> str:
    color = _CAT_COLORS.get(cat, "#94a3b8")
    return (
        f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;'
        f'background:{color};margin-right:6px;vertical-align:middle;"></span>{cat}'
    )


def _fmt_date(dt) -> str:
    return f"{dt.strftime('%b')} {dt.day}"


def _init():
    if "df" not in st.session_state:
        st.session_state.df = load_sample()
        st.session_state.source = "sample"


def render():
    _init()

    # ── Tab-scoped CSS ────────────────────────────────────────────────
    st.markdown("""
    <style>
    /* Dropzone: hide Streamlit's default instructions and Browse button (redundant) */
    [data-testid="stFileUploaderDropzoneInstructions"] { display: none !important; }
    [data-testid="stFileUploaderDropzone"] button      { display: none !important; }
    /* Dropzone: size and center the overlay content */
    [data-testid="stFileUploaderDropzone"] {
        min-height: 190px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Header: title + Sample / Upload buttons ───────────────────────
    # Sample CSV is a real st.download_button: a data: URI <a> inside st.html()
    # gets stripped by the sanitizer, so the old link never actually downloaded.
    _sample_csv = load_sample().to_csv(index=False)

    _UP_B64 = base64.b64encode(
        b"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none'"
        b" stroke='white' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>"
        b"<path d='M12 15V4m0 0L8 8m4-4l4 4'/>"
        b"<path d='M5 15v3a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-3'/></svg>"
    ).decode()

    col_title, col_btns = st.columns([1.7, 1], vertical_alignment="bottom")
    with col_title:
        st.markdown(
            '<h1 style="font-size:24px;font-weight:700;color:#171717;letter-spacing:-0.3px;'
            'margin:0 0 5px;line-height:1.25;">Import purchases</h1>'
            '<p style="font-size:14px;color:#6b7280;margin:0 0 8px;line-height:1.5;">Upload a CSV '
            'of your grocery receipts. Everything is parsed in your browser&nbsp;&mdash; nothing '
            'leaves this page.</p>',
            unsafe_allow_html=True,
        )
    with col_btns:
        b_sample, b_upload = st.columns(2, gap="small")
        with b_sample:
            st.download_button(
                "Sample CSV",
                data=_sample_csv,
                file_name="grocery-purchases-sample.csv",
                mime="text/csv",
                icon=":material/download:",
                use_container_width=True,
            )
        with b_upload:
            # Visual parity with the prototype's green button. The click handler
            # opens the dropzone's file picker (best-effort; the dropzone below
            # is also directly clickable).
            st.html(
                f"""<style>
                  .btn-green {{
                    display:inline-flex; align-items:center; justify-content:center; width:100%;
                    background:#16a34a; color:white; border:none; border-radius:12px;
                    padding:9px 16px; font-size:14px; font-weight:600; cursor:pointer;
                    white-space:nowrap; line-height:1; box-shadow:0 1px 3px rgba(0,0,0,.15);
                    font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Arial,sans-serif;
                  }}
                  .btn-green::before {{
                    content:""; display:inline-block; width:15px; height:15px;
                    margin-right:7px; flex-shrink:0;
                    background:url("data:image/svg+xml;base64,{_UP_B64}") no-repeat center/contain;
                  }}
                  .btn-green:hover {{ background:#15803d; }}
                </style>
                <button class="btn-green"
                  onclick="try{{window.parent.document.querySelector('input[type=file]').click()}}catch(e){{}}">
                  Upload CSV
                </button>"""
            )

    # ── Dropzone visual overlay ───────────────────────────────────────
    # Only shown when no file is loaded; hides automatically after upload
    # so the file info chip shown by Streamlit's widget isn't obscured.
    # We read the uploader's widget state (populated before the script body
    # runs) rather than `source`, which is only updated *after* this point —
    # otherwise the overlay still renders on the rerun the file arrives and
    # overlaps the file chip.
    _has_upload = st.session_state.get("csv_uploader") is not None
    if not _has_upload and st.session_state.get("source", "sample") == "sample":
      st.markdown(
        f"""<div style="
            text-align:center;
            margin-bottom:-150px;
            position:relative;
            z-index:2;
            pointer-events:none;
            padding-top:28px;
        ">
          <span style="
              display:inline-flex;width:56px;height:56px;
              border-radius:50%;background:white;
              box-shadow:0 0 0 1px #e5e7eb;
              align-items:center;justify-content:center;
              margin-bottom:12px;
          ">{_ICON_UPLOAD_GREEN}</span>
          <p style="font-size:14px;font-weight:600;color:#374151;margin:0 0 4px;">
            Drag &amp; drop your CSV here
          </p>
          <p style="font-size:12px;color:#9ca3af;margin:0;">
            or click to browse &middot; columns: date, store, item, category, quantity, price
          </p>
        </div>""",
        unsafe_allow_html=True,
    )

    # Actual file_uploader (provides dashed border, drag-and-drop, Browse button)
    uploaded = st.file_uploader(
        "Drag & drop your CSV here",
        type=["csv"],
        label_visibility="collapsed",
        key="csv_uploader",
    )

    if uploaded is not None:
        # Only parse when this is a newly-selected file. The widget keeps the
        # same file across reruns; re-reading it each time is wasteful and can
        # fail once the buffer is consumed.
        file_id = f"{uploaded.name}:{getattr(uploaded, 'size', 0)}"
        if st.session_state.get("loaded_file_id") != file_id:
            df, err = load_upload(uploaded)
            if err:
                st.session_state["upload_error"] = err
            else:
                st.session_state.df = df
                st.session_state.source = uploaded.name
                st.session_state.import_limit = 40
                st.session_state.loaded_file_id = file_id
                st.session_state.pop("upload_error", None)
                remember(df, uploaded.name)  # survive tab-nav page reloads

        if st.session_state.get("upload_error"):
            st.markdown(
                f'<div style="margin-top:10px;padding:10px 16px;border-radius:10px;'
                f'background:#fef2f2;color:#b91c1c;font-size:14px;font-weight:500;'
                f'border:1px solid #fecaca;">✕  {st.session_state["upload_error"]}</div>',
                unsafe_allow_html=True,
            )

    df     = st.session_state.df
    source = st.session_state.source
    info   = summary(df)

    # ── Status chips (Gap 3 + 4) ───────────────────────────────────────
    def _fmt_chip_date(dt):
        return f"{dt.strftime('%b')} {dt.day}, {dt.year}"

    chip_text = (
        f"Sample data loaded · {info['rows']:,} rows"
        if source == "sample"
        else f"Imported · {info['rows']:,} rows"
    )
    date_str = f"{_fmt_chip_date(info['date_min'])} – {_fmt_chip_date(info['date_max'])}"

    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:8px;margin:14px 0 20px;flex-wrap:wrap;">
          <span style="
              display:inline-flex;align-items:center;
              background:#f0fdf4;color:#15803d;
              box-shadow:0 0 0 1px #bbf7d0;
              border-radius:9999px;padding:5px 12px;font-size:13px;font-weight:600;
          ">{_ICON_CHECK}{chip_text}</span>
          <span style="
              display:inline-flex;align-items:center;
              background:#f5f5f5;color:#6b7280;
              border-radius:9999px;padding:5px 12px;font-size:13px;
          ">{_ICON_CALENDAR}{date_str}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if source != "sample":
        if st.button("↩  Reset to sample data", type="secondary"):
            st.session_state.df = load_sample()
            st.session_state.source = "sample"
            # Clear the uploaded file so the dropzone overlay returns
            st.session_state.pop("csv_uploader", None)
            st.session_state.pop("loaded_file_id", None)
            st.session_state.pop("upload_error", None)
            st.session_state.import_limit = 40
            forget()  # drop the retained dataset from the cross-reload store
            st.rerun()

    # ── Purchase history card ──────────────────────────────────────────
    st.markdown("""
    <style>
    /* Card: rounded corners, prototype border, no internal gap */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px !important;
        border: 1px solid #e5e7eb !important;
        overflow: hidden;
    }
    [data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {
        padding: 0 !important;
        gap: 0 !important;
    }
    /* Table + divider rows must reach the card's side borders: kill the
       horizontal padding Streamlit puts on each element container. */
    [data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] {
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    /* Column gap inside the card header row */
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] {
        padding: 0 !important;
        gap: 8px !important;
        align-items: center !important;
    }
    /* Right column (search): add right-side padding + vertical centering */
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stColumn"]:last-child {
        padding-right: 16px !important;
        padding-top: 8px !important;
        padding-bottom: 4px !important;
    }
    /* Search input: magnifier icon */
    [data-testid="stTextInput"] input {
        background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%239ca3af' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><circle cx='11' cy='11' r='7'/><path d='M21 21l-4.2-4.2'/></svg>");
        background-repeat: no-repeat;
        background-position: 10px center;
        background-size: 14px 14px;
        padding-left: 32px !important;
        font-size: 13px !important;
        border-radius: 10px !important;
    }
    /* Row separators + hover (match prototype) */
    table tbody tr td { border-bottom: 1px solid #f5f5f5; }
    table tbody tr:hover { background-color: rgba(0,0,0,0.018); }
    /* "Show more": green text link button spanning the card footer */
    [data-testid="stVerticalBlockBorderWrapper"] .stButton button {
        background: transparent !important;
        border: none !important;
        color: #15803d !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] .stButton button:hover {
        background: #f0fdf4 !important;
        color: #166534 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    _ICON_LIST = (
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#16a34a" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
        'style="flex-shrink:0;">'
        '<path d="M9 6h11M9 12h11M9 18h11"/>'
        '<circle cx="4.5" cy="6" r="1" fill="#16a34a" stroke="none"/>'
        '<circle cx="4.5" cy="12" r="1" fill="#16a34a" stroke="none"/>'
        '<circle cx="4.5" cy="18" r="1" fill="#16a34a" stroke="none"/>'
        '</svg>'
    )

    # Search query (must come before filtering)
    query = ""
    with st.container(border=True):
        # Card header: list icon + title/count on left, search on right
        col_head, col_search = st.columns([3, 1])

        with col_search:
            query = st.text_input(
                "search",
                placeholder="Search items, stores…",
                label_visibility="collapsed",
            )

        # Apply filter before rendering header counts
        filtered = df.copy()
        if query.strip():
            q = query.lower()
            mask = (
                filtered["item"].str.lower().str.contains(q, na=False)
                | filtered["store"].str.lower().str.contains(q, na=False)
                | filtered["category"].str.lower().str.contains(q, na=False)
            )
            filtered = filtered[mask]

        with col_head:
            st.markdown(
                f'<div style="padding:14px 20px 10px;">'
                f'<div style="display:flex;align-items:center;gap:8px;">'
                f'{_ICON_LIST}'
                f'<div>'
                f'<p style="font-size:14px;font-weight:600;color:#111827;margin:0;line-height:1.3;">Purchase history</p>'
                f'<p style="font-size:12px;color:#9ca3af;margin:2px 0 0;">{len(filtered):,} of {len(df):,} rows</p>'
                f'</div></div></div>',
                unsafe_allow_html=True,
            )

        # Separator between card header and table
        st.markdown(
            '<div style="border-top:1px solid #f3f4f6;margin:0;"></div>',
            unsafe_allow_html=True,
        )

        # Pagination — show a page of rows + "Show more" (matches prototype,
        # which renders 40 rows at a time rather than one long scroll box).
        limit = st.session_state.get("import_limit", 40)
        page = filtered.iloc[:limit]

        # Table rows
        rows_html = ""
        for _, r in page.iterrows():
            date_s = _fmt_date(r["date"]) if hasattr(r["date"], "strftime") else str(r["date"])[:10]
            rows_html += (
                "<tr>"
                f'<td style="color:#6b7280;white-space:nowrap;padding:12px 20px;font-size:14px;">{date_s}</td>'
                f'<td style="color:#525252;padding:12px 20px;font-size:14px;">{r["store"]}</td>'
                f'<td style="font-weight:500;color:#262626;padding:12px 20px;font-size:14px;">{r["item"]}</td>'
                f'<td style="padding:12px 20px;font-size:14px;">{_dot(str(r["category"]))}</td>'
                f'<td style="text-align:right;color:#6b7280;padding:12px 20px;font-size:14px;font-variant-numeric:tabular-nums;">{int(r["quantity"])}</td>'
                f'<td style="text-align:right;font-weight:600;color:#111827;padding:12px 20px;font-size:14px;font-variant-numeric:tabular-nums;">${r["price"]:.2f}</td>'
                "</tr>"
            )

        # Header: DATE shows the active-sort state (green + chevron) like the
        # prototype; rows are pre-sorted newest-first in utils.data._clean.
        _chevron = (
            '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#15803d" '
            'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" '
            'style="vertical-align:middle;margin-left:3px;"><path d="M6 9l6 6 6-6"/></svg>'
        )
        _TH = ('padding:10px 20px;font-size:11px;font-weight:700;letter-spacing:.06em;'
               'text-transform:uppercase;white-space:nowrap;')
        header_html = (
            f'<th style="text-align:left;{_TH}color:#15803d;">Date{_chevron}</th>'
            f'<th style="text-align:left;{_TH}color:#9ca3af;">Store</th>'
            f'<th style="text-align:left;{_TH}color:#9ca3af;">Item</th>'
            f'<th style="text-align:left;{_TH}color:#9ca3af;">Category</th>'
            f'<th style="text-align:right;{_TH}color:#9ca3af;">Qty</th>'
            f'<th style="text-align:right;{_TH}color:#9ca3af;">Price</th>'
        )
        st.markdown(
            f"""<table style="width:100%;border-collapse:collapse;">
              <thead>
                <tr style="background:#fafafa;border-bottom:1px solid #f3f4f6;">
                  {header_html}
                </tr>
              </thead>
              <tbody>{rows_html}</tbody>
            </table>""",
            unsafe_allow_html=True,
        )

        # "Show 40 more" footer button when more rows remain
        remaining = len(filtered) - limit
        if remaining > 0:
            st.markdown(
                '<div style="border-top:1px solid #f3f4f6;"></div>',
                unsafe_allow_html=True,
            )
            if st.button(
                f"Show 40 more ({remaining} remaining)",
                key="import_show_more",
                use_container_width=True,
            ):
                st.session_state.import_limit = limit + 40
                st.rerun()
