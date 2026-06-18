"""
Groww Review Pulse Dashboard — Streamlit Entry Point
=====================================================
Refined to match the design style of the React application in Improve UI Design.
Sidebar: Weekly Pulse, Fee Explainer, Run History, Settings.
"""
import os
import sys
import requests
import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.dashboard.views.weekly_pulse import render_weekly_pulse
from src.dashboard.views.fee_explainer import render_fee_explainer
from src.dashboard.views.audit_history import render_audit_history

# ── Page Config ──
st.set_page_config(
    page_title="Groww Review Pulse Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

BRAND_MINT = "#00b386"
ON_SURFACE = "#111827"
MUTED_FOREGROUND = "#6b7280"
BORDER = "rgba(0, 0, 0, 0.07)"
SURFACE_TEXT = "#374151"

# ── Global CSS ──
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@400;500;600;700&display=swap');
    .stApp {{ background: #f5f6f8 !important; font-family: 'Inter', sans-serif !important; }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    header[data-testid="stHeader"] {{
        background: rgba(245, 246, 248, 0.8) !important;
        backdrop-filter: blur(12px);
    }}
    [data-testid="stSidebar"] {{
        background: #0f172a !important;
        border-right: 1px solid rgba(255,255,255,0.06) !important;
    }}
    [data-testid="stSidebar"] > div:first-child {{ padding-top: 24px !important; }}
    [data-testid="stSidebar"] .stRadio > div {{ gap: 4px !important; }}
    [data-testid="stSidebar"] .stRadio > div > label {{
        background: transparent !important;
        border-radius: 8px !important;
        padding: 10px 12px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 13.5px !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
        color: #cbd5e1 !important;
        border: none !important;
        outline: none !important;
        cursor: pointer !important;
    }}
    [data-testid="stSidebar"] .stRadio > div > label:hover {{
        background: #1e293b !important;
        color: #f1f5f9 !important;
    }}
    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"],
    [data-testid="stSidebar"] .stRadio > div > label[aria-checked="true"] {{
        background: #1e293b !important;
        color: #f1f5f9 !important;
        font-weight: 500 !important;
    }}
    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] svg,
    [data-testid="stSidebar"] .stRadio > div > label[aria-checked="true"] svg {{
        color: {BRAND_MINT} !important;
    }}
    .stButton > button {{
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 179, 134, 0.15) !important;
    }}
    .trigger-btn > button {{
        background: {BRAND_MINT} !important;
        color: white !important;
        border: none !important;
        padding: 10px 20px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    }}
    .trigger-btn > button:hover {{
        background: #00874f !important;
        box-shadow: 0 4px 12px rgba(0, 179, 134, 0.2) !important;
    }}
    .edit-schedule-btn > button {{
        background: #f9fafb !important;
        color: {SURFACE_TEXT} !important;
        border: 1px solid {BORDER} !important;
        padding: 10px 20px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }}
    .edit-schedule-btn > button:hover {{
        background: #f3f4f6 !important;
    }}
    .streamlit-expanderHeader {{
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        color: {ON_SURFACE} !important;
        border-radius: 8px !important;
    }}
    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 10px; }}
    h1, h2, h3, h4, h5, h6 {{ font-family: 'Outfit', sans-serif !important; }}
    .stSelectbox > div > div {{ border-radius: 8px !important; border-color: {BORDER} !important; }}
    .stAlert {{ border-radius: 8px !important; font-family: 'Inter', sans-serif !important; }}
    .block-container {{ padding-top: 2rem !important; padding-bottom: 2rem !important; max-width: 1200px !important; }}
