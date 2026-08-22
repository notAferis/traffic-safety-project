"""
data_collection.py
------------------
Real-time Data Collection & Logging Pipeline using SQLite in WAL mode
with an asynchronous in-memory event queue.

Manages offline detection logging, snapshot storage, deduplication, human-in-the-loop (HITL)
admin review workflows, and dataset export for active model retraining.
"""

import os
import sqlite3
import time
import queue
import threading
import json
import zipfile
from datetime import datetime
from pathlib import Path
import numpy as np
from PIL import Image

# Directory setup
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "collection"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
DB_PATH = DATA_DIR / "detections.db"

# Thread-safe event queue for real-time non-blocking writes
_event_queue = queue.Queue()
_writer_thread = None
_stop_event = threading.Event()

# In-memory frame cache for real-time visual deduplication
_last_feed_frame_cache = {}


def is_duplicate_frame(frame_rgb, feed_id: int, mad_threshold: float = 12.0) -> bool:
    """
    Perceptual visual similarity check using downsampled grayscale Mean Absolute Difference.
    Returns True if the current frame is perceptually identical (MAD < 12.0) to the
    last captured snapshot for this feed, avoiding collecting duplicate frames.
    """
    try:
        import cv2
        gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
        small = cv2.resize(gray, (64, 64), interpolation=cv2.INTER_AREA).astype(np.float32)

        prev = _last_feed_frame_cache.get(feed_id)
        if prev is not None:
            mad = float(np.mean(np.abs(small - prev)))
            if mad < mad_threshold:
                return True

        _last_feed_frame_cache[feed_id] = small
        return False
    except Exception:
        return False


