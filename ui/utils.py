
import os
import time
from datetime import datetime

import cv2
import streamlit as st
from PIL import Image


@st.cache_resource(show_spinner="Loading AI Incident Detection Model (DETR)...")
def load_incident_detector():
    try:
        import torch
        from transformers import pipeline
        force_cpu = os.getenv("FORCE_CPU", "").strip().lower() in ("1", "true", "yes")
        if force_cpu:
            device = -1
        elif torch.cuda.is_available():
            device = 0
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = -1
        detector = pipeline(
            "object-detection", model="hilmantm/detr-traffic-accident-detection", device=device
        )
        return detector
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None


def open_video_captures(active_feeds):
    """
    Opens a cv2.VideoCapture for each active feed.

    Returns (caps, failed_feed_names) — caps is a list of [feed, cap] pairs for
    sources that opened successfully; failed_feed_names lists the ones that didn't,
    for the caller to surface via st.error.
    """
    caps = []
    failed_feed_names = []
    for feed in active_feeds:
        if feed['source_type'] == "Video File":
            cap = cv2.VideoCapture(feed['video_path'])
        elif feed['source_type'] == "Network Camera (RTSP/HTTP)":
            # Force the FFMPEG backend explicitly for network streams (RTSP or
            # HTTP/MJPEG) — OpenCV's auto-detected backend isn't always FFMPEG,
            # and FFMPEG is the backend this build actually supports both
            # protocols through.
            cap = cv2.VideoCapture(feed['stream_url'], cv2.CAP_FFMPEG)
        else:
            cap = cv2.VideoCapture(feed['webcam_idx'])

        if cap.isOpened():
            caps.append([feed, cap])
        else:
            failed_feed_names.append(feed['name'])
    return caps, failed_feed_names


def run_detection_worker(inference_state, run_ai, detector, inference_stop_event, frame_skip):
    """
    DETR on CPU is far too slow to run synchronously in the render loop (it would
    gate display fps to model latency). Instead, this runs in a background thread,
    continuously detecting on whatever the latest frame is for each feed, dropping
    frames it can't keep up with. The render loop never waits on it — it just draws
    the most recently completed detections, so display fps is bounded by frame
    decode/render speed, not inference speed.
    """
    detect_max_w = 320
    while not inference_stop_event.is_set():
        if not (run_ai and detector is not None):
            time.sleep(0.1)
            continue
        for feed_id, frame in list(inference_state["latest_frames"].items()):
            if inference_stop_event.is_set():
                break
            h, w = frame.shape[:2]
            if w > detect_max_w:
                scale = w / float(detect_max_w)
                proc_frame = cv2.resize(frame, (detect_max_w, int(h / scale)))
            else:
                scale = 1.0
                proc_frame = frame
            try:
                detections = detector(Image.fromarray(proc_frame))
            except Exception:
                detections = []
            for d in detections:
                box = d["box"]
                box["xmin"] *= scale
                box["xmax"] *= scale
                box["ymin"] *= scale
                box["ymax"] *= scale
            inference_state["predictions"][feed_id] = detections
        time.sleep(frame_skip * 0.03)


def parse_phone_numbers(raw: str) -> list[str]:
    """Parses the dashboard's Contacts tab (comma-separated) into a clean list."""
    return [n.strip() for n in raw.split(",") if n.strip()] or ["0540552725"]


def trigger_agent_dispatch(
    feed_name, location_info, confidence_val, image_base64_data, contacts, verification_threshold, global_logs
):
    """
    Runs in a background thread (see main_v2.py) — verifies the flagged frame via
    the LLM and dispatches SMS/voice reports if confirmed. Appends a result entry to
    global_logs rather than touching st.session_state directly, since session_state
    isn't safe to write from a non-main thread; main_v2.py drains global_logs into
    session_state on the main thread each render loop iteration.
    """
    try:
        from agentic.agents import run_incident_response
        alert_prompt = (
            f"Emergency: A vehicle accident has been detected on '{feed_name}' "
            f"located at {location_info}. The AI model confidence score is {confidence_val:.1f}%. "
            f"Please immediately call and send SMS dispatch reports to notify emergency contacts."
        )
        agent_reply = run_incident_response(
            alert_prompt,
            location=location_info,
            image_base64=image_base64_data,
            contacts=contacts,
            verification_confidence_threshold=verification_threshold,
        )
        t_stamp = datetime.now().strftime("%H:%M:%S")

        is_false_positive = "false positive" in agent_reply.lower() or "no accident" in agent_reply.lower()

        if is_false_positive:
            global_logs.append({
                "time": t_stamp,
                "type": f"FALSE ALARM FILTERED: {feed_name}",
                "confidence": "Blocked",
                "color_class": "text-blue-400 font-bold"
            })
        else:
            global_logs.append({
                "time": t_stamp,
                "type": f"DISPATCH OK: {feed_name}",
                "confidence": "Sent",
                "color_class": "text-green-400"
            })
    except Exception as ex:
        t_stamp = datetime.now().strftime("%H:%M:%S")
        global_logs.append({
            "time": t_stamp,
            "type": f"DISPATCH ERROR: {ex}",
            "confidence": "Failed",
            "color_class": "text-red-400"
        })
