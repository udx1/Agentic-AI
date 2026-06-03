import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils import data as udata

# ── Inline SVG icons (from gt-ui.jsx) ────────────────────────────────
_SVG = {
    "cart":   '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/><path d="M2 3h2.2l2.3 12.2a1.5 1.5 0 0 0 1.5 1.2h8.8a1.5 1.5 0 0 0 1.5-1.2L21 7H5.5"/></svg>',
    "store":  '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9.5V20a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1V9.5"/><path d="M3 4h18l1 5a3 3 0 0 1-6 0 3 3 0 0 1-6 0 3 3 0 0 1-6 0z"/></svg>',
    "trend":  '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17l5-5 4 3 8-9"/><path d="M17 6h4v4"/></svg>',
    "list":   '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1" fill="{c}" stroke="none"/><circle cx="4.5" cy="12" r="1" fill="{c}" stroke="none"/><circle cx="4.5" cy="18" r="1" fill="{c}" stroke="none"/></svg>',
    "donut":  '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="3.2"/></svg>',
    "bars":   '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20V11M10 20V5M16 20V14M22 20H2"/></svg>',
    "trendg": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17l5-5 4 3 8-9"/><path d="M17 6h4v4"/></svg>',
}


def _icon(key: str, color: str = "currentColor") -> str:
    return _SVG.get(key, "").replace("{c}", color)


def _card_head(icon_key: str, title: str, sub: str = "", right: str = "") -> None:
    right_html = (
        f'<span style="font-size:11px;color:#9ca3af;font-weight:500;">{right}</span>'
        if right else ""
    )
    st.markdown(
        f"""<div style="display:flex;align-items:center;justify-content:space-between;
                padding:14px 18px 12px;border-bottom:1px solid #f3f4f6;">
          <div style="display:flex;align-items:center;gap:8px;">
            {_icon(icon_key)}
            <div>
              <div style="font-size:13px;font-weight:600;color:#1f2937;line-height:1.3;">{title}</div>
              {'<div style="font-size:11px;color:#9ca3af;margin-top:2px;">'+sub+'</div>' if sub else ''}
            </div>
          </div>
          {right_html}
        </div>""",
        unsafe_allow_html=True,
    )