</style>
""", unsafe_allow_html=True)


# ── Sidebar ──
with st.sidebar:
    # Groww Brand
    st.markdown(
        f'<div style="padding:4px 0 20px 4px;margin-bottom:8px;display:flex;align-items:center;gap:12px;">'
        f'  <div style="width:34px;height:34px;border-radius:8px;background:{BRAND_MINT};'
        f'    display:flex;align-items:center;justify-content:center;">'
        f'    <span style="color:white;font-size:16px;font-weight:700;">G</span></div>'
        f'  <span style="font-family:Inter,sans-serif;font-size:17px;font-weight:600;color:#f1f5f9;'
        f'    letter-spacing:-0.01em;">Groww</span>'
        f'</div>',
        unsafe_allow_html=True)

    # Navigation — matches React layout items
    page = st.radio(
        "Navigate",
        ["📊  Weekly Pulse", "💰  Fee Explainer", "📜  Run History", "⚙️  Settings"],
        label_visibility="collapsed",
    )

    # Profile & Collapse space
    st.markdown(
        f'<div style="position:fixed;bottom:16px;width:200px;">'
        f'  <div style="display:flex;align-items:center;gap:12px;padding:8px 8px;border-radius:8px;">'
        f'    <div style="width:30px;height:30px;border-radius:50%;background:#1e293b;display:flex;'
        f'      align-items:center;justify-content:center;font-size:14px;color:#94a3b8;">👤</div>'
        f'    <span style="font-family:Inter,sans-serif;font-size:12.5px;font-weight:500;color:#cbd5e1;">Profile</span>'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True)


# ── Page Router ──
if "Weekly Pulse" in page:
    render_weekly_pulse()

elif "Fee Explainer" in page:
    render_fee_explainer()

elif "Run History" in page:
    render_audit_history()

elif "Settings" in page:
    st.markdown(
        f'<div style="margin-bottom:32px;">'
        f'  <h1 style="font-family:Outfit,sans-serif;font-size:22px;font-weight:600;color:{ON_SURFACE};'
        f'    letter-spacing:-0.02em;margin:0;">Settings</h1>'
        f'  <p style="font-family:Inter,sans-serif;font-size:13px;color:{MUTED_FOREGROUND};margin-top:4px;margin-bottom:0;">'
        f'    Configure pipeline settings, notification preferences, and dashboard options.</p>'
        f'</div>',
        unsafe_allow_html=True)

    # ── Pipeline Trigger Card ──
    pipelineSteps = [
        "Fetch & clean latest Play Store reviews",
        "Generate embeddings and cluster into themes",
        "Create weekly pulse summary via Groq LLM",
        "Generate fee explainer",
        "Append to Google Doc and create Gmail draft",
    ]

    # Check if pipeline running in session state
    if "pipeline_running" not in st.session_state:
        st.session_state.pipeline_running = False

    steps_html = ""
    for i, step in enumerate(pipelineSteps):
        if st.session_state.pipeline_running and i < 2:
            circle_style = f"background:#f0faf6;color:{BRAND_MINT};font-size:10px;"
            step_icon = "✔"
        else:
            circle_style = "background:#f0f2f5;color:#9ca3af;font-size:10.5px;"
            step_icon = str(i + 1)

        steps_html += (
            f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">'
            f'  <div style="width:20px;height:20px;border-radius:50%;{circle_style}'
            f'    display:flex;align-items:center;justify-content:center;font-family:Inter,sans-serif;'
            f'    font-weight:700;flex-shrink:0;">{step_icon}</div>'
            f'  <span style="font-family:Inter,sans-serif;font-size:13px;color:{SURFACE_TEXT};">{step}</span>'
            f'</div>'
        )

    st.markdown(
        f'<div style="background:#fff;border:1px solid {BORDER};border-radius:12px;overflow:hidden;'
        f'  box-shadow:0 1px 3px rgba(0,0,0,0.04);margin-bottom:20px;">'
        f'  <div style="padding:24px 24px 20px 24px;border-bottom:1px solid {BORDER};display:flex;align-items:center;gap:12px;">'
        f'    <div style="width:40px;height:40px;border-radius:12px;background:#f0faf6;display:flex;'
        f'      align-items:center;justify-content:center;font-size:18px;">⚡</div>'
        f'    <div>'
        f'      <h2 style="font-family:Outfit,sans-serif;font-size:15px;font-weight:600;color:{ON_SURFACE};margin:0;">'
        f'        Pipeline Trigger</h2>'
        f'      <p style="font-family:Inter,sans-serif;font-size:12.5px;color:{MUTED_FOREGROUND};margin:2px 0 0 0;">'
        f'        Manually trigger a full pipeline run in the background.</p>'
        f'    </div>'
        f'  </div>'
        f'  <div style="padding:20px 24px;border-bottom:1px solid {BORDER};">'
        f'    <div style="font-family:Inter,sans-serif;font-size:11.5px;font-weight:600;color:#9ca3af;'
        f'      text-transform:uppercase;letter-spacing:0.06em;margin-bottom:12px;">Pipeline Steps</div>'
        f'    <div style="display:flex;flex-direction:column;gap:4px;">'
        f'      {steps_html}'
        f'    </div>'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True)

    # Actions row for trigger card
    trigger_col, status_col = st.columns([1, 2])
    with trigger_col:
        st.markdown('<div class="trigger-btn">', unsafe_allow_html=True)
        btn_label = "▶  Running…" if st.session_state.pipeline_running else "▶  Run Pipeline Now"
        if st.button(btn_label, key="trigger_pipeline", use_container_width=True, disabled=st.session_state.pipeline_running):
            st.session_state.pipeline_running = True
            trigger_port = int(os.getenv("SCHEDULER_TRIGGER_PORT", 5050))
            try:
                response = requests.post(f"http://localhost:{trigger_port}/trigger", timeout=5)
                if response.status_code == 202:
                    st.success("✅ Pipeline triggered successfully! Check Run History for updates.")
                else:
                    st.error(f"⚠️ Unexpected response: {response.status_code}")
            except requests.ConnectionError:
                st.warning(f"⚠️ Could not connect to trigger service on port {trigger_port}.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
            st.session_state.pipeline_running = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with status_col:
        trigger_port = int(os.getenv("SCHEDULER_TRIGGER_PORT", 5050))
        try:
            health = requests.get(f"http://localhost:{trigger_port}/health", timeout=2)
            if health.status_code == 200:
                st.markdown(
                    f'<div style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;'
                    f'  border-radius:8px;background:#f0faf6;border:1px solid #bbf7d0;margin-top:2px;'
                    f'  font-family:Inter,sans-serif;font-size:12px;font-weight:500;color:#00b386;">'
                    f'  <span style="width:6px;height:6px;border-radius:50%;background:#00b386;display:inline-block;"></span>'
                    f'  Service online (port {trigger_port})</div>',
                    unsafe_allow_html=True)
        except Exception:
            st.markdown(
                f'<div style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;'
                f'  border-radius:8px;background:#fef2f2;border:1px solid #fecaca;margin-top:2px;'
                f'  font-family:Inter,sans-serif;font-size:12px;font-weight:500;color:#ef4444;">'
                f'  <span style="width:6px;height:6px;border-radius:50%;background:#ef4444;display:inline-block;"></span>'
                f'  Trigger service offline (port {trigger_port})</div>',
                unsafe_allow_html=True)

    st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)

    # ── Scheduler Configuration Card ──
    st.markdown(
        f'<div style="background:#fff;border:1px solid {BORDER};border-radius:12px;overflow:hidden;'
        f'  box-shadow:0 1px 3px rgba(0,0,0,0.04);margin-bottom:20px;">'
        f'  <div style="padding:24px 24px 20px 24px;border-bottom:1px solid {BORDER};display:flex;align-items:center;gap:12px;">'
        f'    <div style="width:40px;height:40px;border-radius:12px;background:#eff6ff;display:flex;'
        f'      align-items:center;justify-content:center;font-size:18px;">🕐</div>'
        f'    <div>'
        f'      <h2 style="font-family:Outfit,sans-serif;font-size:15px;font-weight:600;color:{ON_SURFACE};margin:0;">'
        f'        Scheduler Configuration</h2>'
        f'      <p style="font-family:Inter,sans-serif;font-size:12.5px;color:{MUTED_FOREGROUND};margin:2px 0 0 0;">'
        f'        Automated run schedule and approval settings.</p>'
        f'    </div>'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True)

    # Three-column metadata cards
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown(
            f'<div style="background:#f9fafb;border:1px solid {BORDER};border-radius:8px;padding:16px;">'
            f'  <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">'
            f'    <span style="color:#3b82f6;font-size:13px;">🕐</span>'
            f'    <span style="font-family:Inter,sans-serif;font-size:11px;font-weight:600;color:#9ca3af;'
            f'      text-transform:uppercase;letter-spacing:0.05em;">Schedule</span>'
            f'  </div>'
            f'  <div style="font-family:Inter,sans-serif;font-size:13px;font-weight:600;color:{ON_SURFACE};line-height:1.4;">'
            f'    Every Monday at 08:00 IST</div>'
            f'</div>',
            unsafe_allow_html=True)
    with sc2:
        st.markdown(
            f'<div style="background:#f9fafb;border:1px solid {BORDER};border-radius:8px;padding:16px;">'
            f'  <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">'
            f'    <span style="color:#6b7280;font-size:13px;">🌐</span>'
            f'    <span style="font-family:Inter,sans-serif;font-size:11px;font-weight:600;color:#9ca3af;'
            f'      text-transform:uppercase;letter-spacing:0.05em;">Timezone</span>'
            f'  </div>'
            f'  <div style="font-family:Inter,sans-serif;font-size:13px;font-weight:600;color:{ON_SURFACE};line-height:1.4;">'
            f'    Asia/Kolkata</div>'
            f'</div>',
            unsafe_allow_html=True)
    with sc3:
        st.markdown(
            f'<div style="background:#f9fafb;border:1px solid {BORDER};border-radius:8px;padding:16px;">'
            f'  <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">'
            f'    <span style="color:#00b386;font-size:13px;">✔</span>'
            f'    <span style="font-family:Inter,sans-serif;font-size:11px;font-weight:600;color:#9ca3af;'
            f'      text-transform:uppercase;letter-spacing:0.05em;">Approval Gates</span>'
            f'  </div>'
            f'  <div style="font-family:Inter,sans-serif;font-size:13px;font-weight:600;color:{ON_SURFACE};line-height:1.4;">'
            f'    Auto-approved (headless mode)</div>'
            f'</div>',
            unsafe_allow_html=True)

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="edit-schedule-btn">', unsafe_allow_html=True)
    if st.button("Edit Schedule  →", key="edit_schedule"):
        st.info("Schedule editing is currently restricted to configuration files.")
    st.markdown('</div>', unsafe_allow_html=True)
