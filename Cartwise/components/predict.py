import streamlit as st
import pandas as pd
from utils import data as udata

_CLOCK = (
    '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" '
    'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
    'style="vertical-align:middle;margin-right:3px;">'
    '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/></svg>'
)
_SPARKLE = (
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#16a34a" '
    'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
    'style="vertical-align:middle;">'
    '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/></svg>'
)
_CART = (
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#16a34a" '
    'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
    'style="vertical-align:middle;">'
    '<circle cx="9" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/>'
    '<path d="M2 3h2.2l2.3 12.2a1.5 1.5 0 0 0 1.5 1.2h8.8a1.5 1.5 0 0 0 1.5-1.2L21 7H5.5"/></svg>'
)


def _freq_label(interval: int) -> str:
    if interval <= 13:
        return f"every {interval} days"
    return f"every {round(interval / 7)} wks"


def _status_badge(due_in: int) -> str:
    if due_in <= 0:
        text, bg, fg = "due now", "#f0fdf4", "#15803d"
    elif due_in == 1:
        text, bg, fg = "due tomorrow", "#f0fdf4", "#15803d"
    else:
        text, bg, fg = f"in {due_in} days", "#f5f5f5", "#6b7280"
    return (
        f'<span style="font-size:10px;font-weight:600;font-family:ui-monospace,monospace;'
        f'background:{bg};color:{fg};border-radius:6px;padding:2px 7px;">{text}</span>'
    )


def _init_predict_state(items: list, df_fp: str) -> None:
    """Set session state defaults for checkboxes + quantities when data changes."""
    for it in items:
        st.session_state[f"chk_{it['item']}"] = it["due_in"] <= 2
        st.session_state[f"qty_{it['item']}"] = it["qty"]
    st.session_state["predict_df_fp"] = df_fp


