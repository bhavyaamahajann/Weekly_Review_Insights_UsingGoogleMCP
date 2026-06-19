"""
Weekly Pulse page — matching the Stitch UI / Improve UI Design layout exactly.
All HTML is built as complete strings before rendering.
"""
import os
import json
import glob
import streamlit as st
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.dashboard.components.theme_chart import render_theme_chart
from src.dashboard.components.quote_card import render_quote_cards
from src.dashboard.components.sentiment_gauge import render_sentiment_bar

ON_SURFACE = "#111827"
MUTED_FOREGROUND = "#6b7280"
BORDER = "rgba(0, 0, 0, 0.07)"
SURFACE_TEXT = "#374151"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))


def _load_available_weeks() -> list[str]:
    pattern = os.path.join(PROJECT_ROOT, "data/outputs/pulse_*.json")
    weeks = []
    for f in glob.glob(pattern):
        week_key = os.path.basename(f).replace("pulse_", "").replace(".json", "")
        weeks.append(week_key)
    return sorted(weeks, reverse=True)


def _load_json(path: str):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None


def _get_week_date_range(iso_week: str) -> str:
    try:
        year, week_num = iso_week.split("-W")
        year, week_num = int(year), int(week_num)
        from datetime import date, timedelta
        jan4 = date(year, 1, 4)
        start = jan4 - timedelta(days=jan4.weekday()) + timedelta(weeks=week_num - 1)
        end = start + timedelta(days=6)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return f"{months[start.month-1]} {start.day} – {months[end.month-1]} {end.day}, {year}"
    except Exception:
        return iso_week


