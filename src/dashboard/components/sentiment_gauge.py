"""
Sentiment visualization component.
Renders a horizontal stacked bar matching the Stitch UI reference.
All styles are single-line inline to avoid Streamlit parsing issues.
"""
import streamlit as st

BRAND_MINT = "#00b386"
BRAND_ORANGE = "#f59e0b"
ERROR_RED = "#ef4444"
MUTED_BG = "#f3f4f6"
ON_SURFACE = "#111827"
MUTED_FOREGROUND = "#6b7280"
BORDER = "rgba(0, 0, 0, 0.07)"


def render_sentiment_bar(positive: int, negative: int, neutral: int):
    """Renders a horizontal stacked sentiment bar matching the Stitch UI."""
    total = positive + negative + neutral
    if total == 0:
        st.info("No sentiment data available.")
        return

    pos_pct = round(positive / total * 100)
    neg_pct = round(negative / total * 100)
    neu_pct = 100 - pos_pct - neg_pct

    html = (
        f'<div style="background:#ffffff;border:1px solid {BORDER};border-radius:12px;padding:24px;'
        f'box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
        f'<span style="font-family:Inter,sans-serif;font-size:11px;font-weight:600;text-transform:uppercase;'
        f'letter-spacing:0.06em;color:{MUTED_FOREGROUND};">Sentiment Analysis</span>'
        f'<div style="margin-top:24px;">'
        f'<div style="display:flex;height:16px;width:100%;border-radius:999px;overflow:hidden;background:{MUTED_BG};">'
        f'<div style="width:{pos_pct}%;background:{BRAND_MINT};height:100%;"></div>'
        f'<div style="width:{neu_pct}%;background:{BRAND_ORANGE};height:100%;"></div>'
        f'<div style="width:{neg_pct}%;background:{ERROR_RED};height:100%;"></div>'
        f'</div>'
        f'<div style="display:flex;justify-content:space-between;margin-top:16px;">'
        f'<div style="text-align:center;flex:1;">'
        f'<div style="font-family:Inter,sans-serif;font-size:11px;font-weight:500;text-transform:uppercase;color:{MUTED_FOREGROUND};">Pos</div>'
        f'<div style="font-family:Inter,sans-serif;font-size:14px;font-weight:700;color:{ON_SURFACE};">{pos_pct}%</div>'
        f'</div>'
        f'<div style="text-align:center;flex:1;border-left:1px solid {BORDER};border-right:1px solid {BORDER};padding:0 24px;">'
        f'<div style="font-family:Inter,sans-serif;font-size:11px;font-weight:500;text-transform:uppercase;color:{MUTED_FOREGROUND};">Neu</div>'
        f'<div style="font-family:Inter,sans-serif;font-size:14px;font-weight:700;color:{ON_SURFACE};">{neu_pct}%</div>'
        f'</div>'
        f'<div style="text-align:center;flex:1;">'
        f'<div style="font-family:Inter,sans-serif;font-size:11px;font-weight:500;text-transform:uppercase;color:{MUTED_FOREGROUND};">Neg</div>'
        f'<div style="font-family:Inter,sans-serif;font-size:14px;font-weight:700;color:{ON_SURFACE};">{neg_pct}%</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)
