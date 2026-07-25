import sys
import os
import time
import tempfile
import threading
from datetime import datetime
import cv2
import streamlit as st

# Ensure project root is in sys.path for both runtime and linter resolution
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui.ui_vars import (
    BODY_HTML,
    SIDEBAR_HEADER_HTML,
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
    trigger_agent_dispatch,
)

# Set Streamlit page configurations
st.set_page_config(
    page_title="Smart Traffic & Safety System",
    page_icon="🚦",
    layout="wide"
)

# Cache loader for local Tailwind CSS to avoid reading 2.8MB file from disk on every rerun
@st.cache_data
def get_local_tailwind():
    tailwind_path = os.path.join(os.path.dirname(__file__), "tailwind.min.css")
    if os.path.exists(tailwind_path):
        with open(tailwind_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

# Inject local Tailwind CSS rules directly as an inline stylesheet
st.markdown(f"<style>{get_local_tailwind()}</style>", unsafe_allow_html=True)

# Robust HTML rendering helper that strips leading whitespace from each line
def clean_html(html_str: str) -> str:
    return "\n".join(line.strip() for line in html_str.split("\n"))

def render_html(html_str: str):
    st.markdown(clean_html(html_str), unsafe_allow_html=True)

# Custom premium CSS styling to override Streamlit defaults and implement the design theme
render_html(BODY_HTML)

# Initialize Session State Variables
PHONE_NUMBERS_FILE = os.path.join(project_root, "phone_numbers.txt")

# Thread-safe global list for background thread logs
global_logs = []

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
    # Threshold on the LLM verifier's own confidence_score (agentic/models.py's
    # IncidentVerdict) — separate from the DETR detection threshold above. A DETR
    # trigger + is_accident=True is not enough to dispatch on its own; the verifier
    # must also be at least this confident, or the dispatch is treated as a false
    # positive (see agentic/agents.py::run_incident_response).
    st.session_state.verification_confidence = 0.80
if "frame_skip" not in st.session_state:
    st.session_state.frame_skip = 3
if "feeds" not in st.session_state:
    st.session_state.feeds = [
        {
            "id": 1,
            "name": "Camera 1 (Main)",
            "source_type": "Video File",
            "video_path": None,
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

# Pre-warm detector model immediately on application load (loader lives in ui/utils.py)
detector = load_incident_detector()

# ==================== WEB APP TOP TITLE ====================
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

# ==================== THREE-COLUMN LAYOUT ====================
col_control, col_video, col_logs = st.columns([3, 6, 3])

# ----------------- COLUMN 1: CONTROL SIDE PANEL -----------------
# Everything lives in tabs inside a single card, instead of three stacked
# cards each showing all their content at once — that was pushing the whole
# page well past viewport height, forcing a scroll just to reach the AI
# settings and Start Stream button. Only one tab's content is visible at a
# time, so the panel's height is bounded by its tallest single tab, not the
# sum of all three.
with col_control:
    # Control Panel Title
    render_html(SIDEBAR_HEADER_HTML)

    with st.container(border=True):
        tab_cameras, tab_contacts, tab_ai = st.tabs(["📹 Cameras", "🚨 Contacts", "🧠 AI Settings"])

        # 1. Camera Feeds Group
        with tab_cameras:
            # Render each feed config
            for i, feed in enumerate(st.session_state.feeds):
                with st.expander(f"📹 {feed['name']}", expanded=(i == len(st.session_state.feeds) - 1)):
                    feed['name'] = st.text_input("Feed Name", value=feed['name'], key=f"feed_name_{feed['id']}")
                    feed['source_type'] = st.selectbox(
                        "Source Type",
                        options=["Video File", "Network Camera (RTSP/HTTP)", "USB Local Stream"],
                        index=["Video File", "Network Camera (RTSP/HTTP)", "USB Local Stream"].index(feed['source_type']),
                        key=f"feed_src_type_{feed['id']}"
                    )

                    if feed['source_type'] == "Video File":
                        file_key = f"last_uploaded_file_{feed['id']}"
                        uploaded_file = st.file_uploader(
                            "Upload Video File",
                            type=["mp4", "avi", "mov", "mkv"],
                            key=f"feed_upload_{feed['id']}",
                            label_visibility="collapsed"
                        )
                        if uploaded_file is not None:
                            if file_key not in st.session_state or st.session_state[file_key] != uploaded_file.name:
                                if feed["video_path"] and os.path.exists(feed["video_path"]):
                                    try:
                                        os.remove(feed["video_path"])
                                    except Exception:
                                        pass
                                tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                                tfile.write(uploaded_file.read())
                                feed["video_path"] = tfile.name
                                st.session_state[file_key] = uploaded_file.name
                        else:
                            feed["video_path"] = None
                            if file_key in st.session_state:
                                del st.session_state[file_key]

                        if feed["video_path"] is None:
                            st.info("Upload video to start feed.")

                    elif feed['source_type'] == "Network Camera (RTSP/HTTP)":
                        feed['stream_url'] = st.text_input(
                            "Camera Stream URL",
                            value=feed['stream_url'],
                            placeholder="rtsp://user:pass@ip:port/stream  or  http://ip:port/video",
                            key=f"feed_stream_url_{feed['id']}",
                            label_visibility="collapsed"
                        )
                        st.caption("Accepts RTSP streams (e.g. rtsp://...) or HTTP/MJPEG streams (e.g. http://... or https://...).")

                    elif feed['source_type'] == "USB Local Stream":
                        feed['webcam_idx'] = st.number_input(
                            "Webcam Index",
                            min_value=0,
                            max_value=10,
                            value=feed['webcam_idx'],
                            step=1,
                            key=f"feed_webcam_{feed['id']}",
                            label_visibility="collapsed"
                        )

                    col_act_lbl, col_act_val = st.columns([7, 3])
                    with col_act_lbl:
                        st.markdown('<span class="text-body-sm text-on-surface-variant block pt-1">Active</span>', unsafe_allow_html=True)
                    with col_act_val:
                        feed['active'] = st.toggle("Active", value=feed['active'], key=f"feed_active_{feed['id']}", label_visibility="collapsed")

                    if len(st.session_state.feeds) > 1:
                        with st.container(key=f"feed-remove-{feed['id']}"):
                            if st.button("🗑️ Remove Feed", key=f"feed_remove_{feed['id']}", use_container_width=True):
                                if feed['video_path'] and os.path.exists(feed['video_path']):
                                    try:
                                        os.remove(feed['video_path'])
                                    except Exception:
                                        pass
                                st.session_state.feeds = [f for f in st.session_state.feeds if f['id'] != feed['id']]
                                st.rerun()

            if len(st.session_state.feeds) < 5:
                if st.button("➕ Add Camera Feed", use_container_width=True):
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

        # 2. Emergency Contacts Group
        with tab_contacts:
            st.markdown('<label class="text-body-sm text-on-surface-variant block mb-1">Phone Numbers (comma separated)</label>', unsafe_allow_html=True)
            phone_numbers_input = st.text_input(
                "Emergency Phone Numbers",
                value=st.session_state.phone_numbers,
                placeholder="e.g. 0540552725, 0244123456",
                key="emergency_phone_numbers_input",
                label_visibility="collapsed"
            )
            if phone_numbers_input != st.session_state.phone_numbers:
                st.session_state.phone_numbers = phone_numbers_input
                try:
                    with open(PHONE_NUMBERS_FILE, "w") as f:
                        f.write(phone_numbers_input)
                except Exception as e:
                    st.error(f"Error saving phone numbers: {e}")

        # 3. AI Analytics Settings Group
        with tab_ai:
            # Real-time Detection toggle
            col_lbl, col_tgl = st.columns([7, 3])
            with col_lbl:
                st.markdown('<span class="text-body-sm text-on-surface-variant block pt-1">Real-time Detection</span>', unsafe_allow_html=True)
            with col_tgl:
                run_ai = st.toggle("Real-time Detection", value=True, label_visibility="collapsed")

            # Detection Confidence Threshold slider — gates DETR: which frames get
            # sent to the LLM verifier at all.
            col_l, col_r = st.columns([7, 3])
            with col_l:
                st.markdown('<label class="text-body-sm text-on-surface-variant">Detection Confidence Threshold</label>', unsafe_allow_html=True)
            with col_r:
                st.markdown(f'<span class="text-label-mono font-label-mono text-primary float-right">{st.session_state.confidence:.2f}</span>', unsafe_allow_html=True)
            confidence_thresh = st.slider(
                "Detection Confidence Threshold",
                min_value=0.10,
                max_value=1.00,
                value=st.session_state.confidence,
                step=0.05,
                label_visibility="collapsed"
            )
            st.session_state.confidence = confidence_thresh

            # Verification Confidence Threshold slider — gates dispatch: even when
            # the LLM verifier says is_accident=True, its own confidence_score must
            # also clear this bar before an SMS/voice alert actually goes out.
            col_l, col_r = st.columns([7, 3])
            with col_l:
                st.markdown('<label class="text-body-sm text-on-surface-variant">Verification Confidence Threshold</label>', unsafe_allow_html=True)
            with col_r:
                st.markdown(f'<span class="text-label-mono font-label-mono text-primary float-right">{st.session_state.verification_confidence:.2f}</span>', unsafe_allow_html=True)
            verification_confidence_thresh = st.slider(
                "Verification Confidence Threshold",
                min_value=0.10,
                max_value=1.00,
                value=st.session_state.verification_confidence,
                step=0.05,
                label_visibility="collapsed"
            )
            st.session_state.verification_confidence = verification_confidence_thresh

            # AI Frame Skip slider
            col_l, col_r = st.columns([7, 3])
            with col_l:
                st.markdown('<label class="text-body-sm text-on-surface-variant">AI Frame Skip</label>', unsafe_allow_html=True)
            with col_r:
                st.markdown(f'<span class="text-label-mono font-label-mono text-primary float-right">{st.session_state.frame_skip}</span>', unsafe_allow_html=True)
            frame_skip = st.slider(
                "AI Frame Skip",
                min_value=1,
                max_value=10,
                value=3,
                step=1,
                label_visibility="collapsed"
            )
            st.session_state.frame_skip = frame_skip

            # Loop options (only when using Video source)
            has_video_source = any(f['source_type'] == "Video File" and f['active'] for f in st.session_state.feeds)
            loop_video = True
            if has_video_source:
                loop_video = st.toggle("Loop Video Playback", value=True)

        # Start/Stop Action Buttons — always visible below the tabs, not
        # tucked inside the AI Settings tab, since it's the primary action
        st.markdown('<div class="border-t border-outline-variant/30" style="margin: 4px 0 12px;"></div>', unsafe_allow_html=True)
        if not st.session_state.streaming:
            if st.button("▶️ Start Stream", use_container_width=True, type="primary"):
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
            with st.container(key="stop-stream-btn"):
                if st.button("⏹️ Stop Stream", use_container_width=True, type="secondary"):
                    st.session_state.streaming = False
                    st.rerun()

# ----------------- COLUMN 2: VIDEO SURVEILLANCE PANEL -----------------
with col_video:
    # 1. System Metrics HUD
    status_text = "Active" if st.session_state.streaming else "Idle"
    status_color = "#4edea3" if st.session_state.streaming else "#6b7a80"
    status_animate = "animate-pulse" if st.session_state.streaming else ""
    status_shadow = "box-shadow: 0 0 8px rgba(78,222,163,0.6);" if st.session_state.streaming else ""

    active_feeds = [f for f in st.session_state.feeds if f['active']]
    source_display = f"{len(active_feeds)} Active Feeds" if st.session_state.streaming else "Idle"
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
    render_html(metrics_html)

    # 2. Live Feed Monitor Container
    if run_ai:
        ai_badge_bg, ai_badge_color, ai_badge_border = "bg-secondary/10", "text-secondary", "border-secondary/20"
        ai_dot_bg, ai_dot_animate, ai_status_text = "bg-secondary", "animate-pulse", "ON"
    else:
        ai_badge_bg, ai_badge_color, ai_badge_border = "bg-surface-container-highest", "text-on-surface-variant", "border-outline-variant"
        ai_dot_bg, ai_dot_animate, ai_status_text = "bg-on-surface-variant", "", "OFF"

    live_feed_header_html = LIVE_FEED_HEADER_TEMPLATE.format(
        ai_badge_bg=ai_badge_bg,
        ai_badge_color=ai_badge_color,
        ai_badge_border=ai_badge_border,
        ai_dot_bg=ai_dot_bg,
        ai_dot_animate=ai_dot_animate,
        ai_status_text=ai_status_text
    )
    render_html(live_feed_header_html)

    # Default placeholder when idle
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
        threshold_display=f"{confidence_thresh:.2f}"
    )
    render_html(live_feed_footer_html)

# ----------------- COLUMN 3: INCIDENT LOGS & SESSION STATS -----------------
with col_logs:
    # Incident Log Box
    log_placeholder = st.empty()

    # Session Stats Card
    stats_placeholder = st.empty()

# ==================== LIVE SURVEILLANCE LOOP ====================
if st.session_state.streaming:
    # 1. Open all active caps (ui/utils.py owns the actual cv2.VideoCapture setup)
    caps, failed_feed_names = open_video_captures(active_feeds)
    for failed_name in failed_feed_names:
        st.error(f"Failed to open video source for {failed_name}")

    if not caps:
        st.error("No camera feeds could be opened. Please check inputs and try again.")
        st.session_state.streaming = False
        st.rerun()
    else:
        # Loop parameters
        prev_time = time.time()
        # This DETR checkpoint's preprocessor always upscales to a fixed
        # 800px input internally regardless of what we feed it, so its
        # per-frame cost is fixed: ~3s/frame on CPU, ~0.4s/frame (~2.4fps)
        # on the MX250 GPU (CUDA) or Apple Silicon (MPS). Either way, running
        # display at full 30fps would let the on-screen boxes drift out of
        # sync with what's on screen by the time each detection completes.
        # Pace display to the model's real cadence when AI is on so the
        # overlay stays visually in sync; go full speed when it's off.
        using_gpu = detector is not None and detector.device.type in ("cuda", "mps")
        ai_cadence_dt = 0.42 if using_gpu else (1.0 / 3.0)
        target_dt = ai_cadence_dt if (run_ai and detector is not None) else (1.0 / 30.0)

        # ---- Background AI inference worker (ui/utils.py::run_detection_worker) ----
        # DETR on CPU is far too slow to run synchronously in the render
        # loop (it would gate display fps to model latency). Instead, a
        # single background thread continuously detects on whatever the
        # latest frame is for each feed, dropping frames it can't keep up
        # with. The render loop never waits on it — it just draws the most
        # recently completed detections, so display fps is bounded by
        # frame decode/render speed, not inference speed.
        inference_state = {"latest_frames": {}, "predictions": {}}
        inference_stop_event = threading.Event()

        detection_thread = threading.Thread(
            target=run_detection_worker,
            args=(inference_state, run_ai, detector, inference_stop_event, frame_skip),
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
                    if feed['source_type'] == "Video File" and loop_video:
                        # Loop video source if enabled
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = cap.read()
                    elif feed['source_type'] == "Network Camera (RTSP/HTTP)":
                        # Some IP cameras (e.g. webcamXP-style servers) only ever serve a
                        # single JPEG snapshot per HTTP request rather than a continuous
                        # multipart stream — FFMPEG reads exactly one frame from those and
                        # then reports EOF. Re-opening re-polls the URL for a fresh frame,
                        # which also naturally recovers from a transient network drop on a
                        # true streaming source (RTSP or multipart MJPEG).
                        cap.release()
                        cap = cv2.VideoCapture(feed['stream_url'], cv2.CAP_FFMPEG)
                        caps[cap_idx][1] = cap
                        ret, frame = cap.read()

                if not ret:
                    continue

                any_frame_read = True

                # Resize frame to fit grid nicely
                height, width = frame.shape[:2]
                max_w = 480 if len(active_feeds) > 1 else 960
                if width > max_w:
                    ratio = max_w / float(width)
                    frame = cv2.resize(frame, (max_w, int(height * ratio)))

                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Hand the current frame to the background inference worker
                # and grab whatever detections it has completed so far.
                # Never blocks on the model.
                if run_ai and detector is not None:
                    inference_state["latest_frames"][feed['id']] = frame_rgb.copy()
                    preds = [
                        d for d in inference_state["predictions"].get(feed['id'], [])
                        if d["score"] >= confidence_thresh
                    ]
                else:
                    preds = []

                # Draw AI Detections
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
                        color = (239, 68, 68)  # Red for Accidents
                        label_text = f"ACCIDENT {score:.2f}"
                        if score > highest_accident_score:
                            highest_accident_score = score
                    else:
                        color = (76, 215, 246)  # Light cyan for other elements
                        label_text = f"{label.upper()} {score:.2f}"

                    # Draw bounding box
                    cv2.rectangle(frame_rgb, (xmin, ymin), (xmax, ymax), color, 2)
                    # Bounding label background
                    (tw, th), base = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                    cv2.rectangle(frame_rgb, (xmin, ymin - th - 8), (xmin + tw + 10, ymin), color, -1)
                    # Text overlay
                    text_color = (0, 56, 36) if not is_accident else (255, 255, 255)
                    cv2.putText(frame_rgb, label_text, (xmin + 5, ymin - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, text_color, 1, cv2.LINE_AA)

                # Update global state alert
                if active_alert_in_any_feed:
                    st.session_state.active_incident = True

                # Log to incident console and trigger Agent response
                if active_alert_in_feed:
                    curr_t = time.time()
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

                    # Trigger agent with 60s cooldown per camera feed
                    last_agent_t = st.session_state.last_agent_alert_times.get(feed['id'], 0.0)
                    if (curr_t - last_agent_t) > 60.0:
                        st.session_state.last_agent_alert_times[feed['id']] = curr_t
                        
                        # Add log about triggering dispatch
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        st.session_state.incident_logs.insert(0, {
                            "time": timestamp,
                            "type": f"AGENT ACTIVATE - VERIFYING...",
                            "confidence": f"{highest_accident_score * 100:.1f}%",
                            "color_class": "text-yellow-400 font-bold"
                        })

                        # Encode frame to base64 for multimodal agent visual processing
                        import base64
                        try:
                            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                            _, buffer = cv2.imencode('.jpg', frame_bgr)
                            img_base64 = base64.b64encode(buffer).decode('utf-8')
                        except Exception:
                            img_base64 = None

                        # Parsed/read here (main thread) rather than inside
                        # trigger_agent_dispatch — st.session_state isn't safe to
                        # read from a background thread.
                        dispatch_contacts = parse_phone_numbers(st.session_state.phone_numbers)
                        dispatch_verification_threshold = st.session_state.verification_confidence

                        # Dispatch thread — trigger_agent_dispatch (ui/utils.py) verifies
                        # and dispatches; it appends results to global_logs rather than
                        # touching st.session_state directly from this background thread.
                        dispatch_thread = threading.Thread(
                            target=trigger_agent_dispatch,
                            args=(feed['name'], f"Intersection monitored by {feed['name']}", highest_accident_score * 100, img_base64, dispatch_contacts, dispatch_verification_threshold, global_logs)
                        )
                        dispatch_thread.daemon = True
                        dispatch_thread.start()

                # Render frame in its placeholder
                if feed['id'] in placeholders:
                    placeholders[feed['id']].image(frame_rgb, channels="RGB", use_container_width=True)

            if not any_frame_read:
                break

            st.session_state.frame_count += 1
            st.session_state.active_incident = active_alert_in_any_feed

            # Drain global logs (from background threads) safely into session state
            while len(global_logs) > 0:
                log_item = global_logs.pop(0)
                st.session_state.incident_logs.insert(0, log_item)

            # Calculate live FPS
            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time)
            prev_time = curr_time
            st.session_state.fps = 0.9 * st.session_state.fps + 0.1 * fps if st.session_state.fps > 0 else fps

            # Format and update logs HTML
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

            # Update Session Summary — every number here is derived from what the
            # pipeline actually did this session, not simulated/placeholder data.
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

            # Pace display to ~30fps instead of running full-tilt (only
            # relevant for video files now that inference no longer gates
            # this loop; live camera/RTSP reads already self-pace).
            elapsed = time.time() - loop_start
            time.sleep(max(0.0, target_dt - elapsed))

        # Stop the background inference worker and release all caps
        inference_stop_event.set()
        detection_thread.join(timeout=1.0)
        for feed, cap in caps:
            cap.release()

        # Reset streaming state
        st.session_state.streaming = False
        st.rerun()

# Default Side Panels rendering when not streaming
if not st.session_state.streaming:
    log_placeholder.markdown(clean_html(DEFAULT_LOG_CONSOLE_HTML), unsafe_allow_html=True)
    stats_placeholder.markdown(clean_html(DEFAULT_STATS_CARD_HTML), unsafe_allow_html=True)