def render_weekly_pulse():
    available_weeks = _load_available_weeks()

    if not available_weeks:
        st.markdown(
            f'<div style="text-align:center;padding:80px 40px;background:#fff;border-radius:12px;'
            f'border:1px solid {BORDER};margin-top:20px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
            f'<div style="font-size:64px;margin-bottom:16px;">📊</div>'
            f'<h3 style="font-family:Outfit,sans-serif;font-size:24px;font-weight:600;color:{ON_SURFACE};">No Pulse Reports Yet</h3>'
            f'<p style="font-family:Inter,sans-serif;font-size:14px;color:{MUTED_FOREGROUND};">Run the pipeline to generate your first report.</p>'
            f'</div>', unsafe_allow_html=True)
        return

    # Add week selector in sidebar if multiple weeks exist
    if len(available_weeks) > 1:
        selected_week = st.sidebar.selectbox("Select Week", available_weeks, key="weekly_pulse_week_select")
    else:
        selected_week = available_weeks[0]

    pulse_data = _load_json(os.path.join(PROJECT_ROOT, f"data/outputs/pulse_{selected_week}.json"))
    themes_data = _load_json(os.path.join(PROJECT_ROOT, f"data/cleaned/themes_metadata_{selected_week}.json"))
    if not themes_data:
        themes_data = _load_json(os.path.join(PROJECT_ROOT, "data/cleaned/themes_metadata.json"))
    quotes_data = _load_json(os.path.join(PROJECT_ROOT, f"data/cleaned/quotes_{selected_week}.json"))
    if not quotes_data:
        quotes_data = _load_json(os.path.join(PROJECT_ROOT, "data/cleaned/quotes.json"))

    if not pulse_data:
        st.error(f"Could not load pulse data for week {selected_week}")
        return

    sentiment = pulse_data.get("sentiment", {"positive": 0, "negative": 0, "neutral": 0})
    summary = pulse_data.get("weekly_summary", "No summary available.")
    action_ideas = pulse_data.get("action_ideas", [])
    themes = themes_data.get("themes", []) if themes_data else []
    total_reviews = sum(t["size"] for t in themes) if themes else 0
    date_range = _get_week_date_range(selected_week)

    # ── Page Header ──
    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:32px;flex-wrap:wrap;gap:16px;">'
        f'  <div>'
        f'    <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
        f'      <h1 style="font-family:Outfit,sans-serif;font-size:22px;font-weight:600;color:{ON_SURFACE};'
        f'        letter-spacing:-0.02em;margin:0;">Weekly review — {selected_week}</h1>'
        f'      <span style="background:#f0faf6;color:#00b386;font-family:Inter,sans-serif;font-size:12px;'
        f'        font-weight:500;padding:2px 12px;border-radius:999px;display:inline-flex;align-items:center;gap:4px;">'
        f'        ✔ Completed</span>'
        f'    </div>'
        f'  </div>'
        f'  <div style="display:flex;align-items:center;gap:8px;background:#fff;border:1px solid {BORDER};'
        f'    padding:8px 12px;border-radius:8px;font-size:12.5px;color:{MUTED_FOREGROUND};box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
        f'    📅 {date_range}'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True)

    # ── Top Stats Row ──
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f'<div style="background:#fff;border:1px solid {BORDER};border-radius:12px;padding:20px;'
            f'box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
            f'  <div style="font-family:Inter,sans-serif;font-size:11px;font-weight:600;color:#9ca3af;'
            f'    text-transform:uppercase;letter-spacing:0.06em;margin-bottom:10px;">Total Reviews</div>'
            f'  <div style="font-family:Outfit,sans-serif;font-size:42px;font-weight:700;color:{ON_SURFACE};'
            f'    letter-spacing:-0.03em;line-height:1;">{total_reviews:,}</div>'
            f'  <div style="display:flex;align-items:center;gap:4px;color:#00b386;font-family:Inter,sans-serif;'
            f'    font-size:12px;font-weight:500;margin-top:8px;">📈 Analyzed this week</div>'
            f'</div>',
            unsafe_allow_html=True)

    with col2:
        render_sentiment_bar(
            positive=sentiment.get("positive", 0),
            negative=sentiment.get("negative", 0),
            neutral=sentiment.get("neutral", 0))

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

    # ── Middle Row: Summary + Theme Clusters ──
    summary_col, themes_col = st.columns([2, 1])

    with summary_col:
        rec_html = ""
        if action_ideas:
            rec_html = (
                f'<div style="background:#fffbeb;border:1px solid #fde68a;padding:16px;border-radius:8px;'
                f'margin-top:20px;display:flex;align-items:flex-start;gap:8px;">'
                f'  <span style="color:#d97706;font-size:16px;line-height:1;margin-top:1px;">⚠</span>'
                f'  <div>'
                f'    <span style="font-family:Inter,sans-serif;font-size:12.5px;font-weight:600;color:#92400e;">'
                f'      Strategic Recommendation:</span> '
                f'    <span style="font-family:Inter,sans-serif;font-size:12.5px;color:#78350f;">'
                f'      {action_ideas[0]}</span>'
                f'  </div>'
                f'</div>'
            )

        st.markdown(
            f'<div style="background:#fff;border:1px solid {BORDER};border-radius:12px;padding:24px;'
            f'box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
            f'  <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;">'
            f'    <div style="width:4px;height:18px;background:#00b386;border-radius:999px;"></div>'
            f'    <h3 style="font-family:Outfit,sans-serif;font-size:14px;font-weight:600;color:{ON_SURFACE};margin:0;">'
            f'      Weekly Pulse Summary</h3>'
            f'  </div>'
            f'  <p style="font-family:Inter,sans-serif;font-size:13.5px;color:{SURFACE_TEXT};line-height:1.65;'
            f'    margin:0;">{summary}</p>'
            f'  {rec_html}'
            f'</div>',
            unsafe_allow_html=True)

    with themes_col:
        render_theme_chart(themes)

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

    # ── Bottom Row: Quotes + Action Recommendations ──
    quotes_col, actions_col = st.columns(2)

    with quotes_col:
        render_quote_cards(quotes_data or [])

    with actions_col:
        priority_colors = {
            "HIGH": {"text": "#ef4444", "bg": "#fef2f2"},
            "URGENT": {"text": "#ef4444", "bg": "#fef2f2"},
            "MED": {"text": "#f59e0b", "bg": "#fffbeb"},
            "LOW": {"text": "#6b7280", "bg": "#f9fafb"}
        }

        cards_html = ""
        for i, idea in enumerate(action_ideas):
            # Map priority
            if i == 0:
                p_label = "HIGH"
            elif i == 1:
                p_label = "MED"
            else:
                p_label = "LOW"

            p_cfg = priority_colors[p_label]

            cards_html += (
                f'<div style="background:#f9fafb;border:1px solid {BORDER};border-radius:8px;'
                f'  padding:12px 16px;display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">'
                f'  <p style="font-family:Inter,sans-serif;font-size:12.5px;color:{SURFACE_TEXT};'
                f'    line-height:1.55;margin:0;flex:1;">{idea}</p>'
                f'  <span style="background:{p_cfg["bg"]};color:{p_cfg["text"]};font-family:Inter,sans-serif;'
                f'    font-size:10.5px;font-weight:700;padding:2px 8px;border-radius:999px;flex-shrink:0;'
                f'    margin-top:1px;">{p_label}</span>'
                f'</div>'
            )

        st.markdown(
            f'<div style="background:#fff;border:1px solid {BORDER};border-radius:12px;padding:24px;'
            f'  box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
            f'  <h3 style="font-family:Outfit,sans-serif;font-size:14px;font-weight:600;'
            f'    color:{ON_SURFACE};margin:0 0 16px 0;">Action Recommendations</h3>'
            f'  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
            f'    <span style="font-family:Inter,sans-serif;font-size:11px;font-weight:600;color:#9ca3af;'
            f'      text-transform:uppercase;letter-spacing:0.06em;">Action Item</span>'
            f'    <span style="font-family:Inter,sans-serif;font-size:11px;font-weight:600;color:#9ca3af;'
            f'      text-transform:uppercase;letter-spacing:0.06em;">Priority</span>'
            f'  </div>'
            f'  <div style="display:flex;flex-direction:column;gap:8px;">'
            f'    {cards_html}'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True)

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:#fff;border:1px solid {BORDER};border-radius:12px;padding:24px;'
        f'box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
        f'  <div style="font-family:Inter,sans-serif;font-size:11px;font-weight:600;color:#9ca3af;'
        f'    text-transform:uppercase;letter-spacing:0.06em;margin-bottom:10px;">Processing Pipeline</div>'
        f'  <div style="font-family:Outfit,sans-serif;font-size:42px;font-weight:700;color:{ON_SURFACE};'
        f'    letter-spacing:-0.03em;line-height:1;">{len(themes)}</div>'
        f'  <div style="font-family:Inter,sans-serif;font-size:12px;color:{MUTED_FOREGROUND};margin-top:6px;">'
        f'    Theme clusters identified & monitored</div>'
        f'  <div style="display:flex;align-items:center;gap:4px;color:#00b386;font-family:Inter,sans-serif;'
        f'    font-size:11px;font-weight:500;margin-top:8px;">✔ Pipeline complete</div>'
        f'</div>',
        unsafe_allow_html=True)
