import sys
import os
import json
import streamlit as st

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui.ui_vars import BODY_HTML
from agentic.data_collection import (
    get_pending_reviews,
    update_review_status,
    delete_detection_record,
    get_collection_stats,
    export_dataset_zip,
)
from agentic.hf_exporter import (
    get_staging_summary,
    push_dataset_to_hub,
    build_hf_dataset,
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

st.markdown('<div class="text-headline-sm font-bold text-on-surface mb-1">📁 Active Data Collection Review (Human-in-the-Loop)</div>', unsafe_allow_html=True)
st.caption("Inspect and relabel candidate detections, manage staged datasets with visual bounding boxes, and push directly to Hugging Face Hub.")

stats = get_collection_stats()

# KPI Metric Cards
st.markdown(f"""
<div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 16px;">
    <div style="background: rgba(76, 215, 246, 0.08); border: 1px solid rgba(76, 215, 246, 0.2); padding: 12px; border-radius: 10px; text-align: center;">
        <div style="font-size: 10px; color: #8e9196; font-weight: 600;">TOTAL SAMPLES</div>
        <div style="font-size: 22px; font-weight: bold; color: #4cd7f6;">{stats['total']}</div>
    </div>
    <div style="background: rgba(234, 179, 8, 0.1); border: 1px solid rgba(234, 179, 8, 0.2); padding: 12px; border-radius: 10px; text-align: center;">
        <div style="font-size: 10px; color: #eab308; font-weight: 600;">PENDING REVIEW</div>
        <div style="font-size: 22px; font-weight: bold; color: #eab308;">{stats['pending']}</div>
    </div>
    <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); padding: 12px; border-radius: 10px; text-align: center;">
        <div style="font-size: 10px; color: #ef4444; font-weight: 600;">ACCIDENTS (CLASS 0)</div>
        <div style="font-size: 22px; font-weight: bold; color: #ef4444;">{stats['confirmed']}</div>
    </div>
    <div style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); padding: 12px; border-radius: 10px; text-align: center;">
        <div style="font-size: 10px; color: #3b82f6; font-weight: 600;">VEHICLES (CLASS 1)</div>
        <div style="font-size: 22px; font-weight: bold; color: #3b82f6;">{stats.get('relabeled_vehicle', 0)}</div>
    </div>
    <div style="background: rgba(107, 114, 128, 0.1); border: 1px solid rgba(107, 114, 128, 0.2); padding: 12px; border-radius: 10px; text-align: center;">
        <div style="font-size: 10px; color: #9ca3af; font-weight: 600;">DISCARDED / FALSE</div>
        <div style="font-size: 22px; font-weight: bold; color: #9ca3af;">{stats['rejected']}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Tabs: 1. Review Queue | 2. Hugging Face Hub Publisher & Staging
review_tab, hf_tab = st.tabs(["📋 Pending Review Queue", "🚀 Hugging Face Hub Staging & Publisher"])

# ==============================================================================
# TAB 1: PENDING REVIEW QUEUE
# ==============================================================================
with review_tab:
    c_exp, c_sp = st.columns([4, 6])
    with c_exp:
        if st.button("📥 Export Reviewed Dataset (ZIP + YOLO Labels)", width='stretch', type="secondary"):
            zip_file = export_dataset_zip()
            if zip_file:
                st.success(f"Dataset exported with images, manifest & YOLO labels:\n`{zip_file}`")
            else:
                st.warning("No reviewed detection logs available to export yet.")

    st.markdown('<div class="border-t border-outline-variant/30" style="margin: 14px 0;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="text-body-md font-bold text-on-surface mb-3">Pending Confirmation & Relabeling Queue</div>', unsafe_allow_html=True)

    pending_items = get_pending_reviews(limit=20)
    if not pending_items:
        st.info("🎉 Verification queue is empty! No detections currently pending operator review.")
    else:
        for idx in range(0, len(pending_items), 2):
            cols_rev = st.columns(2)
            for c_idx, item in enumerate(pending_items[idx:idx+2]):
                with cols_rev[c_idx]:
                    st.markdown(f"""
                    <div style="background: #161c1e; border: 1px solid #263134; border-radius: 12px; padding: 14px; margin-bottom: 14px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <span style="font-weight: 600; color: #4cd7f6;">📹 {item['feed_name']}</span>
                            <span style="font-size: 11px; color: #8e9196;">{item['timestamp']}</span>
                        </div>
                    """, unsafe_allow_html=True)

                    img_path = item.get("image_path", "")
                    show_boxes = st.toggle("👁️ Show Bounding Boxes", value=True, key=f"rev_page_bbox_{item['id']}")

                    display_img = img_path
                    if show_boxes and img_path:
                        ann_path = img_path.replace(".png", "_annotated.png")
                        if os.path.exists(ann_path):
                            display_img = ann_path

                    if display_img and os.path.exists(display_img):
                        st.image(display_img, caption=f"Frame ({'Annotated' if show_boxes else 'Clean View'})", use_container_width=True)

                    # Prediction Details Badge
                    pred_label = item.get("predicted_label", "accident")
                    score_pct = item['confidence_score'] * 100
                    st.markdown(
                        f"<div style='background: rgba(76, 215, 246, 0.08); padding: 8px 12px; border-radius: 8px; margin: 8px 0; font-size: 12px;'>"
                        f"<b>DETR Prediction:</b> <span style='color: #ef4444; font-weight: bold;'>{pred_label.upper()}</span> ({score_pct:.1f}% confidence)<br/>"
                        f"<b>VLM Verifier:</b> {item.get('vlm_verdict', 'NOT_RUN')}"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                    st.markdown('<span style="font-size: 12px; font-weight: 600; color: #eef2f3;">Select Ground Truth Class:</span>', unsafe_allow_html=True)

                    # Quick 1-Click Action Buttons
                    c1, c2, c3 = st.columns([1.2, 1.2, 1.0])
                    
                    with c1:
                        if st.button("🚨 Accident", key=f"page_conf_{item['id']}", width='stretch', type="primary", help="Confirm bounding box as an Accident (Class 0)"):
                            update_review_status(item['id'], "CONFIRMED_ACCIDENT", corrected_label="accident", notes="Operator confirmed as accident")
                            st.rerun()
                    
                    with c2:
                        if st.button("🚗 Vehicle", key=f"page_relabel_{item['id']}", width='stretch', help="Relabel false alarm box as normal Vehicle (Class 1)"):
                            update_review_status(item['id'], "RELABELED_VEHICLE", corrected_label="vehicle", notes="Operator relabeled from accident to vehicle")
                            st.rerun()

                    with c3:
                        if st.button("❌ Discard", key=f"page_rej_{item['id']}", width='stretch', type="secondary", help="Reject sample as background / false alarm"):
                            update_review_status(item['id'], "REJECTED_FALSE_POSITIVE", corrected_label="background", notes="Operator discarded sample")
                            st.rerun()

                    st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# TAB 2: HUGGING FACE HUB STAGING & PUBLISHER (WITH TOGGLE BOXES & DELETE)
# ==============================================================================
with hf_tab:
    st.markdown('<div class="text-body-md font-bold text-on-surface mb-2">🤗 Hugging Face Dataset Staging, Inspection & Direct Hub Publisher</div>', unsafe_allow_html=True)
    st.caption("Inspect curated images, toggle prediction bounding boxes, delete false samples, and push standard Arrow/Parquet datasets to Hugging Face Hub.")

    hf_summary = get_staging_summary()
    staged_samples = hf_summary["samples"]
    valid_samples = [s for s in staged_samples if (s.get("corrected_label") or "").lower() in ["accident", "vehicle"] or s.get("review_status") in ["CONFIRMED_ACCIDENT", "RELABELED_VEHICLE"]]

    col_hf_cfg, col_hf_push = st.columns([6, 4])

    with col_hf_cfg:
        st.markdown('<div class="bg-surface-container border border-outline-variant p-md rounded-xl shadow-card mb-md">', unsafe_allow_html=True)
        st.markdown('<div class="text-body-sm font-bold text-primary mb-2">⚙️ Dataset Configuration & Splits</div>', unsafe_allow_html=True)

        st.markdown(
            f"**Curated Images Ready for Export:** `{len(valid_samples)}` samples  \n"
            f"- 🚨 **Accident Scenes (Class 0):** `{hf_summary['accidents']}` images  \n"
            f"- 🚗 **Normal Vehicle Scenes (Class 1):** `{hf_summary['vehicles']}` images"
        )

        train_val_split = st.slider(
            "Train / Validation Split Ratio",
            min_value=0.50,
            max_value=0.95,
            value=0.85,
            step=0.05,
            format="%.0f%% Train",
            help="Proportion of verified images allocated to the training split."
        )
        num_train_est = int(len(valid_samples) * train_val_split)
        num_val_est = len(valid_samples) - num_train_est
        st.caption(f"Estimated Splits: **{num_train_est}** Train / **{num_val_est}** Validation samples.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_hf_push:
        st.markdown('<div class="bg-surface-container border border-outline-variant p-md rounded-xl shadow-card mb-md">', unsafe_allow_html=True)
        st.markdown('<div class="text-body-sm font-bold text-secondary mb-2">🚀 Push Directly to Hugging Face Hub</div>', unsafe_allow_html=True)

        hf_repo_id = st.text_input(
            "Hugging Face Dataset Repository ID",
            value="traffic-accident-hitl-dataset",
            placeholder="e.g. username/traffic-accidents-dataset",
            help="Target repository path on Hugging Face (e.g. 'dri11heaD/traffic-accidents-hitl')."
        )

        env_token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN") or ""
        hf_token_input = st.text_input(
            "Hugging Face API Token (Write)",
            value=env_token,
            type="password",
            placeholder="hf_...",
            help="Access token with write permissions from https://huggingface.co/settings/tokens"
        )

        hf_is_private = st.toggle("Private Dataset Repository", value=True, help="Set to Private so only your account can view/download.")

        if st.button("🚀 Convert & Push Dataset to Hugging Face Hub", width='stretch', type="primary"):
            if not valid_samples:
                st.error("No reviewed accident or vehicle samples available yet to publish!")
            elif not hf_repo_id.strip():
                st.error("Please provide a valid Hugging Face dataset repository name.")
            elif not hf_token_input.strip() and not env_token:
                st.error("Please provide your Hugging Face API Token (with WRITE access).")
            else:
                with st.spinner("Generating Hugging Face Arrow tables, dataset card, and uploading to Hub..."):
                    try:
                        hub_url = push_dataset_to_hub(
                            repo_id=hf_repo_id.strip(),
                            hf_token=hf_token_input.strip() or env_token,
                            private=hf_is_private,
                            train_ratio=train_val_split,
                        )
                        st.success(f"🎉 Dataset published successfully to Hugging Face Hub!\n\n**Dataset URL:** [{hub_url}]({hub_url})")
                        st.markdown(f'<a href="{hub_url}" target="_blank" style="display: inline-block; padding: 10px 18px; background: #ffb95f; color: #000; font-weight: bold; border-radius: 8px; text-decoration: none; margin-top: 8px;">🔗 Open in Hugging Face Hub</a>', unsafe_allow_html=True)
                    except Exception as push_err:
                        st.error(f"Upload failed: {push_err}")

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="border-t border-outline-variant/30" style="margin: 16px 0;"></div>', unsafe_allow_html=True)
    
    # ==================== STAGING GALLERY & MANAGEMENT ====================
    st.markdown('<div class="text-body-md font-bold text-on-surface mb-2">🖼️ Staged Dataset Inspection & Curation Gallery</div>', unsafe_allow_html=True)
    st.caption("Review all staged samples with toggleable prediction bounding boxes. You can delete any incorrect or redundant samples before pushing to Hugging Face.")

    # Filter Toolbar
    c_flt1, c_flt2, c_flt3 = st.columns([3, 3, 3])
    with c_flt1:
        stg_filter = st.selectbox(
            "Filter Staged Class",
            options=["All Staged Samples", "🚨 Accidents Only (Class 0)", "🚗 Vehicles Only (Class 1)"],
            key="stg_class_filter"
        )
    with c_flt2:
        global_boxes = st.toggle("👁️ Show All Prediction Bounding Boxes", value=True, key="stg_global_bbox_toggle")
    with c_flt3:
        stg_limit = st.selectbox(
            "Show Samples Limit",
            options=[16, 32, 64, 100, 200],
            index=1,
            key="stg_samples_limit"
        )

    # Filter samples
    displayed_samples = list(valid_samples)
    if "Accidents" in stg_filter:
        displayed_samples = [s for s in displayed_samples if (s.get("corrected_label") or "").lower() == "accident" or s.get("review_status") == "CONFIRMED_ACCIDENT"]
    elif "Vehicles" in stg_filter:
        displayed_samples = [s for s in displayed_samples if (s.get("corrected_label") or "").lower() == "vehicle" or s.get("review_status") == "RELABELED_VEHICLE"]

    displayed_samples = displayed_samples[:stg_limit]

    if not displayed_samples:
        st.info("No staged samples match the current filter.")
    else:
        st.markdown(f"<div style='font-size: 12px; color: #8e9196; margin-bottom: 10px;'>Showing <b>{len(displayed_samples)}</b> staged samples:</div>", unsafe_allow_html=True)

        for g_idx in range(0, len(displayed_samples), 4):
            cols_g = st.columns(4)
            for c_i, s in enumerate(displayed_samples[g_idx:g_idx+4]):
                with cols_g[c_i]:
                    c_label = s.get("corrected_label", "accident").lower()
                    badge_color = "#ef4444" if c_label == "accident" else "#3b82f6"
                    badge_name = "🚨 ACCIDENT (0)" if c_label == "accident" else "🚗 VEHICLE (1)"

                    st.markdown(f"""
                    <div style="background: #161c1e; border: 1px solid #263134; border-radius: 10px; padding: 10px; margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-size: 11px; font-weight: bold; color: {badge_color};">{badge_name}</span>
                            <span style="font-size: 10px; color: #8e9196;">#{s['id']}</span>
                        </div>
                    """, unsafe_allow_html=True)

                    # Per-card bounding box toggle (defaults to global toggle state)
                    card_show_boxes = st.toggle("👁️ Boxes", value=global_boxes, key=f"stg_bbox_card_{s['id']}")

                    img_p = s.get("image_path", "")
                    display_p = img_p
                    if card_show_boxes and img_p:
                        ann_p = img_p.replace(".png", "_annotated.png")
                        if os.path.exists(ann_p):
                            display_p = ann_p

                    if display_p and os.path.exists(display_p):
                        st.image(display_p, caption=f"{'Annotated' if card_show_boxes else 'Clean'} | {s.get('confidence_score', 0)*100:.0f}%", use_container_width=True)
                    else:
                        st.caption("No image file found")

                    st.markdown(f"<div style='font-size: 10px; color: #8e9196; margin: 4px 0;'>📹 {s.get('feed_name', 'Cam')} · {s.get('timestamp', '')[:16]}</div>", unsafe_allow_html=True)

                    # Delete sample button
                    if st.button("🗑️ Delete", key=f"stg_del_{s['id']}", width='stretch', help="Permanently delete this sample from the dataset"):
                        delete_detection_record(s['id'], delete_files=True)
                        st.rerun()

                    st.markdown('</div>', unsafe_allow_html=True)
