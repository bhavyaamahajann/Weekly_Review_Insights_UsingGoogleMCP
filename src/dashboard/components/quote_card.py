"""
Quote display card component.
Builds complete HTML in a single call to avoid Streamlit tag auto-closing.
"""
import streamlit as st
import hashlib

ON_SURFACE = "#111827"
MUTED_FOREGROUND = "#6b7280"
BORDER = "rgba(0, 0, 0, 0.07)"

STYLES = {
    "positive": {
        "avatar_bg": "#f0faf6",
        "avatar_color": "#00b386",
        "tag_bg": "#f0faf6",
        "tag_color": "#00b386",
        "tag_label": "POSITIVE"
    },
    "negative": {
        "avatar_bg": "#fef2f2",
        "avatar_color": "#ef4444",
        "tag_bg": "#fef2f2",
        "tag_color": "#ef4444",
        "tag_label": "CRITICAL"
    },
    "neutral": {
        "avatar_bg": "#fffbeb",
        "avatar_color": "#f59e0b",
        "tag_bg": "#fffbeb",
        "tag_color": "#f59e0b",
        "tag_label": "NEUTRAL"
    }
}


def _generate_display(review_id: str) -> tuple:
    """Generates consistent initials and name from a review ID."""
    h = hashlib.md5(review_id.encode()).hexdigest()
    first_names = ["Ankit", "Rahul", "Priya", "Sneha", "Vikram",
                   "Neha", "Rohan", "Aarti", "Kiran", "Meera"]
    last_names = ["S.", "K.", "M.", "R.", "P.", "D.", "G.", "T.", "B.", "L."]
    idx = int(h[:4], 16)
    name = first_names[idx % len(first_names)]
    last = last_names[(idx >> 4) % len(last_names)]
    initials = f"{name[0]}{last[0]}"
    return initials, f"{name} {last}"


def _detect_sentiment(quote: str, theme: str) -> str:
    """Simple sentiment heuristic."""
    text = (quote + " " + theme).lower()
    neg = ["unable", "worst", "bad", "poor", "crash", "freeze", "slow",
           "issue", "problem", "scam", "hate", "terrible", "not", "loss", "frustration", "frustrated"]
    pos = ["good", "great", "love", "excellent", "best", "amazing",
           "wonderful", "helpful", "easy", "nice", "smooth", "clean", "praise", "praised"]
    n = sum(1 for kw in neg if kw in text)
    p = sum(1 for kw in pos if kw in text)
    if n > p:
        return "negative"
    elif p > n:
        return "positive"
    return "neutral"


def render_quote_cards(quotes: list[dict]):
    """Renders all quote cards in a single complete HTML block."""
    if not quotes:
        st.info("No verbatim quotes available for this week.")
        return

    cards_html = ""
    for q in quotes:
        theme = q.get("theme", "Unknown")
        quote = q.get("quote", "")
        rid = q.get("source_review_id", "unknown")
        sentiment = _detect_sentiment(quote, theme)
        cfg = STYLES[sentiment]
        initials, display_name = _generate_display(rid)

        cards_html += (
            f'<div style="display:flex;gap:12px;margin-bottom:16px;">'
            f'  <div style="width:34px;height:34px;border-radius:50%;background:{cfg["avatar_bg"]};'
            f'    flex-shrink:0;display:flex;align-items:center;justify-content:center;'
            f'    font-family:Inter,sans-serif;font-weight:700;font-size:11.5px;color:{cfg["avatar_color"]};">'
            f'    {initials}</div>'
            f'  <div style="flex:1;min-width:0;">'
            f'    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;flex-wrap:wrap;">'
            f'      <span style="font-family:Inter,sans-serif;font-weight:600;font-size:12.5px;'
            f'        color:{ON_SURFACE};">{display_name}</span>'
            f'      <span style="background:{cfg["tag_bg"]};color:{cfg["tag_color"]};font-family:Inter,sans-serif;'
            f'        font-size:10.5px;padding:2px 8px;border-radius:999px;font-weight:600;">'
            f'        {cfg["tag_label"]}</span>'
            f'    </div>'
            f'    <p style="font-family:Inter,sans-serif;font-size:12.5px;color:{MUTED_FOREGROUND};'
            f'      line-height:1.55;margin:0;">"{quote}"</p>'
            f'  </div>'
            f'</div>'
        )

    full_html = (
        f'<div style="background:#ffffff;border:1px solid {BORDER};'
        f'border-radius:12px;padding:24px;'
        f'box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
        f'<h3 style="font-family:Outfit,sans-serif;font-size:14px;font-weight:600;'
        f'color:{ON_SURFACE};margin:0 0 16px 0;">Representative Feedback</h3>'
        f'<div style="display:flex;flex-direction:column;gap:4px;">'
        f'{cards_html}'
        f'</div>'
        f'</div>'
    )

    st.markdown(full_html, unsafe_allow_html=True)