def _kpi_card(label: str, value: str, sub: str, accent: bool = False) -> None:
    _icon_map = {
        "TOTAL SPEND": ("cart", "#16a34a", "#f0fdf4"),
        "SHOPPING TRIPS": ("store", "#9ca3af", "#f5f5f5"),
        "AVG. BASKET": ("trend", "#9ca3af", "#f5f5f5"),
        "ITEMS TRACKED": ("list", "#9ca3af", "#f5f5f5"),
    }
    icon_key, icon_color, icon_bg = _icon_map[label]
    svg = _icon(icon_key, icon_color)
    st.markdown(
        f"""<div style="border:1px solid #e5e7eb;border-radius:16px;padding:20px;background:white;height:100%;">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:12px;">
            <span style="font-size:11px;font-weight:700;text-transform:uppercase;
                         letter-spacing:0.06em;color:#9ca3af;">{label}</span>
            <span style="display:flex;width:32px;height:32px;align-items:center;
                         justify-content:center;border-radius:10px;background:{icon_bg};">{svg}</span>
          </div>
          <div style="font-size:26px;font-weight:700;color:#171717;line-height:1;">{value}</div>
          <div style="margin-top:8px;font-size:12px;color:#9ca3af;">{sub}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def _spend_donut(by_cat: pd.DataFrame, total: float) -> None:
    total_fmt = f"${total:,.2f}"

    fig = go.Figure(go.Pie(
        labels=by_cat["category"],
        values=by_cat["value"].round(2),
        hole=0.65,
        marker=dict(colors=by_cat["color"].tolist(), line=dict(color="white", width=2)),
        textinfo="none",
        hovertemplate="<b>%{label}</b><br>$%{value:,.2f} · %{percent}<extra></extra>",
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=8, b=8),
        height=240,
        showlegend=False,
        annotations=[
            dict(
                text="TOTAL SPEND",
                x=0.5, y=0.58,
                font=dict(size=10, color="#9ca3af", family="system-ui, Arial, sans-serif"),
                showarrow=False,
            ),
            dict(
                text=f"<b>{total_fmt}</b>",
                x=0.5, y=0.42,
                font=dict(size=17, color="#171717", family="system-ui, Arial, sans-serif"),
                showarrow=False,
            ),
        ],
        paper_bgcolor="white",
        plot_bgcolor="white",
    )

    cat_total = by_cat["value"].sum()
    legend_rows = "".join(
        f'<tr>'
        f'<td style="padding:5px 0;white-space:nowrap;">'
        f'<span style="display:inline-block;width:10px;height:10px;border-radius:2px;'
        f'background:{row["color"]};margin-right:6px;vertical-align:middle;"></span>'
        f'<span style="font-size:13px;color:#374151;">{row["category"]}</span></td>'
        f'<td style="padding:5px 0 5px 16px;text-align:right;font-size:13px;'
        f'font-weight:600;color:#111827;white-space:nowrap;">${row["value"]:,.2f}</td>'
        f'<td style="padding:5px 0 5px 8px;text-align:right;font-size:12px;color:#9ca3af;">'
        f'{row["value"]/cat_total*100:.0f}%</td>'
        f'</tr>'
        for _, row in by_cat.iterrows()
    )

    c_chart, c_legend = st.columns([2.2, 2.2])
    with c_chart:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with c_legend:
        st.markdown(
            f'<table style="width:100%;border-collapse:collapse;margin-top:16px;">'
            f'{legend_rows}</table>',
            unsafe_allow_html=True,
        )


def _freq_bars(freq: pd.DataFrame) -> None:
    df_plot = freq.iloc[::-1].reset_index(drop=True)  # reverse: highest at top
    fig = go.Figure(go.Bar(
        y=df_plot["item"],
        x=df_plot["count"],
        orientation="h",
        marker=dict(color=df_plot["color"].tolist(), opacity=0.88),
        text=df_plot["count"],
        textposition="outside",
        textfont=dict(size=12, color="#9ca3af"),
        hovertemplate="<b>%{y}</b>: %{x}<extra></extra>",
        cliponaxis=False,
    ))
    fig.update_layout(
        margin=dict(l=0, r=36, t=8, b=8),
        height=280,
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[0, df_plot["count"].max() * 1.18]),
        yaxis=dict(tickfont=dict(size=12, color="#4b5563"), showgrid=False, automargin=True),
        bargap=0.38,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _trend_area(trend: pd.DataFrame) -> None:
    fig = go.Figure(go.Scatter(
        x=trend["week"],
        y=trend["total"].round(2),
        fill="tozeroy",
        line=dict(color="#16a34a", width=2.5),
        fillcolor="rgba(22, 163, 74, 0.09)",
        mode="lines",
        hovertemplate="<b>%{x|%b %d}</b><br>$%{y:,.2f}<extra></extra>",
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        height=200,
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=11, color="#9ca3af"),
            tickformat="%b %d",
            tickangle=0,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f3f4f6",
            tickfont=dict(size=11, color="#9ca3af"),
            tickprefix="$",
            tickformat=",.0f",
            zeroline=False,
        ),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _empty_card(msg: str = "No data in this period.") -> None:
    st.markdown(
        f'<div style="height:160px;display:flex;align-items:center;'
        f'justify-content:center;color:#9ca3af;font-size:14px;">{msg}</div>',
        unsafe_allow_html=True,
    )


def render(df: pd.DataFrame | None = None) -> None:
    # Ensure data exists (guard for direct tab navigation)
    if df is None:
        df = st.session_state.get("df")
    if df is None:
        from utils.data import load_sample
        st.session_state.df = load_sample()
        st.session_state.source = "sample"
        df = st.session_state.df

    # ── Header + period toggle ────────────────────────────────────────
    col_h, col_p = st.columns([3, 1.4])
    with col_h:
        st.markdown(
            '<h1 style="font-size:24px;font-weight:700;color:#171717;margin:0 0 4px 0;'
            'letter-spacing:-0.3px;">Dashboard</h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="font-size:14px;color:#6b7280;margin:0 0 12px;">Where your grocery money '
            'goes and what you buy most often.</p>',
            unsafe_allow_html=True,
        )
    with col_p:
        st.write("")
        period_label = st.segmented_control(
            "Period",
            options=["30 days", "90 days", "All time"],
            default="90 days",
            key="dashboard_period",
            label_visibility="collapsed",
        )
        if period_label is None:
            period_label = "90 days"

    period_val = {"30 days": 30, "90 days": 90, "All time": "all"}[period_label]
    view = udata.filter_period(df, period_val)

    if view.empty:
        st.info("No data in this period.")
        return

    k = udata.kpis(view)
    by_cat = udata.spend_by_category(view)
    freq = udata.repurchase_frequency(view, 8)
    trend = udata.spend_over_time(view)

    # ── KPI row ───────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        _kpi_card("TOTAL SPEND", f"${k['total']:,.2f}",
                  f"{k['units']} items across {k['trips']} trips", accent=True)
    with c2:
        _kpi_card("SHOPPING TRIPS", str(k['trips']), "distinct store visits")
    with c3:
        _kpi_card("AVG. BASKET", f"${k['avg_basket']:,.2f}", "spend per trip")
    with c4:
        _kpi_card("ITEMS TRACKED", str(k['items']), "unique products")

    # ── Charts: donut + frequency bars ───────────────────────────────
    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    col_cat, col_freq = st.columns([3, 2], gap="medium")

    with col_cat:
        with st.container(border=True):
            _card_head("donut", "Spend by category", "share of total grocery spend")
            if by_cat.empty:
                _empty_card()
            else:
                _spend_donut(by_cat, k["total"])

    with col_freq:
        top_item = freq.iloc[0]["item"] if not freq.empty else ""
        sub = f"most bought: {top_item}" if top_item else "how often items are bought"
        with st.container(border=True):
            _card_head("bars", "Repurchase frequency", sub)
            if freq.empty:
                _empty_card()
            else:
                _freq_bars(freq)

    # ── Trend area ────────────────────────────────────────────────────
    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        _card_head(
            "trendg", "Spend over time", "weekly totals",
            right=f"{len(trend)} weeks" if not trend.empty else "",
        )
        if trend.empty:
            _empty_card()
        else:
            _trend_area(trend)