def render(df: pd.DataFrame | None = None) -> None:
    # Ensure data exists
    if df is None:
        df = st.session_state.get("df")
    if df is None:
        from utils.data import load_sample
        st.session_state.df = load_sample()
        st.session_state.source = "sample"
        df = st.session_state.df

    pred = udata.predict_next_week(df)
    items = pred["items"]

    # Detect data change and (re)initialize state
    df_fp = f"{len(df)}_{str(df['date'].max())[:10]}"
    if st.session_state.get("predict_df_fp") != df_fp:
        _init_predict_state(items, df_fp)

    # ── Empty state ───────────────────────────────────────────────────
    if not items:
        st.markdown(
            f'<div style="text-align:center;padding:64px 0;">'
            f'<div style="display:inline-flex;width:56px;height:56px;border-radius:50%;'
            f'background:#f5f5f5;align-items:center;justify-content:center;'
            f'font-size:24px;margin-bottom:16px;">{_SPARKLE}</div>'
            f'<h2 style="font-size:18px;font-weight:600;color:#374151;margin:0 0 8px;">Not enough history yet</h2>'
            f'<p style="font-size:14px;color:#6b7280;max-width:380px;margin:0 auto;">We need at least a couple '
            f'of purchases per item to spot a pattern. Import more history to get predictions.</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Header ────────────────────────────────────────────────────────
    _next = df["date"].max() + pd.Timedelta(days=7)
    week_of = _next.strftime("%b") + " " + str(_next.day)

    col_h, col_btn = st.columns([3, 1])
    with col_h:
        st.markdown(
            '<h1 style="font-size:24px;font-weight:700;color:#171717;margin:0 0 4px 0;'
            'letter-spacing:-0.3px;">Predict next week</h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p style="font-size:14px;color:#6b7280;margin:0 0 16px;">Items you\'re likely to need '
            f'by the week of {week_of}, based on how often you usually buy them.</p>',
            unsafe_allow_html=True,
        )
    with col_btn:
        st.write("")
        st.write("")
        all_on = all(st.session_state.get(f"chk_{i['item']}", False) for i in items)
        if st.button("Clear all" if all_on else "Select all", use_container_width=True):
            for i in items:
                st.session_state[f"chk_{i['item']}"] = not all_on
            st.rerun()

    # ── Main layout: checklist | side rail ───────────────────────────
    col_list, col_rail = st.columns([2, 1], gap="medium")

    # Count selected for the header badge (read from current session_state)
    n_selected = sum(1 for i in items if st.session_state.get(f"chk_{i['item']}", False))

    with col_list:
        with st.container(border=True):
            # Card header
            st.markdown(
                f'<div style="display:flex;align-items:center;justify-content:space-between;'
                f'padding:14px 18px 12px;border-bottom:1px solid #f3f4f6;">'
                f'<div style="display:flex;align-items:center;gap:8px;">'
                f'{_CART}'
                f'<div>'
                f'<div style="font-size:13px;font-weight:600;color:#1f2937;">Predicted shopping list</div>'
                f'<div style="font-size:11px;color:#9ca3af;margin-top:2px;">{len(items)} items likely needed</div>'
                f'</div></div>'
                f'<span style="background:#f0fdf4;color:#15803d;border-radius:9999px;'
                f'padding:4px 12px;font-size:12px;font-weight:700;">{n_selected} selected</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Grouped checklist
            for group in pred["grouped"]:
                # Category header
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;'
                    f'margin:16px 18px 6px;">'
                    f'<span style="width:10px;height:10px;border-radius:50%;'
                    f'background:{group["color"]};display:inline-block;flex-shrink:0;"></span>'
                    f'<span style="font-size:11px;font-weight:700;text-transform:uppercase;'
                    f'letter-spacing:0.06em;color:#9ca3af;">{group["category"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                for it in group["items"]:
                    r_chk, r_info, r_qty, r_price = st.columns(
                        [0.45, 4.2, 1.4, 1.1], gap="small", vertical_alignment="center"
                    )
                    with r_chk:
                        st.checkbox(
                            label=it["item"],
                            key=f"chk_{it['item']}",
                            label_visibility="collapsed",
                        )
                    with r_info:
                        checked = st.session_state.get(f"chk_{it['item']}", False)
                        name_color = "#1f2937" if checked else "#9ca3af"
                        badge = _status_badge(it["due_in"])
                        st.markdown(
                            f'<div style="margin:2px 0 1px;">'
                            f'<span style="font-size:14px;font-weight:600;color:{name_color};">'
                            f'{it["item"]}</span> {badge}</div>'
                            f'<div style="font-size:11px;color:#9ca3af;">'
                            f'{_CLOCK}{_freq_label(it["interval"])} · last bought {it["days_since"]}d ago'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    with r_qty:
                        qty = st.number_input(
                            "qty",
                            min_value=1,
                            value=it["qty"],
                            key=f"qty_{it['item']}",
                            label_visibility="collapsed",
                            step=1,
                        )
                    with r_price:
                        unit_price = it["est_price"] / max(it["qty"], 1)
                        st.markdown(
                            f'<div style="text-align:right;font-size:14px;font-weight:600;'
                            f'color:#171717;">${unit_price * qty:.2f}</div>',
                            unsafe_allow_html=True,
                        )

                st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

    with col_rail:
        # ── Estimated total card ──────────────────────────────────────
        selected_items = [i for i in items if st.session_state.get(f"chk_{i['item']}", False)]
        sel_total = sum(
            (i["est_price"] / max(i["qty"], 1)) * st.session_state.get(f"qty_{i['item']}", i["qty"])
            for i in selected_items
        )

        st.markdown(
            f'<div style="border:1px solid #e5e7eb;border-radius:16px;overflow:hidden;margin-bottom:12px;">'
            f'<div style="background:#16a34a;padding:20px 20px 16px;">'
            f'<div style="font-size:11px;font-weight:500;text-transform:uppercase;'
            f'letter-spacing:0.06em;color:#bbf7d0;">Estimated total</div>'
            f'<div style="font-size:30px;font-weight:700;color:white;margin:4px 0 2px;'
            f'letter-spacing:-0.5px;">${sel_total:,.2f}</div>'
            f'<div style="font-size:13px;color:#bbf7d0;">{len(selected_items)} of {len(items)} items selected</div>'
            f'</div>'
            f'<div style="padding:14px;background:white;"></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Export button
        export_lines = _build_export(pred, selected_items, df, st.session_state)
        st.download_button(
            "Export shopping list",
            data=export_lines,
            file_name="shopping-list.txt",
            mime="text/plain",
            use_container_width=True,
            disabled=len(selected_items) == 0,
            icon=":material/download:",
        )

        st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

        # ── How we predicted card ─────────────────────────────────────
        with st.container(border=True):
            st.markdown(
                f'<div style="padding:16px 16px 4px;display:flex;align-items:center;gap:8px;">'
                f'{_SPARKLE}'
                f'<span style="font-size:13px;font-weight:600;color:#1f2937;">How we predicted</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            # Each row is two flex children — a dot + a single text span — so the
            # sentence flows normally. (A loose text node + <b> become separate
            # flex items, which is what made the text look broken.)
            _bullets = [
                ("We measure the ", "average days between purchases", " for each item."),
                ("Compared against ", "days since you last bought it", "."),
                ("Items due within ", "the next 7 days", " land on this list."),
            ]
            bullets_html = "".join(
                '<div style="display:flex;gap:10px;margin-bottom:10px;">'
                '<span style="margin-top:7px;width:6px;height:6px;border-radius:50%;'
                'background:#16a34a;flex-shrink:0;"></span>'
                f'<span style="font-size:13px;color:#6b7280;line-height:1.5;">{pre}'
                f'<b style="color:#374151;font-weight:600;">{bold}</b>{post}</span>'
                '</div>'
                for pre, bold, post in _bullets
            )
            st.markdown(
                f'<div style="margin:8px 16px 14px;">{bullets_html}</div>',
                unsafe_allow_html=True,
            )


def _build_export(pred: dict, selected_items: list, df: pd.DataFrame, ss) -> str:
    latest = df["date"].max()
    _nxt = latest + pd.Timedelta(days=7)
    week_str = _nxt.strftime("%B") + " " + str(_nxt.day)
    lines = [f"Shopping list — week of {week_str}", ""]
    sel_set = {i["item"] for i in selected_items}
    for g in pred["grouped"]:
        g_items = [i for i in g["items"] if i["item"] in sel_set]
        if not g_items:
            continue
        lines.append(g["category"].upper())
        for i in g_items:
            q = ss.get(f"qty_{i['item']}", i["qty"])
            unit_price = i["est_price"] / max(i["qty"], 1)
            price_str = f"~${unit_price * q:.2f}"
            lines.append(f"  [ ] {i['item']}  ×{q}   {price_str}")
        lines.append("")
    total = sum(
        (i["est_price"] / max(i["qty"], 1)) * ss.get(f"qty_{i['item']}", i["qty"])
        for i in selected_items
    )
    lines.append(f"Estimated total: ${total:,.2f}")
    return "\n".join(lines)
