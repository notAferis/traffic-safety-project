import sys
import os
import streamlit as st

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui.ui_vars import BODY_HTML
from ui.utils import update_live_settings

@st.cache_data
def get_local_tailwind():
    tailwind_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tailwind.min.css")
    if os.path.exists(tailwind_path):
        with open(tailwind_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

st.markdown(f"<style>{get_local_tailwind()}</style>", unsafe_allow_html=True)
st.markdown(BODY_HTML, unsafe_allow_html=True)

st.markdown('<div class="text-headline-sm font-bold text-on-surface mb-3">🧠 AI Detection & Verification Settings</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="bg-surface-container border border-outline-variant p-md rounded-xl shadow-card mb-md">', unsafe_allow_html=True)
    st.markdown('<div class="text-body-sm font-bold text-primary mb-2">🎯 Primary Detector (RT-DETR-v2)</div>', unsafe_allow_html=True)
    st.caption("Model: `dri11heaD/accident-detection-model` (Fine-tuned for traffic accidents)")

    # Toggle Bounding Boxes On/Off
    col_lbl, col_tgl = st.columns([7, 3])
    with col_lbl:
        st.markdown('<span class="text-body-sm text-on-surface-variant block pt-1">👁️ Draw Bounding Boxes on Stream</span>', unsafe_allow_html=True)
    with col_tgl:
        show_bboxes = st.toggle("Draw Bounding Boxes", value=st.session_state.get("show_bounding_boxes", True), key="toggle_ai_page_bboxes", label_visibility="collapsed")
    st.session_state.show_bounding_boxes = show_bboxes

    # Detection Confidence Threshold Slider
    st.markdown('<div class="border-t border-outline-variant/30" style="margin: 8px 0;"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="flex justify-between text-body-sm text-on-surface-variant"><span>Detection Confidence Gate</span><span class="font-bold text-primary">{st.session_state.confidence * 100:.0f}%</span></div>', unsafe_allow_html=True)
    confidence_thresh = st.slider(
        "Detection Confidence Threshold",
        min_value=0.10,
        max_value=1.00,
        value=float(st.session_state.confidence),
        step=0.05,
        format="%.2f",
        label_visibility="collapsed"
    )
    st.session_state.confidence = confidence_thresh
    st.caption("Frames with DETR accident score above this threshold are forwarded to the VLM Verifier.")

    # AI Frame Skip Slider
    st.markdown('<div class="border-t border-outline-variant/30" style="margin: 8px 0;"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="flex justify-between text-body-sm text-on-surface-variant"><span>AI Frame Skip Rate</span><span class="font-bold text-primary">{st.session_state.frame_skip}</span></div>', unsafe_allow_html=True)
    frame_skip = st.slider(
        "AI Frame Skip",
        min_value=1,
        max_value=10,
        value=st.session_state.frame_skip,
        step=1,
        label_visibility="collapsed"
    )
    st.session_state.frame_skip = frame_skip
    st.caption("Controls inference cadence. Lower = faster reaction, Higher = less CPU/GPU compute load.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="bg-surface-container border border-outline-variant p-md rounded-xl shadow-card mb-md">', unsafe_allow_html=True)
    st.markdown('<div class="text-body-sm font-bold text-secondary mb-2">🤖 Multimodal VLM Verifier Gate</div>', unsafe_allow_html=True)

    st.markdown('<label class="text-body-sm text-on-surface-variant block mb-1">Verifier Model Architecture</label>', unsafe_allow_html=True)
    verifier_options = [
        "Qwen 3.5 VL (Local / Offline)",
        "Gemini 3.7 Flash (Cloud / Online)",
        "Gemini 3.5 Flash (Cloud / Online)",
        "ChatGPT GPT-5.4 Mini (OpenAI / Cloud)",
    ]
    current_idx = 0
    if st.session_state.verifier_model in verifier_options:
        current_idx = verifier_options.index(st.session_state.verifier_model)
    elif "3.5" in st.session_state.verifier_model.lower():
        current_idx = 2
    elif "gemini" in st.session_state.verifier_model.lower():
        current_idx = 1
    elif "gpt" in st.session_state.verifier_model.lower() or "chatgpt" in st.session_state.verifier_model.lower():
        current_idx = 3

    verifier_choice = st.selectbox(
        "Verifier Model Architecture",
        options=verifier_options,
        index=current_idx,
        key="ai_page_verifier_select",
        label_visibility="collapsed"
    )
    st.session_state.verifier_model = verifier_choice

    st.markdown('<div class="border-t border-outline-variant/30" style="margin: 8px 0;"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="flex justify-between text-body-sm text-on-surface-variant"><span>Verification Confidence Threshold</span><span class="font-bold text-secondary">{st.session_state.verification_confidence * 100:.0f}%</span></div>', unsafe_allow_html=True)
    verification_confidence_thresh = st.slider(
        "Verification Threshold",
        min_value=0.10,
        max_value=1.00,
        value=st.session_state.verification_confidence,
        step=0.05,
        label_visibility="collapsed"
    )
    st.session_state.verification_confidence = verification_confidence_thresh

    # Push settings to the background verification worker immediately so
    # pending and future verification jobs use the updated model/threshold.
    update_live_settings(
        verifier_model=verifier_choice,
        verification_threshold=verification_confidence_thresh,
    )
    st.caption("Only VLM confirmations exceeding this confidence score trigger live SMS & voice dispatch.")

    st.markdown('<div class="border-t border-outline-variant/30" style="margin: 8px 0;"></div>', unsafe_allow_html=True)
    col_lbl, col_tgl = st.columns([7, 3])
    with col_lbl:
        st.markdown('<span class="text-body-sm text-on-surface-variant block pt-1">Real-Time Data Collection Logging</span>', unsafe_allow_html=True)
    with col_tgl:
        enable_data_coll = st.toggle("Enable Data Collection", value=st.session_state.enable_data_collection, key="ai_page_data_coll", label_visibility="collapsed")
    st.session_state.enable_data_collection = enable_data_coll
    st.caption("Automatically stores snapshot frames and candidate detections for active HITL review.")
    st.markdown('</div>', unsafe_allow_html=True)
