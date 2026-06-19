"""
Theme distribution chart component.
Renders theme clusters as styled bars matching the Stitch UI reference.
All CSS is inline to avoid Streamlit stripping <style> blocks.
"""
import streamlit as st
import hashlib

PRIMARY = "#00b386"
MUTED_BG = "#f0f2f5"
BORDER = "rgba(0, 0, 0, 0.07)"
ON_SURFACE = "#111827"
MUTED_FOREGROUND = "#6b7280"
SURFACE_TEXT = "#374151"

COLOR_HIGH = "#ef4444"
COLOR_MED = "#00b386"
COLOR_LOW = "#3b82f6"


def render_theme_chart(themes: list[dict]):
    """Renders a styled theme clusters panel matching the Stitch UI."""
    if not themes:
        st.info("No theme data available for this week.")
        return

    sorted_themes = sorted(themes, key=lambda t: t["size"], reverse=True)
    max_size = sorted_themes[0]["size"] if sorted_themes else 1

    rows_html = ""
    for i, theme in enumerate(sorted_themes):
        label = theme["label"]
        size = theme["size"]
        width_pct = int((size / max_size) * 100)

        # Priority logic
        ratio = size / max_size
        if ratio >= 0.7:
            priority_label, priority_color = "high", COLOR_HIGH
        elif ratio >= 0.4:
            priority_label, priority_color = "medium", COLOR_MED
        else:
            priority_label, priority_color = "low", COLOR_LOW

        # Deterministic delta simulation
        h = int(hashlib.md5(label.encode()).hexdigest()[:4], 16)
        delta = (h % 31) - 15  # Range -15 to +15

        if delta > 0:
            delta_html = (
                f'<span style="display:inline-flex;align-items:center;gap:2px;color:#00b386;font-size:11px;font-weight:500;">'
                f'▲ {delta}</span>'
            )
        elif delta < 0:
            delta_html = (
                f'<span style="display:inline-flex;align-items:center;gap:2px;color:#ef4444;font-size:11px;font-weight:500;">'
                f'▼ {abs(delta)}</span>'
            )
        else:
            delta_html = (
                f'<span style="display:inline-flex;align-items:center;gap:2px;color:#6b7280;font-size:11px;font-weight:500;">'
                f'▬ 0</span>'
            )

        tag_html = ""
        if i < 3:
            tag_html = (
                f'<span style="margin-left:6px;background:#e0f2fe;color:#0284c7;font-size:8.5px;'
                f'font-weight:700;padding:1px 4px;border-radius:3px;text-transform:uppercase;'
                f'display:inline-block;vertical-align:middle;font-family:Inter,sans-serif;">TOP</span>'
            )

        rows_html += (
            f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">'
            f'  <div style="width:22px;height:22px;border-radius:4px;background:{MUTED_BG};'
            f'    display:flex;align-items:center;justify-content:center;font-family:Inter,sans-serif;'
            f'    font-size:11px;font-weight:600;color:{MUTED_FOREGROUND};flex-shrink:0;">'
            f'    {i + 1}</div>'
            f'  <div style="flex:1;min-width:0;">'
            f'    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
            f'      <span style="font-family:Inter,sans-serif;font-size:12.5px;font-weight:500;color:{SURFACE_TEXT};'
            f'        overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding-right:8px;">{label}{tag_html}</span>'
            f'      <span style="font-family:Inter,sans-serif;font-size:12.5px;font-weight:600;color:{ON_SURFACE};'
            f'        font-variant-numeric:tabular-nums;">{size:,}</span>'
            f'    </div>'
            f'    <div style="height:4px;background:{MUTED_BG};border-radius:999px;overflow:hidden;">'
            f'      <div style="height:100%;width:{width_pct}%;background:{priority_color};border-radius:999px;"></div>'
            f'    </div>'
            f'  </div>'
            f'  <div style="min-width:40px;text-align:right;flex-shrink:0;">'
            f'    {delta_html}'
            f'  </div>'
            f'</div>'
        )

    full_html = (
        f'<div style="background:#ffffff;border:1px solid {BORDER};border-radius:12px;padding:24px;'
        f'box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
        f'  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">'
        f'    <h3 style="font-family:Outfit,sans-serif;font-size:14px;font-weight:600;color:{ON_SURFACE};margin:0;">Theme Clusters</h3>'
        f'    <span style="font-family:Inter,sans-serif;font-size:11px;font-weight:600;background:{MUTED_BG};'
        f'      color:{MUTED_FOREGROUND};padding:2px 8px;border-radius:999px;text-transform:uppercase;">Top 5</span>'
        f'  </div>'
        f'  <div style="display:flex;flex-direction:column;gap:4px;">'
        f'    {rows_html}'
        f'  </div>'
        f'</div>'
    )

    st.markdown(full_html, unsafe_allow_html=True)
