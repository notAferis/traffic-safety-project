# Project Progress Log

Running log of notable changes to the incident-detection/dispatch pipeline, for use in project
documentation. Newest entries at the top.

---

## 2026-08-22 — Upgraded to RT-DETR-v2, Built Modular Multi-Page UI, and Added Active HITL Visual Deduplication & Relabeling

**What changed:**

1. **Model Architecture Upgrade**:
   - Integrated fine-tuned RT-DETR-v2 (`dri11heaD/accident-detection-model`) replacing base DETR.
   - Added robust image processor fallback (`PekingU/rtdetr_r50vd`) when `preprocessor_config.json` is missing in the repository.
   - Configured multi-class mapping (`0: accident`, `1: vehicle`).

2. **Modular Multi-Page Tabbed UI Architecture**:
   - Refactored `ui/main.py` using Streamlit's official `st.navigation` and `st.Page` routing.
   - Created clean modular pages under `ui/pages/`:
     - `ui/pages/home.py`: Live video surveillance, multi-camera feeds (1–5 cameras), and all stream/feed controls on the home page.
     - `ui/pages/ai_settings.py`: Model selection (Qwen 3.5 VL Local vs Gemini Cloud), confidence thresholds, AI frame skip, and live bounding box toggle.
     - `ui/pages/active_review.py`: Human-In-The-Loop confirmation and class relabeling queue.
     - `ui/pages/prediction_history.py`: Historical analytics, time-series chart, and structured visual facts JSON inspector.
     - `ui/pages/emergency_contacts.py`: Emergency contacts list and dispatch gateway overview.

3. **Active Human-in-the-Loop (HITL) Visual Deduplication & Relabeling**:
   - **Perceptual Deduplication**: Added `is_duplicate_frame()` using downsampled Mean Absolute Difference (MAD) to prevent duplicate snapshots when video loops or scenes remain stationary.
   - **Class Relabeling & Ground Truth Annotation**:
     - Database schema in SQLite WAL `detection_logs` extended with `predicted_label`, `corrected_label`, and `bounding_boxes`.
     - 1-click action buttons on the Active Review tab:
       - `🚨 Accident (Class 0)`: Confirms incident as accident (`CONFIRMED_ACCIDENT`).
       - `🚗 Vehicle (Class 1)`: Relabels false alarm bounding boxes as normal vehicles (`RELABELED_VEHICLE`).
       - `❌ Discard`: Rejects sample as background noise (`REJECTED_FALSE_POSITIVE`).
   - **Hugging Face Hub Staging, Visual Curation & 1-Click Publisher**:
     - Standardized Hugging Face `DatasetDict` object detection format with COCO bounding boxes and typed features (`0: accident`, `1: vehicle`).
     - Staging gallery with global and per-card **`👁️ Toggle Bounding Boxes`** and **`🗑️ Delete Sample`** functionality.
     - Direct 1-click Hub publisher (`push_dataset_to_hub()`) with automated `README.md` dataset card generation and public/private repo settings.
   - **YOLO Fine-Tuning Dataset Export**:
     - ZIP exporter generates dataset manifest, `classes.txt`, and normalized YOLO format `.txt` label files mapping corrected classes (`0: accident`, `1: vehicle`) to bounding boxes.

4. **Bug Fixes & Stability**:
   - Fixed `KeyError: 'false_positive_rate'` on the prediction history page.
   - Fixed OpenCV assertion crash `(-215:Assertion failed) !_filename.empty()`.
   - Fixed video upload bug where uploads were wiped on Streamlit reruns.
   - Fixed VLM verifier model selection synchronization across pages.

**Files touched:** `agentic/data_collection.py`, `agentic/hf_exporter.py`, `ui/pages/home.py`, `ui/pages/ai_settings.py`, `ui/pages/active_review.py`, `ui/pages/prediction_history.py`, `ui/pages/emergency_contacts.py`, `ui/main.py`, `ui/utils.py`, `agentic/agents.py`, `pyproject.toml`.

---

See [`docs/PROGRESS.md`](./docs/PROGRESS.md) for earlier historical development logs.
