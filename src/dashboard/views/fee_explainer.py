"""
Fee Explainer page — matching the Stitch UI / Improve UI Design layout.
All HTML built as complete strings in single st.markdown calls.
"""
import os
import json
import glob
import streamlit as st

PRIMARY = "#00b386"
ON_SURFACE = "#111827"
MUTED_FOREGROUND = "#6b7280"
BORDER = "rgba(0,0,0,0.07)"
SURFACE_TEXT = "#374151"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))


def _load_available_weeks() -> list[str]:
    pattern = os.path.join(PROJECT_ROOT, "data/outputs/fee_explainer_*.json")
    weeks = []
    for f in glob.glob(pattern):
        week_key = os.path.basename(f).replace("fee_explainer_", "").replace(".json", "")
        weeks.append(week_key)
    return sorted(weeks, reverse=True)


def _load_fee_data(iso_week: str) -> dict | None:
    path = os.path.join(PROJECT_ROOT, f"data/outputs/fee_explainer_{iso_week}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None


def render_fee_explainer():
    available_weeks = _load_available_weeks()

    if not available_weeks:
        st.markdown(
            f'<div style="text-align:center;padding:80px 40px;background:#fff;border-radius:12px;'
            f'border:1px solid {BORDER};margin-top:20px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
            f'<div style="font-size:64px;margin-bottom:16px;">💰</div>'
            f'<h3 style="font-family:Outfit,sans-serif;font-size:24px;font-weight:600;color:{ON_SURFACE};">No Fee Explainers Yet</h3>'
            f'<p style="font-family:Inter,sans-serif;font-size:14px;color:{MUTED_FOREGROUND};">Run the pipeline to generate fee explainer reports.</p>'
            f'</div>', unsafe_allow_html=True)
        return

    # Add week selector in sidebar if multiple weeks exist
    if len(available_weeks) > 1:
        selected_week = st.sidebar.selectbox("Select Week", available_weeks, key="fee_explainer_week_select")
    else:
        selected_week = available_weeks[0]

    fee_data = _load_fee_data(selected_week)

    if not fee_data:
        st.error(f"Could not load fee explainer data for week {selected_week}")
        return

    scenario = fee_data.get("scenario", "Fee Scenario")
    bullets = fee_data.get("bullets", [])
    sources = fee_data.get("sources", [])
    last_checked = fee_data.get("last_checked", "Unknown")

    # ── Header ──
    st.markdown(
        f'<div style="margin-bottom:32px;">'
        f'  <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
        f'    <h1 style="font-family:Outfit,sans-serif;font-size:22px;font-weight:600;color:{ON_SURFACE};'
        f'      letter-spacing:-0.02em;margin:0;">{scenario}</h1>'
        f'    <span style="background:#fff7ed;color:#c2410c;border:1px solid #fed7aa;font-family:Inter,sans-serif;'
        f'      font-size:11.5px;font-weight:600;padding:2px 12px;border-radius:999px;">'
        f'      Last checked: {last_checked}</span>'
        f'  </div>'
        f'  <p style="font-family:Inter,sans-serif;font-size:13px;color:{MUTED_FOREGROUND};margin-top:6px;margin-bottom:0;">'
        f'    Generated for week {selected_week} — Factual, neutral fee explanation for Groww users</p>'
        f'</div>',
        unsafe_allow_html=True)

    content_col, sidebar_col = st.columns([2, 1])

    with content_col:
        # Build bullets HTML
        bullets_html = ""
        for i, bullet in enumerate(bullets):
            bullets_html += (
                f'<div style="display:flex;gap:16px;align-items:flex-start;padding:16px;background:#f9fafb;'
                f'  border:1px solid {BORDER};border-radius:8px;margin-bottom:12px;">'
                f'  <div style="width:26px;height:26px;border-radius:50%;background:#f0faf6;flex-shrink:0;'
                f'    display:flex;align-items:center;justify-content:center;font-family:Inter,sans-serif;'
                f'    font-size:12px;font-weight:700;color:{PRIMARY};margin-top:1px;">{i+1}</div>'
                f'  <p style="font-family:Inter,sans-serif;font-size:13.5px;color:{SURFACE_TEXT};line-height:1.6;'
                f'    margin:0;">{bullet}</p>'
                f'</div>'
            )

        st.markdown(
            f'<div style="background:#fff;border:1px solid {BORDER};border-radius:12px;padding:24px;'
            f'  box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
            f'  <div style="display:flex;align-items:center;gap:8px;margin-bottom:20px;">'
            f'    <span style="color:{PRIMARY};font-size:16px;line-height:1;">📖</span>'
            f'    <h2 style="font-family:Outfit,sans-serif;font-size:15px;font-weight:600;color:{ON_SURFACE};margin:0;">'
            f'      Key Facts</h2>'
            f'  </div>'
            f'  <div style="display:flex;flex-direction:column;gap:4px;">'
            f'    {bullets_html}'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True)

    with sidebar_col:
        # Sources card
        sources_html = ""
        for source in sources:
            if isinstance(source, dict):
                s_name = source.get("name", "")
                s_url = source.get("url", "#")
            else:
                s_name = str(source)
                s_url = "#"

            sources_html += (
                f'<a href="{s_url}" target="_blank" style="display:flex;align-items:center;gap:8px;padding:10px 12px;background:#f9fafb;'
                f'  border:1px solid {BORDER};border-radius:8px;text-decoration:none;transition:all 0.15s ease;'
                f'  margin-bottom:8px;">'
                f'  <div style="width:6px;height:6px;border-radius:50%;background:{PRIMARY};flex-shrink:0;"></div>'
                f'  <span style="font-family:Inter,sans-serif;font-size:12.5px;color:{PRIMARY};font-weight:500;'
                f'    overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;">{s_name}</span>'
                f'  <span style="color:#9ca3af;font-size:11px;margin-left:auto;">↗</span>'
                f'</a>'
            )

        st.markdown(
            f'<div style="background:#fff;border:1px solid {BORDER};border-radius:12px;padding:20px;'
            f'  box-shadow:0 1px 3px rgba(0,0,0,0.04);margin-bottom:16px;">'
            f'  <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;">'
            f'    <span style="color:{PRIMARY};font-size:14px;line-height:1;">↗</span>'
            f'    <h3 style="font-family:Outfit,sans-serif;font-size:13.5px;font-weight:600;color:{ON_SURFACE};margin:0;">'
            f'      Official Sources</h3>'
            f'  </div>'
            f'  <div style="display:flex;flex-direction:column;gap:2px;">'
            f'    {sources_html}'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True)

        # Disclaimer
        st.markdown(
            f'<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:12px;padding:20px;'
            f'  margin-bottom:16px;">'
            f'  <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
            f'    <span style="color:#d97706;font-size:14px;line-height:1;">⚠</span>'
            f'    <span style="font-family:Inter,sans-serif;font-size:13px;font-weight:600;color:#92400e;'
            f'      text-transform:uppercase;letter-spacing:0.05em;">Disclaimer</span>'
            f'  </div>'
            f'  <p style="font-family:Inter,sans-serif;font-size:12px;color:#78350f;line-height:1.6;margin:0;">'
            f'    This is a factual summary only. It does not constitute financial advice. '
            f'    Always refer to the latest scheme documents and SEBI guidelines.</p>'
            f'</div>',
            unsafe_allow_html=True)

        # Report Info
        st.markdown(
            f'<div style="background:#fff;border:1px solid {BORDER};border-radius:12px;padding:20px;'
            f'  box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
            f'  <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;">'
            f'    <span style="color:{MUTED_FOREGROUND};font-size:14px;line-height:1;">ℹ</span>'
            f'    <h3 style="font-family:Outfit,sans-serif;font-size:13.5px;font-weight:600;color:{ON_SURFACE};margin:0;">'
            f'      Report Info</h3>'
            f'  </div>'
            f'  <div style="display:flex;flex-direction:column;gap:12px;">'
            f'    <div style="display:flex;justify-content:space-between;align-items:center;">'
            f'      <span style="font-family:Inter,sans-serif;font-size:11.5px;color:#9ca3af;font-weight:500;'
            f'        text-transform:uppercase;letter-spacing:0.04em;">ISO Week</span>'
            f'      <span style="font-family:monospace;font-size:13.5px;font-weight:700;color:{ON_SURFACE};">'
            f'        {selected_week}</span>'
            f'    </div>'
            f'    <div style="display:flex;justify-content:space-between;align-items:center;">'
            f'      <span style="font-family:Inter,sans-serif;font-size:11.5px;color:#9ca3af;font-weight:500;'
            f'        text-transform:uppercase;letter-spacing:0.04em;">Bullet Count</span>'
            f'      <span style="font-family:monospace;font-size:13.5px;font-weight:700;color:{ON_SURFACE};">'
            f'        {len(bullets)} / 6</span>'
            f'    </div>'
            f'    <div style="display:flex;justify-content:space-between;align-items:center;">'
            f'      <span style="font-family:Inter,sans-serif;font-size:11.5px;color:#9ca3af;font-weight:500;'
            f'        text-transform:uppercase;letter-spacing:0.04em;">Sources</span>'
            f'      <span style="font-family:monospace;font-size:13.5px;font-weight:700;color:{ON_SURFACE};">'
            f'        {len(sources)}</span>'
            f'    </div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True)
