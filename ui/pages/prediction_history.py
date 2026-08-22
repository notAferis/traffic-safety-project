import sys
import os
import json
import streamlit as st

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui.ui_vars import BODY_HTML
from agentic.data_collection import (
    get_verification_history,
    get_verification_analytics,
)

@st.cache_data
def get_local_tailwind():
    tailwind_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tailwind.min.css")
    if os.path.exists(tailwind_path):
        with open(tailwind_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

st.markdown(f"<style>{get_local_tailwind()}</style>", unsafe_allow_html=True)
st.markdown(BODY_HTML, unsafe_allow_html=True)

st.markdown('<div class="text-headline-sm font-bold text-on-surface mb-2">📊 Incident Verification History & Analytics</div>', unsafe_allow_html=True)
st.caption("Complete chronological record of all detections verified by the multimodal VLM agent.")

v_analytics = get_verification_analytics()

# High-level Metrics Cards
v_total = v_analytics.get('total', 0)
v_acc = v_analytics.get('accidents', 0)
v_fp = v_analytics.get('false_positives', 0)
v_rate = v_analytics.get('filter_rate', v_analytics.get('false_positive_rate', 0.0))

st.markdown(f"""
<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px;">
    <div style="background: rgba(76, 215, 246, 0.08); border: 1px solid rgba(76, 215, 246, 0.2); padding: 14px; border-radius: 10px; text-align: center;">
        <div style="font-size: 11px; color: #8e9196; font-weight: 600;">TOTAL VERIFICATIONS</div>
        <div style="font-size: 24px; font-weight: bold; color: #4cd7f6;">{v_total}</div>
    </div>
    <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); padding: 14px; border-radius: 10px; text-align: center;">
        <div style="font-size: 11px; color: #ef4444; font-weight: 600;">VERIFIED ACCIDENTS</div>
        <div style="font-size: 24px; font-weight: bold; color: #ef4444;">{v_acc}</div>
    </div>
    <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.2); padding: 14px; border-radius: 10px; text-align: center;">
        <div style="font-size: 11px; color: #22c55e; font-weight: 600;">FALSE POSITIVES FILTERED</div>
        <div style="font-size: 24px; font-weight: bold; color: #22c55e;">{v_fp}</div>
    </div>
    <div style="background: rgba(255, 185, 95, 0.1); border: 1px solid rgba(255, 185, 95, 0.2); padding: 14px; border-radius: 10px; text-align: center;">
        <div style="font-size: 11px; color: #ffb95f; font-weight: 600;">FILTER EFFICIENCY RATE</div>
        <div style="font-size: 24px; font-weight: bold; color: #ffb95f;">{v_rate:.1f}%</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Time series chart
if v_analytics.get("time_series"):
    import pandas as pd
    df_ts = pd.DataFrame(v_analytics["time_series"])
    if not df_ts.empty and "time" in df_ts.columns:
        df_ts.set_index("time", inplace=True)
        st.markdown('<div class="text-body-sm font-bold text-on-surface mb-1">📈 Accident Detections Over Time</div>', unsafe_allow_html=True)
        st.bar_chart(df_ts, height=180)

st.markdown('<div class="border-t border-outline-variant/30" style="margin: 16px 0;"></div>', unsafe_allow_html=True)

# Filters Toolbar
c_f1, c_f2, c_sp = st.columns([3, 3, 4])
with c_f1:
    hist_status_filter = st.selectbox(
        "Filter Verdict Status",
        options=["All Verifications", "Verified Accidents Only", "False Alarms Filtered Only"],
        key="page_hist_verdict_filter"
    )
with c_f2:
    feed_names = ["All Feeds"] + [f["name"] for f in st.session_state.get("feeds", [])]
    hist_feed_filter = st.selectbox(
        "Filter Camera Feed",
        options=feed_names,
        key="page_hist_feed_filter"
    )

acc_only = (hist_status_filter == "Verified Accidents Only")
f_filter = None if hist_feed_filter == "All Feeds" else hist_feed_filter
v_history = get_verification_history(limit=50, accident_only=acc_only, feed_filter=f_filter)

if hist_status_filter == "False Alarms Filtered Only":
    v_history = [h for h in v_history if h.get("is_accident") == 0]

if not v_history:
    st.info("No past verification records match the selected filter.")
else:
    for record in v_history:
        is_acc = record.get("is_accident") == 1
        status_badge = "🚨 ACCIDENT DISPATCHED" if is_acc else "🛡️ FALSE ALARM FILTERED"
        badge_color = "#ef4444" if is_acc else "#3b82f6"

        with st.expander(f"{status_badge} — {record['feed_name']} ({record['timestamp']})", expanded=False):
            col_img, col_det = st.columns([4, 6])
            with col_img:
                img_p = record.get("image_path", "")
                show_boxes = st.toggle("👁️ Show Bounding Boxes", value=False, key=f"hist_page_bbox_{record['id']}")

                display_img = img_p
                if show_boxes and img_p:
                    ann_path = img_p.replace(".png", "_annotated.png")
                    if os.path.exists(ann_path):
                        display_img = ann_path

                if display_img and os.path.exists(display_img):
                    st.image(display_img, caption=f"{'Annotated View' if show_boxes else 'Clean View'} @ {record['timestamp']}", use_container_width=True)

            with col_det:
                st.markdown(
                    f"<div style='font-size: 13px; color: {badge_color}; font-weight: bold; margin-bottom: 6px;'>"
                    f"Status: {record['dispatch_status']} | Model: {record['verifier_model']}</div>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"**DETR Detector Score:** `{record['detr_confidence'] * 100:.1f}%`  \n"
                    f"**VLM Verifier Score:** `{record['vlm_confidence'] * 100:.1f}%`"
                )
                if record.get("sms_report"):
                    st.info(f"**SMS Dispatch Report:**\n{record['sms_report']}")

                try:
                    v_json = json.loads(record.get("vlm_response_json", "{}"))
                    st.markdown("**Structured Visual Features:**")
                    st.markdown(f"- **Vehicles:** {v_json.get('vehicles_involved', 'N/A')}")
                    st.markdown(f"- **Damage & Hazards:** {v_json.get('damage_and_hazards', 'N/A')}")
                    st.markdown(f"- **Road Blockage:** {v_json.get('road_blockage_status', 'N/A')}")
                    st.markdown(f"- **Observations:** {v_json.get('observations', 'N/A')}")
                    with st.expander("📄 Raw Model JSON", expanded=False):
                        st.json(v_json)
                except Exception:
                    if record.get("observations"):
                        st.markdown(f"**Observations:** {record['observations']}")
