import sys
import os
import streamlit as st

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui.ui_vars import BODY_HTML
from ui.utils import parse_phone_numbers

PHONE_NUMBERS_FILE = os.path.join(project_root, "phone_numbers.txt")

@st.cache_data
def get_local_tailwind():
    tailwind_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tailwind.min.css")
    if os.path.exists(tailwind_path):
        with open(tailwind_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

st.markdown(f"<style>{get_local_tailwind()}</style>", unsafe_allow_html=True)
st.markdown(BODY_HTML, unsafe_allow_html=True)

st.markdown('<div class="text-headline-sm font-bold text-on-surface mb-2">🚨 Emergency Contacts & Dispatch Configuration</div>', unsafe_allow_html=True)
st.caption("Manage responders notified during verified traffic collisions.")

_dispatch_mode = os.getenv("DISPATCH_MODE", "online").strip().lower()

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="bg-surface-container border border-outline-variant p-md rounded-xl shadow-card">', unsafe_allow_html=True)
    st.markdown('<div class="text-body-sm font-bold text-primary mb-2">📞 Responders Phone List</div>', unsafe_allow_html=True)

    phone_numbers_input = st.text_area(
        "Emergency Phone Numbers (comma-separated)",
        value=st.session_state.get("phone_numbers", "0540552725"),
        placeholder="e.g. 0540552725, 0244123456",
        height=120,
        key="contacts_page_numbers_input"
    )
    if phone_numbers_input != st.session_state.get("phone_numbers", ""):
        st.session_state.phone_numbers = phone_numbers_input
        try:
            with open(PHONE_NUMBERS_FILE, "w") as f:
                f.write(phone_numbers_input)
            st.success("Phone numbers updated successfully!")
        except Exception as e:
            st.error(f"Error saving phone numbers: {e}")

    contacts_list = parse_phone_numbers(st.session_state.get("phone_numbers", "0540552725"))
    st.markdown(f"**Active Contacts Count:** `{len(contacts_list)}` numbers parsed")
    for num in contacts_list:
        st.markdown(f"- 📱 `{num}`")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="bg-surface-container border border-outline-variant p-md rounded-xl shadow-card">', unsafe_allow_html=True)
    st.markdown('<div class="text-body-sm font-bold text-secondary mb-2">📡 Dispatch Mode Overview</div>', unsafe_allow_html=True)

    if _dispatch_mode == "offline":
        st.markdown("""
        <div style="background: rgba(78, 222, 163, 0.1); border: 1px solid rgba(78, 222, 163, 0.2); padding: 12px; border-radius: 8px; margin-bottom: 10px;">
            <div style="font-weight: bold; color: #4edea3;">Mode: OFFLINE (GSM / Termux)</div>
            <div style="font-size: 12px; color: #9fadb2; margin-top: 4px;">Dispatches SMS messages directly through the local connected GSM Android / Termux phone node without requiring internet access.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(76, 215, 246, 0.1); border: 1px solid rgba(76, 215, 246, 0.2); padding: 12px; border-radius: 8px; margin-bottom: 10px;">
            <div style="font-weight: bold; color: #4cd7f6;">Mode: ONLINE (mNotify API + Voice Calls)</div>
            <div style="font-size: 12px; color: #9fadb2; margin-top: 4px;">Sends rapid SMS notifications via mNotify SMS API and initiates automated voice call alerts to all registered emergency contacts.</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
