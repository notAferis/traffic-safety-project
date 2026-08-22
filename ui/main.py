import sys
import os
import streamlit as st

# Ensure project root is in sys.path for runtime imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui.utils import init_verification_worker
from agentic.data_collection import init_data_collection

# Initialize SQLite database & background verification worker
init_data_collection()
init_verification_worker()

# Set Streamlit page configuration
st.set_page_config(
    page_title="Smart Traffic & Safety System",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
PHONE_NUMBERS_FILE = os.path.join(project_root, "phone_numbers.txt")

if "streaming" not in st.session_state:
    st.session_state.streaming = False
if "incident_logs" not in st.session_state:
    st.session_state.incident_logs = []
if "frame_count" not in st.session_state:
    st.session_state.frame_count = 0
if "fps" not in st.session_state:
    st.session_state.fps = 0.0
if "active_incident" not in st.session_state:
    st.session_state.active_incident = False
if "confidence" not in st.session_state:
    st.session_state.confidence = 0.60
if "verification_confidence" not in st.session_state:
    st.session_state.verification_confidence = 0.80
if "frame_skip" not in st.session_state:
    st.session_state.frame_skip = 3
if "show_bounding_boxes" not in st.session_state:
    st.session_state.show_bounding_boxes = True
if "feeds" not in st.session_state:
    default_video = os.path.join(project_root, "agentic", "test_incidents", "video.mp4")
    st.session_state.feeds = [
        {
            "id": 1,
            "name": "Camera 1 (Main)",
            "source_type": "Video File",
            "video_path": default_video if os.path.exists(default_video) else None,
            "stream_url": "",
            "webcam_idx": 0,
            "active": True
        }
    ]
if "phone_numbers" not in st.session_state:
    if os.path.exists(PHONE_NUMBERS_FILE):
        try:
            with open(PHONE_NUMBERS_FILE, "r") as f:
                st.session_state.phone_numbers = f.read().strip()
        except Exception:
            st.session_state.phone_numbers = "0540552725"
    else:
        st.session_state.phone_numbers = "0540552725"
if "last_agent_alert_times" not in st.session_state:
    st.session_state.last_agent_alert_times = {}
if "stream_start_time" not in st.session_state:
    st.session_state.stream_start_time = None
if "verifier_model" not in st.session_state:
    st.session_state.verifier_model = "Qwen 3.5 VL (Local / Offline)"
if "dispatch_cooldown_minutes" not in st.session_state:
    st.session_state.dispatch_cooldown_minutes = 5
if "enable_data_collection" not in st.session_state:
    st.session_state.enable_data_collection = True
if "data_review_threshold" not in st.session_state:
    st.session_state.data_review_threshold = 0.80

import streamlit.components.v1 as components

# Define Navigation Pages located in ui/pages/
pages = [
    st.Page("pages/home.py", title="Live Surveillance", icon="📹", default=True),
    st.Page("pages/ai_settings.py", title="AI Settings", icon="🧠"),
    st.Page("pages/active_review.py", title="Active HITL Review", icon="📁"),
    st.Page("pages/prediction_history.py", title="Prediction History", icon="📊"),
    st.Page("pages/emergency_contacts.py", title="Emergency Contacts", icon="🚨"),
]

pg = st.navigation(pages)

with st.sidebar:
    # 1. Top Brand Banner
    st.markdown("""
    <div class="sidebar-brand-top">
        <div style="display: flex; align-items: center; gap: 12px; padding: 4px 8px 16px 8px; border-bottom: 1px solid #3b494c;">
            <div style="width: 40px; height: 40px; border-radius: 10px; background-color: #192122; display: flex; align-items: center; justify-content: center; border: 1px solid #3b494c; flex-shrink: 0;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#c3f5ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M7 6h10v12H7z"/><circle cx="12" cy="9" r="1.5" fill="#c3f5ff"/><circle cx="12" cy="12" r="1.5" fill="#c3f5ff"/><circle cx="12" cy="15" r="1.5" fill="#c3f5ff"/></svg>
            </div>
            <div>
                <h1 style="font-family: 'Hanken Grotesk', sans-serif; font-size: 16px; font-weight: 700; color: #c3f5ff; margin: 0; line-height: 1.25;">Traffic Safety AI</h1>
                <p style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #bac9cc; margin: 2px 0 0 0;">Autonomous Emergency System</p>
            </div>
        </div>
        <script>
            (function() {
                try {
                    var doc = window.parent.document;
                    var b = doc.querySelector('.sidebar-brand-top');
                    var n = doc.querySelector('[data-testid="stSidebarNav"]');
                    var c = doc.querySelector('[data-testid="stSidebarContent"]');
                    if (b && n && c) {
                        var elem = b.closest('[data-testid="stElementContainer"]') || b;
                        if (c.contains(elem) && c.contains(n) && elem.nextElementSibling !== n) {
                            c.insertBefore(elem, n);
                        }
                    }
                } catch(e) {}
            })();
        </script>
    </div>
    """, unsafe_allow_html=True)

    # 2. Footer Links
    st.markdown("""
    <div class="sidebar-footer-bottom">
        <div style="display: flex; flex-direction: column; gap: 6px; padding: 16px 4px 4px 4px; border-top: 1px solid #3b494c;">
            <a href="#" style="display: flex; align-items: center; gap: 12px; padding: 10px 14px; color: #bac9cc; text-decoration: none; border-radius: 6px; font-size: 13px; font-family: 'Hanken Grotesk', sans-serif; transition: all 0.2s;" onmouseover="this.style.backgroundColor='#2e3638'; this.style.color='#dce4e5';" onmouseout="this.style.backgroundColor='transparent'; this.style.color='#bac9cc';">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                <span>Documentation</span>
            </a>
            <a href="#" style="display: flex; align-items: center; gap: 12px; padding: 10px 14px; color: #bac9cc; text-decoration: none; border-radius: 6px; font-size: 13px; font-family: 'Hanken Grotesk', sans-serif; transition: all 0.2s;" onmouseover="this.style.backgroundColor='#2e3638'; this.style.color='#dce4e5';" onmouseout="this.style.backgroundColor='transparent'; this.style.color='#bac9cc';">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49 0 2.8-.84 3.44-2.16L24 9.5 21.5 8l-1.5 1.5M5 14c-1.49 0-2.8-.84-3.44-2.16L0 9.5 2.5 8l1.5 1.5"/><path d="M18 10a6 6 0 0 0-12 0v5a3 3 0 0 0 3 3h6a3 3 0 0 0 3-3v-5z"/><path d="M9 21v-1a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v1"/></svg>
                <span>Support</span>
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

pg.run()