def init_data_collection():
    """Initializes local storage directories, SQLite database in WAL mode, and worker thread."""
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Enable WAL mode for ultra-fast non-blocking concurrent writes & reads
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detection_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            feed_name TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            confidence_category TEXT NOT NULL,
            image_path TEXT NOT NULL,
            vlm_verdict TEXT DEFAULT 'NOT_RUN',
            vlm_confidence REAL DEFAULT 0.0,
            review_status TEXT NOT NULL,
            reviewer_notes TEXT DEFAULT '',
            reviewed_at TEXT DEFAULT '',
            predicted_label TEXT DEFAULT 'accident',
            corrected_label TEXT DEFAULT 'accident',
            bounding_boxes TEXT DEFAULT '[]'
        )
    """)

    # Schema migration checks for existing databases
    for col_def in [
        ("predicted_label", "TEXT DEFAULT 'accident'"),
        ("corrected_label", "TEXT DEFAULT 'accident'"),
        ("bounding_boxes", "TEXT DEFAULT '[]'")
    ]:
        try:
            cursor.execute(f"ALTER TABLE detection_logs ADD COLUMN {col_def[0]} {col_def[1]};")
        except Exception:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verification_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            feed_name TEXT NOT NULL,
            location_info TEXT NOT NULL,
            detr_confidence REAL NOT NULL,
            vlm_confidence REAL NOT NULL,
            is_accident INTEGER NOT NULL,
            dispatch_status TEXT NOT NULL,
            verifier_model TEXT NOT NULL,
            image_path TEXT NOT NULL,
            vlm_response_json TEXT NOT NULL,
            vehicles_involved TEXT DEFAULT '',
            damage_and_hazards TEXT DEFAULT '',
            road_blockage_status TEXT DEFAULT '',
            sms_report TEXT DEFAULT '',
            observations TEXT DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()

    # Start background database writer thread if not already running
    global _writer_thread, _stop_event
    if _writer_thread is None or not _writer_thread.is_alive():
        _stop_event.clear()
        _writer_thread = threading.Thread(target=_db_writer_worker, daemon=True)
        _writer_thread.start()


def _db_writer_worker():
    """Background worker thread that drains the event queue into SQLite WAL transactions."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    while not _stop_event.is_set() or not _event_queue.empty():
        try:
            event = _event_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        try:
            boxes_json = json.dumps(event.get("bounding_boxes", []))
            cursor.execute("""
                INSERT INTO detection_logs (
                    timestamp, feed_name, confidence_score, confidence_category,
                    image_path, vlm_verdict, vlm_confidence, review_status,
                    predicted_label, corrected_label, bounding_boxes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event["timestamp"],
                event["feed_name"],
                event["confidence_score"],
                event["confidence_category"],
                event["image_path"],
                event.get("vlm_verdict", "NOT_RUN"),
                event.get("vlm_confidence", 0.0),
                event["review_status"],
                event.get("predicted_label", "accident"),
                event.get("corrected_label", "accident"),
                boxes_json,
            ))
            conn.commit()
        except Exception as e:
            print(f"[DataCollection] DB write error: {e}")
        finally:
            _event_queue.task_done()

    conn.close()


def save_snapshot_image(image_rgb_or_bgr, filename_prefix="frame", annotated_image=None) -> str:
    """
    Saves frame numpy array, PIL Image, or Base64 string to PNG snapshot file.
    If annotated_image is provided, saves an additional '_annotated.png' file alongside it.
    Returns relative path to clean snapshot image.
    """
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    t_stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
    filename = f"{filename_prefix}_{t_stamp}"
    full_clean_path = SNAPSHOT_DIR / f"{filename}.png"

    try:
        import cv2
        import base64
        from io import BytesIO

        def _write_img(img_obj, target_path):
            if isinstance(img_obj, str) and len(img_obj) > 50:
                img_bytes = base64.b64decode(img_obj)
                img = Image.open(BytesIO(img_bytes))
                img.save(target_path, "PNG")
            elif hasattr(img_obj, "shape"): # numpy array
                bgr = cv2.cvtColor(img_obj, cv2.COLOR_RGB2BGR)
                cv2.imwrite(str(target_path), bgr)
            elif isinstance(img_obj, Image.Image):
                img_obj.save(target_path, "PNG")

        _write_img(image_rgb_or_bgr, full_clean_path)

        if annotated_image is not None:
            full_annotated_path = SNAPSHOT_DIR / f"{filename}_annotated.png"
            _write_img(annotated_image, full_annotated_path)

        return f"data/collection/snapshots/{filename}.png"
    except Exception as e:
        print(f"[DataCollection] Image save error: {e}")
        return ""


def log_verification_record(
    feed_name: str,
    location_info: str,
    detr_confidence: float,
    vlm_verdict_dict: dict,
    dispatch_status: str,
    verifier_model: str,
    image_input=None,
    annotated_image_input=None,
) -> int:
    """
    Saves a verification record into the SQLite database.
    """
    init_data_collection()
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save clean frame snapshot and optional annotated frame snapshot
    image_path = ""
    if image_input is not None:
        clean_prefix = feed_name.replace(" ", "_").replace("(", "").replace(")", "")
        image_path = save_snapshot_image(
            image_input,
            filename_prefix=f"verif_{clean_prefix}",
            annotated_image=annotated_image_input
        )

    is_accident_val = 1 if vlm_verdict_dict.get("is_accident", False) else 0
    vlm_conf = float(vlm_verdict_dict.get("confidence_score", 0.0))
    vlm_json_str = json.dumps(vlm_verdict_dict, indent=2)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO verification_records (
            timestamp, feed_name, location_info, detr_confidence, vlm_confidence,
            is_accident, dispatch_status, verifier_model, image_path, vlm_response_json,
            vehicles_involved, damage_and_hazards, road_blockage_status, sms_report, observations
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        feed_name,
        location_info,
        float(detr_confidence),
        vlm_conf,
        is_accident_val,
        dispatch_status,
        verifier_model,
        image_path,
        vlm_json_str,
        vlm_verdict_dict.get("vehicles_involved", ""),
        vlm_verdict_dict.get("damage_and_hazards", ""),
        vlm_verdict_dict.get("road_blockage_status", ""),
        vlm_verdict_dict.get("sms_report", ""),
        vlm_verdict_dict.get("observations", "")
    ))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id


def get_verification_history(limit: int = 100, accident_only: bool = False, feed_filter: str = "All"):
    """Fetches past verification records for UI display."""
    init_data_collection()
    if not DB_PATH.exists():
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM verification_records"
    conditions = []
    params = []

    if accident_only:
        conditions.append("is_accident = 1")
    if feed_filter and feed_filter != "All":
        conditions.append("feed_name = ?")
        params.append(feed_filter)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    try:
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
    except Exception as ex:
        print(f"[DataCollection] History fetch error: {ex}")
        rows = []

    conn.close()
    return rows


def get_verification_analytics():
    """Calculates summary statistics and time series data for verified detections."""
    init_data_collection()
    if not DB_PATH.exists():
        return {
            "total": 0,
            "accidents": 0,
            "false_positives": 0,
            "filter_rate": 0.0,
            "false_positive_rate": 0.0,
            "time_series": []
        }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM verification_records")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM verification_records WHERE is_accident = 1")
    accidents = cursor.fetchone()[0]

    false_positives = total - accidents
    filter_rate = (false_positives / total * 100.0) if total > 0 else 0.0

    # Hourly distribution of verifications
    cursor.execute("""
        SELECT strftime('%H:00', timestamp) as hour,
               SUM(CASE WHEN is_accident = 1 THEN 1 ELSE 0 END) as accidents,
               SUM(CASE WHEN is_accident = 0 THEN 1 ELSE 0 END) as filtered
        FROM verification_records
        GROUP BY hour
        ORDER BY hour ASC
    """)
    time_series = [{"time": r[0], "Accidents": r[1], "Filtered": r[2]} for r in cursor.fetchall()]

    conn.close()
    return {
        "total": total,
        "accidents": accidents,
        "false_positives": false_positives,
        "filter_rate": filter_rate,
        "false_positive_rate": filter_rate,
        "time_series": time_series
    }


def enqueue_detection(
    feed_name: str,
    confidence_score: float,
    image_path: str,
    review_thresh: float = 0.80,
    vlm_verdict: str = "NOT_RUN",
    vlm_confidence: float = 0.0,
    predicted_label: str = "accident",
    corrected_label: str = "accident",
    bounding_boxes: list = None,
):
    """Enqueues a detection event with predicted label and bounding boxes for non-blocking persistence."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if confidence_score <= review_thresh:
        category = "LOW"
        review_status = "PENDING_REVIEW"
    else:
        category = "HIGH"
        review_status = "AUTO_APPROVED"

    event = {
        "timestamp": timestamp,
        "feed_name": feed_name,
        "confidence_score": float(confidence_score),
        "confidence_category": category,
        "image_path": image_path,
        "vlm_verdict": vlm_verdict,
        "vlm_confidence": float(vlm_confidence),
        "review_status": review_status,
        "predicted_label": predicted_label,
        "corrected_label": corrected_label,
        "bounding_boxes": bounding_boxes or []
    }
    _event_queue.put(event)
    return review_status


def get_pending_reviews(limit: int = 50):
    """Fetches queued detections marked as PENDING_REVIEW for admin dashboard inspection."""
    if not DB_PATH.exists():
        return []
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM detection_logs
        WHERE review_status = 'PENDING_REVIEW'
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def update_review_status(record_id: int, new_status: str, corrected_label: str = None, notes: str = ""):
    """Updates the review status and ground-truth corrected label of a detection record."""
    if not DB_PATH.exists():
        return
    
    reviewed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if corrected_label:
        cursor.execute("""
            UPDATE detection_logs
            SET review_status = ?, corrected_label = ?, reviewer_notes = ?, reviewed_at = ?
            WHERE id = ?
        """, (new_status, corrected_label, notes, reviewed_at, record_id))
    else:
        cursor.execute("""
            UPDATE detection_logs
            SET review_status = ?, reviewer_notes = ?, reviewed_at = ?
            WHERE id = ?
        """, (new_status, notes, reviewed_at, record_id))
    conn.commit()
    conn.close()


def delete_detection_record(record_id: int, delete_files: bool = True):
    """Deletes a detection record from SQLite and removes its snapshot image files from disk."""
    if not DB_PATH.exists():
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT image_path FROM detection_logs WHERE id = ?", (record_id,))
    row = cursor.fetchone()

    if row and delete_files:
        img_rel = row[0]
        if img_rel:
            clean_p = BASE_DIR / img_rel
            ann_p = BASE_DIR / img_rel.replace(".png", "_annotated.png")
            try:
                if clean_p.exists():
                    clean_p.unlink()
                if ann_p.exists():
                    ann_p.unlink()
            except Exception as e:
                print(f"[DataCollection] File deletion error: {e}")

    cursor.execute("DELETE FROM detection_logs WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()


def get_collection_stats():
    """Returns database summary statistics for the admin dashboard."""
    if not DB_PATH.exists():
        return {"total": 0, "pending": 0, "confirmed": 0, "relabeled_vehicle": 0, "rejected": 0, "auto": 0}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM detection_logs")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM detection_logs WHERE review_status = 'PENDING_REVIEW'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM detection_logs WHERE review_status = 'CONFIRMED_ACCIDENT'")
    confirmed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM detection_logs WHERE review_status = 'RELABELED_VEHICLE' OR (review_status = 'REJECTED_FALSE_POSITIVE' AND corrected_label = 'vehicle')")
    relabeled_vehicle = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM detection_logs WHERE review_status = 'REJECTED_FALSE_POSITIVE' AND (corrected_label != 'vehicle' OR corrected_label IS NULL)")
    rejected = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM detection_logs WHERE review_status = 'AUTO_APPROVED'")
    auto = cursor.fetchone()[0]

    conn.close()
    return {
        "total": total,
        "pending": pending,
        "confirmed": confirmed,
        "relabeled_vehicle": relabeled_vehicle,
        "rejected": rejected,
        "auto": auto
    }


def export_dataset_zip() -> str:
    """
    Packages all reviewed detections and snapshot images into a downloadable ZIP archive
    with JSON manifest and YOLO annotations for model fine-tuning.
    Class 0: accident
    Class 1: vehicle
    """
    if not DB_PATH.exists():
        return ""
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detection_logs WHERE review_status != 'PENDING_REVIEW'")
    records = [dict(r) for r in cursor.fetchall()]
    conn.close()

    export_dir = DATA_DIR / "exports"
    os.makedirs(export_dir, exist_ok=True)
    zip_path = export_dir / f"dataset_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Write JSON manifest
        manifest_data = json.dumps(records, indent=2)
        zipf.writestr("dataset_manifest.json", manifest_data)
        zipf.writestr("classes.txt", "accident\nvehicle\n")

        # Include snapshot images and YOLO format label .txt files
        for r in records:
            img_rel = r.get("image_path", "")
            if img_rel:
                full_img_path = BASE_DIR / img_rel
                if full_img_path.exists():
                    zipf.write(full_img_path, arcname=f"images/{full_img_path.name}")
                    
                    # Create YOLO annotation file
                    label_filename = full_img_path.stem + ".txt"
                    
                    # Map corrected_label to class ID
                    corr_label = (r.get("corrected_label") or "accident").lower()
                    if "vehicle" in corr_label:
                        class_id = 1
                    elif "accident" in corr_label:
                        class_id = 0
                    else:
                        class_id = None

                    # If bounding boxes exist, format as normalized YOLO box (class_id x_center y_center width height)
                    try:
                        boxes = json.loads(r.get("bounding_boxes", "[]"))
                        lines = []
                        if class_id is not None and boxes:
                            with Image.open(full_img_path) as im:
                                w_img, h_img = im.size
                            for b in boxes:
                                b_data = b.get("box", {})
                                xmin = b_data.get("xmin", 0)
                                ymin = b_data.get("ymin", 0)
                                xmax = b_data.get("xmax", 0)
                                ymax = b_data.get("ymax", 0)
                                bw = (xmax - xmin) / float(w_img)
                                bh = (ymax - ymin) / float(h_img)
                                xc = (xmin + xmax) / 2.0 / float(w_img)
                                yc = (ymin + ymax) / 2.0 / float(h_img)
                                lines.append(f"{class_id} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")
                        
                        yolo_content = "\n".join(lines)
                        zipf.writestr(f"labels/{label_filename}", yolo_content)
                    except Exception:
                        pass

    return str(zip_path)
