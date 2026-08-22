import sys
import os
import time
import tempfile
import threading
from datetime import datetime
import cv2
import streamlit as st

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui.ui_vars import (
    BODY_HTML,
    TOP_HEADER_TEMPLATE,
    METRICS_TEMPLATE,
    LIVE_FEED_HEADER_TEMPLATE,
    DEFAULT_PLACEHOLDER_HTML,
    LIVE_FEED_FOOTER_TEMPLATE,
    LOG_CONSOLE_TEMPLATE,
    STATS_CARD_TEMPLATE,
    DEFAULT_LOG_CONSOLE_HTML,
    DEFAULT_STATS_CARD_HTML
)
from ui.utils import (
    load_incident_detector,
    open_video_captures,
    parse_phone_numbers,
    run_detection_worker,
    enqueue_verification_job,
)
from agentic.data_collection import (
    enqueue_detection,
    save_snapshot_image,
    is_duplicate_frame,
)

# Cache loader for local Tailwind CSS
@st.cache_data
def get_local_tailwind():
    tailwind_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tailwind.min.css")
    if os.path.exists(tailwind_path):
        with open(tailwind_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

st.markdown(f"<style>{get_local_tailwind()}</style>", unsafe_allow_html=True)

def clean_html(html_str: str) -> str:
    return "\n".join(line.strip() for line in html_str.split("\n"))

def render_html(html_str: str):
    st.markdown(clean_html(html_str), unsafe_allow_html=True)

render_html(BODY_HTML)

detector = load_incident_detector()
global_logs = []

# Top Header
_dispatch_mode = os.getenv("DISPATCH_MODE", "online").strip().lower()
if _dispatch_mode == "offline":
    _dispatch_badge_bg, _dispatch_badge_color, _dispatch_badge_border = "bg-secondary/12", "text-secondary", "border-secondary/20"
    _dispatch_icon, _dispatch_label = "wifi_off", "Offline Dispatch"
else:
    _dispatch_badge_bg, _dispatch_badge_color, _dispatch_badge_border = "bg-primary/12", "text-primary", "border-primary/20"
    _dispatch_icon, _dispatch_label = "wifi", "Online Dispatch"

top_header_html = TOP_HEADER_TEMPLATE.format(
    dispatch_badge_bg=_dispatch_badge_bg,
    dispatch_badge_color=_dispatch_badge_color,
    dispatch_badge_border=_dispatch_badge_border,
    dispatch_icon=_dispatch_icon,
    dispatch_label=_dispatch_label,
    clock_display=datetime.now().strftime("%a %d %b · %H:%M")
)
render_html(top_header_html)

# ==================== STREAM SETTINGS & CONTROLS ON HOME ====================
with st.container():
    col_ctrl, col_cfg = st.columns([3, 7])

    with col_ctrl:
        st.markdown('<div class="text-body-sm font-bold text-on-surface mb-1">🎮 Stream Control</div>', unsafe_allow_html=True)
        if not st.session_state.streaming:
            if st.button("▶️ Start Live Stream", width='stretch', type="primary", key="home_start_stream_btn"):
                valid = True
                active_feeds = [f for f in st.session_state.feeds if f['active']]
                if not active_feeds:
                    st.error("Activate at least one camera feed!")
                    valid = False
                else:
                    for feed in active_feeds:
                        if feed['source_type'] == "Video File" and feed['video_path'] is None:
                            st.error(f"Upload a video for {feed['name']} first!")
                            valid = False
                        elif feed['source_type'] == "Network Camera (RTSP/HTTP)" and not feed['stream_url']:
                            st.error(f"Provide an RTSP or HTTP stream URL for {feed['name']} first!")
                            valid = False

                if valid:
                    st.session_state.streaming = True
                    st.session_state.frame_count = 0
                    st.session_state.fps = 0.0
                    st.session_state.active_incident = False
                    st.session_state.last_agent_alert_times = {}
                    st.session_state.incident_logs = []
                    st.session_state.stream_start_time = time.time()
                    st.rerun()
        else:
            if st.button("⏹️ Stop Stream", width='stretch', type="secondary", key="home_stop_stream_btn"):
                st.session_state.streaming = False
                st.rerun()

    with col_cfg:
        with st.expander("📹 Camera Feed Setup & Sources", expanded=(not st.session_state.streaming and all(f['video_path'] is None and not f['stream_url'] for f in st.session_state.feeds))):
            cols_feeds = st.columns(len(st.session_state.feeds))
            for i, feed in enumerate(st.session_state.feeds):
                with cols_feeds[i]:
                    st.markdown(f"**{feed['name']}**")
                    feed['name'] = st.text_input("Name", value=feed['name'], key=f"home_name_{feed['id']}")
                    feed['source_type'] = st.selectbox(
                        "Source",
                        options=["Video File", "Network Camera (RTSP/HTTP)", "USB Local Stream"],
                        index=["Video File", "Network Camera (RTSP/HTTP)", "USB Local Stream"].index(feed['source_type']),
                        key=f"home_src_{feed['id']}"
                    )

                    if feed['source_type'] == "Video File":
                        file_key = f"last_uploaded_file_{feed['id']}"
                        uploaded_file = st.file_uploader(
                            "Upload Video",
                            type=["mp4", "avi", "mov", "mkv"],
                            key=f"home_upload_{feed['id']}"
                        )
                        if uploaded_file is not None:
                            # A new file is in the uploader — only re-save if it's
                            # a different file than what we already processed.
                            if file_key not in st.session_state or st.session_state[file_key] != uploaded_file.name:
                                # Clean up old temp file (but don't delete default test videos)
                                if feed["video_path"] and os.path.exists(feed["video_path"]) and "test_incidents" not in feed["video_path"]:
                                    try:
                                        os.remove(feed["video_path"])
                                    except Exception:
                                        pass
                                tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                                tfile.write(uploaded_file.read())
                                tfile.flush()
                                tfile.close()
                                feed["video_path"] = tfile.name
                                st.session_state[file_key] = uploaded_file.name

                        # When uploaded_file is None (happens on every st.rerun()),
                        # do NOT touch feed["video_path"] — it's already set from
                        # the upload or from the default. Only assign the default
                        # test video if nothing has ever been set.
                        if not feed.get("video_path"):
                            default_vid = os.path.join(project_root, "agentic", "test_incidents", "video.mp4")
                            if os.path.exists(default_vid):
                                feed["video_path"] = default_vid

                        # Show currently loaded source
                        if feed.get("video_path"):
                            loaded_name = st.session_state.get(file_key, os.path.basename(feed["video_path"]))
                            st.caption(f"📂 Loaded: `{loaded_name}`")

                    elif feed['source_type'] == "Network Camera (RTSP/HTTP)":
                        feed['stream_url'] = st.text_input(
                            "Stream URL",
                            value=feed['stream_url'],
                            placeholder="rtsp://... or http://...",
                            key=f"home_url_{feed['id']}"
                        )

                    elif feed['source_type'] == "USB Local Stream":
                        feed['webcam_idx'] = st.number_input(
                            "Webcam Index",
                            min_value=0,
                            max_value=10,
                            value=feed['webcam_idx'],
                            step=1,
                            key=f"home_webcam_{feed['id']}"
                        )

                    feed['active'] = st.toggle("Active Feed", value=feed['active'], key=f"home_active_{feed['id']}")

            if len(st.session_state.feeds) < 5:
                if st.button("➕ Add Another Camera Feed"):
                    new_id = max([f['id'] for f in st.session_state.feeds], default=0) + 1
                    st.session_state.feeds.append({
                        "id": new_id,
                        "name": f"Camera {new_id}",
                        "source_type": "Video File",
                        "video_path": None,
                        "stream_url": "",
                        "webcam_idx": 0,
                        "active": True
                    })
                    st.rerun()

st.markdown('<div class="border-t border-outline-variant/30" style="margin: 8px 0 14px 0;"></div>', unsafe_allow_html=True)

# ==================== MAIN SURVEILLANCE GRID ====================
col_video, col_logs = st.columns([7, 3])

with col_video:
    metrics_placeholder = st.empty()
    active_feeds = [f for f in st.session_state.feeds if f['active']]

    def render_metrics():
        status_text = "Active" if st.session_state.streaming else "Idle"
        status_color = "#4edea3" if st.session_state.streaming else "#6b7a80"
        status_animate = "animate-pulse" if st.session_state.streaming else ""
        status_shadow = "box-shadow: 0 0 8px rgba(78,222,163,0.6);" if st.session_state.streaming else ""

        current_active_feeds = [f for f in st.session_state.feeds if f['active']]
        source_display = f"{len(current_active_feeds)} Active Feeds" if st.session_state.streaming else "Idle"
        fps_display = f"{st.session_state.fps:.1f}" if st.session_state.streaming else "0.0"

        if st.session_state.active_incident:
            alert_text, alert_bg, alert_color = "Danger", "bg-error/12", "text-error"
        else:
            alert_text, alert_bg, alert_color = "Safe", "bg-secondary/12", "text-secondary"

        metrics_html = METRICS_TEMPLATE.format(
            status_animate=status_animate,
            status_color=status_color,
            status_shadow=status_shadow,
            status_text=status_text,
            source_display=source_display,
            fps_display=fps_display,
            alert_bg=alert_bg,
            alert_color=alert_color,
            alert_text=alert_text
        )
        metrics_placeholder.markdown(clean_html(metrics_html), unsafe_allow_html=True)

    render_metrics()

    run_ai = True
    ai_badge_bg, ai_badge_color, ai_badge_border = "bg-secondary/10", "text-secondary", "border-secondary/20"
    ai_dot_bg, ai_dot_animate, ai_status_text = "bg-secondary", "animate-pulse", "ON"

    live_feed_header_html = LIVE_FEED_HEADER_TEMPLATE.format(
        ai_badge_bg=ai_badge_bg,
        ai_badge_color=ai_badge_color,
        ai_badge_border=ai_badge_border,
        ai_dot_bg=ai_dot_bg,
        ai_dot_animate=ai_dot_animate,
        ai_status_text=ai_status_text
    )
    render_html(live_feed_header_html)

    if not st.session_state.streaming:
        video_placeholder = st.empty()
        video_placeholder.markdown(clean_html(DEFAULT_PLACEHOLDER_HTML), unsafe_allow_html=True)
    else:
        placeholders = {}
        num_feeds = len(active_feeds)

        if num_feeds == 1:
            st.markdown(f"<div style='text-align: center; font-weight: bold; margin-bottom: 5px; color: #4cd7f6;'>📹 {active_feeds[0]['name']}</div>", unsafe_allow_html=True)
            placeholders[active_feeds[0]['id']] = st.empty()
        elif num_feeds == 2:
            cols = st.columns(2)
            for j, feed in enumerate(active_feeds):
                with cols[j]:
                    st.markdown(f"<div style='text-align: center; font-weight: bold; margin-bottom: 5px; color: #4cd7f6;'>📹 {feed['name']}</div>", unsafe_allow_html=True)
                    placeholders[feed['id']] = st.empty()
        elif num_feeds == 3:
            cols = st.columns(3)
            for j, feed in enumerate(active_feeds):
                with cols[j]:
                    st.markdown(f"<div style='text-align: center; font-weight: bold; margin-bottom: 5px; color: #4cd7f6;'>📹 {feed['name']}</div>", unsafe_allow_html=True)
                    placeholders[feed['id']] = st.empty()
        elif num_feeds == 4:
            cols_r1 = st.columns(2)
            cols_r2 = st.columns(2)
            for j, feed in enumerate(active_feeds):
                if j < 2:
                    with cols_r1[j]:
                        st.markdown(f"<div style='text-align: center; font-weight: bold; margin-bottom: 5px; color: #4cd7f6;'>📹 {feed['name']}</div>", unsafe_allow_html=True)
                        placeholders[feed['id']] = cols_r1[j].empty()
                else:
                    with cols_r2[j - 2]:
                        st.markdown(f"<div style='text-align: center; font-weight: bold; margin-bottom: 5px; color: #4cd7f6;'>📹 {feed['name']}</div>", unsafe_allow_html=True)
                        placeholders[feed['id']] = cols_r2[j - 2].empty()
        else: # 5 feeds
            cols_r1 = st.columns(3)
            cols_r2 = st.columns(2)
            for j, feed in enumerate(active_feeds):
                if j < 3:
                    with cols_r1[j]:
                        st.markdown(f"<div style='text-align: center; font-weight: bold; margin-bottom: 5px; color: #4cd7f6;'>📹 {feed['name']}</div>", unsafe_allow_html=True)
                        placeholders[feed['id']] = cols_r1[j].empty()
                else:
                    with cols_r2[j - 3]:
                        st.markdown(f"<div style='text-align: center; font-weight: bold; margin-bottom: 5px; color: #4cd7f6;'>📹 {feed['name']}</div>", unsafe_allow_html=True)
                        placeholders[feed['id']] = cols_r2[j - 3].empty()

    live_feed_footer_html = LIVE_FEED_FOOTER_TEMPLATE.format(
        feed_count_display=f"{len(active_feeds)}/{len(st.session_state.feeds)} FEEDS ACTIVE",
        threshold_display=f"{st.session_state.confidence:.2f}"
    )
    render_html(live_feed_footer_html)

with col_logs:
    log_placeholder = st.empty()
    stats_placeholder = st.empty()

# Streaming Loop
if st.session_state.streaming:
    caps, failed_feed_names = open_video_captures(active_feeds)
    for failed_name in failed_feed_names:
        st.error(f"Failed to open video source for {failed_name}")

    if not caps:
        st.error("No camera feeds could be opened. Please check inputs and try again.")
        st.session_state.streaming = False
        st.rerun()
    else:
        prev_time = time.time()
        using_gpu = detector is not None and detector.device.type in ("cuda", "mps")
        ai_cadence_dt = 0.42 if using_gpu else (1.0 / 3.0)
        target_dt = ai_cadence_dt if detector is not None else (1.0 / 30.0)

        inference_state = {"latest_frames": {}, "predictions": {}}
        inference_stop_event = threading.Event()

        detection_thread = threading.Thread(
            target=run_detection_worker,
            args=(inference_state, True, detector, inference_stop_event, st.session_state.frame_skip),
            daemon=True,
        )
        detection_thread.start()

        while st.session_state.streaming:
            loop_start = time.time()
            any_frame_read = False
            active_alert_in_any_feed = False

            for cap_idx, (feed, cap) in enumerate(caps):
                ret, frame = cap.read()

                if not ret:
                    if feed['source_type'] == "Video File":
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = cap.read()
                    elif feed['source_type'] == "Network Camera (RTSP/HTTP)":
                        cap.release()
                        reconnect_url = feed.get('stream_url') or ""
                        if reconnect_url:
                            cap = cv2.VideoCapture(reconnect_url, cv2.CAP_FFMPEG)
                            caps[cap_idx][1] = cap
                            ret, frame = cap.read()

                if not ret:
                    continue

                any_frame_read = True

                height, width = frame.shape[:2]
                max_w = 480 if len(active_feeds) > 1 else 960
                if width > max_w:
                    ratio = max_w / float(width)
                    frame = cv2.resize(frame, (max_w, int(height * ratio)))

                clean_frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                if detector is not None:
                    inference_state["latest_frames"][feed['id']] = clean_frame_rgb.copy()
                    preds = [
                        d for d in inference_state["predictions"].get(feed['id'], [])
                        if d["score"] >= st.session_state.confidence
                    ]
                else:
                    preds = []

                annotated_frame_rgb = clean_frame_rgb.copy()
                active_alert_in_feed = False
                highest_accident_score = 0.0

                for pred in preds:
                    box = pred["box"]
                    xmin, ymin, xmax, ymax = int(box["xmin"]), int(box["ymin"]), int(box["xmax"]), int(box["ymax"])
                    label = pred["label"]
                    score = pred["score"]

                    is_accident = any(k in label.lower() for k in ["accident", "collision", "crash", "incident"])

                    if is_accident:
                        active_alert_in_feed = True
                        active_alert_in_any_feed = True
                        color = (239, 68, 68)
                        label_text = f"ACCIDENT {score:.2f}"
                        if score > highest_accident_score:
                            highest_accident_score = score
                    else:
                        color = (76, 215, 246)
                        label_text = f"{label.upper()} {score:.2f}"

                    cv2.rectangle(annotated_frame_rgb, (xmin, ymin), (xmax, ymax), color, 2)
                    (tw, th), base = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                    cv2.rectangle(annotated_frame_rgb, (xmin, ymin - th - 8), (xmin + tw + 10, ymin), color, -1)
                    text_color = (0, 56, 36) if not is_accident else (255, 255, 255)
                    cv2.putText(annotated_frame_rgb, label_text, (xmin + 5, ymin - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, text_color, 1, cv2.LINE_AA)

                if active_alert_in_any_feed:
                    st.session_state.active_incident = True

                if active_alert_in_feed:
                    curr_t = time.time()

                    if st.session_state.get("enable_data_collection", True):
                        last_snap_t = st.session_state.get(f"last_snap_t_{feed['id']}", 0.0)
                        if (curr_t - last_snap_t) > 3.0:
                            # Visual deduplication: discard identical or near-identical frames
                            if not is_duplicate_frame(clean_frame_rgb, feed['id']):
                                st.session_state[f"last_snap_t_{feed['id']}"] = curr_t
                                snap_path = save_snapshot_image(
                                    clean_frame_rgb,
                                    filename_prefix=f"frame{feed['id']}",
                                    annotated_image=annotated_frame_rgb
                                )
                                enqueue_detection(
                                    feed_name=feed['name'],
                                    confidence_score=highest_accident_score,
                                    image_path=snap_path,
                                    review_thresh=st.session_state.get("data_review_threshold", 0.80),
                                    predicted_label="accident",
                                    bounding_boxes=preds
                                )

                    last_log_t = st.session_state.get("last_log_time", 0.0)
                    if (curr_t - last_log_t) > 3.0:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        st.session_state.incident_logs.insert(0, {
                            "time": timestamp,
                            "type": f"ACCIDENT DETECTED ({feed['name']})",
                            "confidence": f"{highest_accident_score * 100:.1f}%",
                            "color_class": "text-red-400"
                        })
                        st.session_state.last_log_time = curr_t

                    if highest_accident_score >= st.session_state.confidence:
                        last_enqueue_t = st.session_state.get(f"last_enqueue_t_{feed['id']}", 0.0)
                        if (curr_t - last_enqueue_t) > 3.0:
                            st.session_state[f"last_enqueue_t_{feed['id']}"] = curr_t

                            import base64
                            try:
                                frame_bgr = cv2.cvtColor(clean_frame_rgb, cv2.COLOR_RGB2BGR)
                                _, buffer = cv2.imencode('.jpg', frame_bgr)
                                img_base64 = base64.b64encode(buffer).decode('utf-8')

                                ann_bgr = cv2.cvtColor(annotated_frame_rgb, cv2.COLOR_RGB2BGR)
                                _, ann_buffer = cv2.imencode('.jpg', ann_bgr)
                                ann_img_base64 = base64.b64encode(ann_buffer).decode('utf-8')
                            except Exception:
                                img_base64 = None
                                ann_img_base64 = None

                            dispatch_contacts = parse_phone_numbers(st.session_state.phone_numbers)

                            enqueue_verification_job({
                                "feed_name": feed['name'],
                                "location_info": f"Intersection monitored by {feed['name']}",
                                "confidence_val": highest_accident_score * 100,
                                "image_base64_data": img_base64,
                                "annotated_base64_data": ann_img_base64,
                                "contacts": dispatch_contacts,
                                "verification_threshold": st.session_state.verification_confidence,
                                "global_logs": global_logs,
                                "verifier_model": st.session_state.verifier_model
                            })

                            timestamp = datetime.now().strftime("%H:%M:%S")
                            st.session_state.incident_logs.insert(0, {
                                "time": timestamp,
                                "type": f"QUEUED FOR VLM VERIFICATION ({feed['name']})",
                                "confidence": f"{highest_accident_score * 100:.1f}%",
                                "color_class": "text-yellow-400 font-bold"
                            })

                display_frame = annotated_frame_rgb if st.session_state.get("show_bounding_boxes", True) else clean_frame_rgb

                if feed['id'] in placeholders:
                    placeholders[feed['id']].image(display_frame, channels="RGB", width='stretch')

            if not any_frame_read:
                break

            st.session_state.frame_count += 1
            st.session_state.active_incident = active_alert_in_any_feed

            while len(global_logs) > 0:
                log_item = global_logs.pop(0)
                st.session_state.incident_logs.insert(0, log_item)

            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time)
            prev_time = curr_time
            st.session_state.fps = 0.9 * st.session_state.fps + 0.1 * fps if st.session_state.fps > 0 else fps
            render_metrics()

            logs_html = ""
            if st.session_state.incident_logs:
                for log in st.session_state.incident_logs[:8]:
                    logs_html += f"""
                    <div class="flex gap-2 {log['color_class']}">
                        <span>[{log['time']}]</span>
                        <span>{log['type']} - CONFIDENCE: {log['confidence']}</span>
                    </div>
                    """
            else:
                logs_html = """
                <div class="animate-pulse flex gap-2 text-secondary">
                    <span class="flex items-center gap-1">MONITORING ACTIVE — no incidents detected yet<span class="w-1 h-3 bg-secondary animate-bounce"></span></span>
                </div>
                """

            log_placeholder.markdown(clean_html(LOG_CONSOLE_TEMPLATE.format(logs_html=logs_html)), unsafe_allow_html=True)

            elapsed_s = int(time.time() - st.session_state.stream_start_time) if st.session_state.stream_start_time else 0
            elapsed_display = f"{elapsed_s // 60:02d}:{elapsed_s % 60:02d}"
            flags_count = sum(1 for l in st.session_state.incident_logs if l['type'].startswith("ACCIDENT DETECTED"))
            dispatched_count = sum(1 for l in st.session_state.incident_logs if l['type'].startswith("DISPATCH OK"))
            filtered_count = sum(1 for l in st.session_state.incident_logs if l['type'].startswith("FALSE ALARM FILTERED"))

            stats_placeholder.markdown(clean_html(STATS_CARD_TEMPLATE.format(
                elapsed_display=elapsed_display,
                frame_count=st.session_state.frame_count,
                flags_count=flags_count,
                dispatched_count=dispatched_count,
                filtered_count=filtered_count
            )), unsafe_allow_html=True)

            elapsed = time.time() - loop_start
            time.sleep(max(0.0, target_dt - elapsed))

        inference_stop_event.set()
        detection_thread.join(timeout=1.0)
        for feed, cap in caps:
            cap.release()

        st.session_state.streaming = False
        st.rerun()

if not st.session_state.streaming:
    log_placeholder.markdown(clean_html(DEFAULT_LOG_CONSOLE_HTML), unsafe_allow_html=True)
    stats_placeholder.markdown(clean_html(DEFAULT_STATS_CARD_HTML), unsafe_allow_html=True)
