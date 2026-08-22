
import os
import queue
import threading
import time
from datetime import datetime

import cv2
import streamlit as st
from PIL import Image


@st.cache_resource(show_spinner="Loading AI Incident Detection Model (RT-DETR)...")
def load_incident_detector():
    try:
        import torch
        from transformers import (
            AutoImageProcessor,
            AutoModelForObjectDetection,
            pipeline,
            logging as tf_logging,
        )
        tf_logging.set_verbosity_error()
        force_cpu = os.getenv("FORCE_CPU", "").strip().lower() in ("1", "true", "yes")
        if force_cpu:
            device = -1
        elif torch.cuda.is_available():
            device = 0
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = -1

        model_name = "dri11heaD/accident-detection-model"
        model = AutoModelForObjectDetection.from_pretrained(model_name)

        try:
            image_processor = AutoImageProcessor.from_pretrained(model_name)
        except Exception:
            # Fallback for RT-DETR-v2 models uploaded without preprocessor_config.json
            image_processor = AutoImageProcessor.from_pretrained("PekingU/rtdetr_r50vd")

        detector = pipeline(
            "object-detection",
            model=model,
            image_processor=image_processor,
            device=device
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
            path = feed.get('video_path') or ""
            if not path:
                failed_feed_names.append(feed['name'])
                continue
            cap = cv2.VideoCapture(path)
        elif feed['source_type'] == "Network Camera (RTSP/HTTP)":
            url = feed.get('stream_url') or ""
            if not url:
                failed_feed_names.append(feed['name'])
                continue
            # Force the FFMPEG backend explicitly for network streams (RTSP or
            # HTTP/MJPEG) — OpenCV's auto-detected backend isn't always FFMPEG,
            # and FFMPEG is the backend this build actually supports both
            # protocols through.
            cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
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
    feed_name, location_info, confidence_val, image_base64_data, contacts, verification_threshold, global_logs, verifier_model="qwen", annotated_base64_data=None
):
    """
    Runs in a background thread (see main.py) — verifies the flagged frame via
    the LLM and dispatches SMS/voice reports if confirmed. Appends a result entry to
    global_logs rather than touching st.session_state directly, since session_state
    isn't safe to write from a non-main thread; main.py drains global_logs into
    session_state on the main thread each render loop iteration.
    """
    try:
        from agentic.agents import run_incident_response
        from agentic.data_collection import log_verification_record

        alert_prompt = (
            f"Analyze the attached traffic camera feed from '{feed_name}' located at {location_info}. "
            f"The primary object detector flagged a candidate incident with {confidence_val:.1f}% confidence.\n"
            f"Inspect the image frame carefully for specific visual facts: vehicle types, vehicle colors, "
            f"collision contact points, structural damage severity, scattered debris, smoke/fire, and road blockage. "
            f"Generate a detailed, factual emergency SMS dispatch report describing what is visually observed."
        )
        agent_reply, verdict_dict, dispatch_status = run_incident_response(
            alert_prompt,
            location=location_info,
            image_base64=image_base64_data,
            contacts=contacts,
            verification_confidence_threshold=verification_threshold,
            verifier_model=verifier_model,
            return_details=True,
        )
        t_stamp = datetime.now().strftime("%H:%M:%S")

        # Persist verification snapshot, predictions, and model response schema to DB
        try:
            detr_float_score = float(confidence_val) / 100.0 if confidence_val > 1.0 else float(confidence_val)
            log_verification_record(
                feed_name=feed_name,
                location_info=location_info,
                detr_confidence=detr_float_score,
                vlm_verdict_dict=verdict_dict,
                dispatch_status=dispatch_status,
                verifier_model=verifier_model,
                image_input=image_base64_data,
                annotated_image_input=annotated_base64_data,
            )
        except Exception as db_err:
            print(f"[trigger_agent_dispatch] Failed to log verification record: {db_err}")

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


# ---------------------------------------------------------------------------
# Asynchronous Verification Queue System (Replaces Cooldown Timers)
# ---------------------------------------------------------------------------
_verification_queue = queue.Queue()
_verification_worker_thread = None
_verification_stop_event = threading.Event()

# Live settings dict — updated by the UI thread on every enqueue, read by the
# worker thread at processing time so settings changes take effect immediately.
_live_settings = {
    "verifier_model": "Qwen 3.5 VL (Local / Offline)",
    "verification_threshold": 0.80,
}
_live_settings_lock = threading.Lock()


def update_live_settings(verifier_model: str = None, verification_threshold: float = None):
    """Update live settings that the verification worker reads at job-processing time."""
    with _live_settings_lock:
        if verifier_model is not None:
            _live_settings["verifier_model"] = verifier_model
        if verification_threshold is not None:
            _live_settings["verification_threshold"] = verification_threshold


def init_verification_worker():
    """Initializes background worker thread to process queued VLM verification jobs sequentially."""
    global _verification_worker_thread, _verification_stop_event
    if _verification_worker_thread is None or not _verification_worker_thread.is_alive():
        _verification_stop_event.clear()
        _verification_worker_thread = threading.Thread(target=_verification_worker_loop, daemon=True)
        _verification_worker_thread.start()


def enqueue_verification_job(job_data: dict):
    """
    Enqueues a candidate incident frame for VLM verification.
    Also syncs the latest verifier_model and verification_threshold into
    the live settings so the worker always uses the most recent values.
    """
    # Sync live settings from whatever the caller passed (reflecting current session state)
    update_live_settings(
        verifier_model=job_data.get("verifier_model"),
        verification_threshold=job_data.get("verification_threshold"),
    )
    init_verification_worker()
    _verification_queue.put(job_data)


def _verification_worker_loop():
    """Background worker thread draining the verification queue into trigger_agent_dispatch."""
    while not _verification_stop_event.is_set():
        try:
            job = _verification_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        # Read the LIVE settings at processing time, not the stale snapshot
        # from when the job was enqueued — this ensures settings changes on
        # the AI Settings page take effect immediately for pending jobs.
        with _live_settings_lock:
            live_model = _live_settings["verifier_model"]
            live_threshold = _live_settings["verification_threshold"]

        try:
            trigger_agent_dispatch(
                feed_name=job["feed_name"],
                location_info=job["location_info"],
                confidence_val=job["confidence_val"],
                image_base64_data=job["image_base64_data"],
                contacts=job["contacts"],
                verification_threshold=live_threshold,
                global_logs=job["global_logs"],
                verifier_model=live_model,
                annotated_base64_data=job.get("annotated_base64_data")
            )
        except Exception as e:
            print(f"[VerificationQueue] Worker error: {e}")
        finally:
            _verification_queue.task_done()


