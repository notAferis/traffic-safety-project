"""
hf_exporter.py
--------------
Converts reviewed Human-in-the-Loop (HITL) detection snapshots and bounding boxes
from SQLite WAL into a production-ready Hugging Face Object Detection Dataset (DatasetDict)
and publishes directly to the Hugging Face Hub.
"""

import os
import json
import sqlite3
import random
from pathlib import Path
from PIL import Image
from datasets import Dataset, DatasetDict, Features, Image as HFImage, Sequence, Value, ClassLabel

# Directory Setup
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "collection"
DB_PATH = DATA_DIR / "detections.db"
SNAPSHOT_DIR = DATA_DIR / "snapshots"


def get_staging_summary() -> dict:
    """
    Returns a summary of all human-reviewed samples available for Hugging Face publishing.
    """
    if not DB_PATH.exists():
        return {"total_reviewed": 0, "accidents": 0, "vehicles": 0, "discarded": 0, "samples": []}

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM detection_logs
        WHERE review_status != 'PENDING_REVIEW'
        ORDER BY id DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    total_reviewed = len(rows)
    accidents = sum(1 for r in rows if (r.get("corrected_label") or "").lower() == "accident" or r.get("review_status") == "CONFIRMED_ACCIDENT")
    vehicles = sum(1 for r in rows if (r.get("corrected_label") or "").lower() == "vehicle" or r.get("review_status") == "RELABELED_VEHICLE")
    discarded = sum(1 for r in rows if r.get("review_status") == "REJECTED_FALSE_POSITIVE" and (r.get("corrected_label") or "").lower() not in ["accident", "vehicle"])

    return {
        "total_reviewed": total_reviewed,
        "accidents": accidents,
        "vehicles": vehicles,
        "discarded": discarded,
        "samples": rows
    }


def build_hf_dataset(
    train_ratio: float = 0.85,
    include_discarded: bool = False,
    seed: int = 42
) -> DatasetDict:
    """
    Constructs a native Hugging Face DatasetDict with 'train' and 'validation' splits
    standardized for Object Detection tasks.
    
    Classes:
      0: accident
      1: vehicle
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if include_discarded:
        cursor.execute("SELECT * FROM detection_logs WHERE review_status != 'PENDING_REVIEW' ORDER BY id ASC")
    else:
        cursor.execute("""
            SELECT * FROM detection_logs
            WHERE review_status != 'PENDING_REVIEW'
              AND (corrected_label IN ('accident', 'vehicle') OR review_status IN ('CONFIRMED_ACCIDENT', 'RELABELED_VEHICLE'))
            ORDER BY id ASC
        """)

    records = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if not records:
        raise ValueError("No reviewed detection records found in database to build dataset.")

    # Shuffle records deterministically
    rng = random.Random(seed)
    shuffled_records = list(records)
    rng.shuffle(shuffled_records)

    split_idx = int(len(shuffled_records) * train_ratio)
    train_records = shuffled_records[:split_idx]
    val_records = shuffled_records[split_idx:] if split_idx < len(shuffled_records) else shuffled_records[:1]

    # Hugging Face Object Detection Features Schema
    hf_features = Features({
        "image": HFImage(),
        "image_id": Value("string"),
        "feed_name": Value("string"),
        "timestamp": Value("string"),
        "objects": {
            "bbox": Sequence(Sequence(Value("float32"), length=4)),  # [xmin, ymin, width, height] in pixels
            "category": Sequence(ClassLabel(names=["accident", "vehicle"])),
            "area": Sequence(Value("float32")),
            "id": Sequence(Value("int64")),
        }
    })

    def _convert_records_to_dict(rec_list):
        data_images = []
        data_image_ids = []
        data_feed_names = []
        data_timestamps = []
        data_objects = []

        global_box_id = 0

        for r in rec_list:
            img_rel = r.get("image_path", "")
            if not img_rel:
                continue
            full_path = BASE_DIR / img_rel
            if not full_path.exists():
                continue

            try:
                with Image.open(full_path) as img:
                    img_w, img_h = img.size

                # Determine class: 0 for accident, 1 for vehicle
                corr_label = (r.get("corrected_label") or "accident").lower()
                if "vehicle" in corr_label or r.get("review_status") == "RELABELED_VEHICLE":
                    cat_id = 1
                elif "accident" in corr_label or r.get("review_status") == "CONFIRMED_ACCIDENT":
                    cat_id = 0
                else:
                    cat_id = 0

                bboxes = []
                categories = []
                areas = []
                box_ids = []

                # Parse detected bounding boxes JSON
                raw_boxes = json.loads(r.get("bounding_boxes", "[]"))
                if raw_boxes:
                    for b in raw_boxes:
                        b_data = b.get("box", {})
                        xmin = float(b_data.get("xmin", 0))
                        ymin = float(b_data.get("ymin", 0))
                        xmax = float(b_data.get("xmax", img_w))
                        ymax = float(b_data.get("ymax", img_h))

                        w = max(1.0, xmax - xmin)
                        h = max(1.0, ymax - ymin)
                        bboxes.append([xmin, ymin, w, h])
                        categories.append(cat_id)
                        areas.append(w * h)
                        box_ids.append(global_box_id)
                        global_box_id += 1
                else:
                    # Fallback: whole frame box if no bounding box was stored
                    bboxes.append([0.0, 0.0, float(img_w), float(img_h)])
                    categories.append(cat_id)
                    areas.append(float(img_w * img_h))
                    box_ids.append(global_box_id)
                    global_box_id += 1

                data_images.append(str(full_path))
                data_image_ids.append(f"img_{r['id']}")
                data_feed_names.append(r.get("feed_name", "Unknown"))
                data_timestamps.append(r.get("timestamp", ""))
                data_objects.append({
                    "bbox": bboxes,
                    "category": categories,
                    "area": areas,
                    "id": box_ids
                })
            except Exception as e:
                print(f"[HF Exporter] Error processing record {r.get('id')}: {e}")
                continue

        return {
            "image": data_images,
            "image_id": data_image_ids,
            "feed_name": data_feed_names,
            "timestamp": data_timestamps,
            "objects": data_objects,
        }

    train_dict = _convert_records_to_dict(train_records)
    val_dict = _convert_records_to_dict(val_records)

    train_ds = Dataset.from_dict(train_dict, features=hf_features)
    val_ds = Dataset.from_dict(val_dict, features=hf_features)

    return DatasetDict({
        "train": train_ds,
        "validation": val_ds
    })


def create_dataset_card_content(repo_id: str, num_train: int, num_val: int, num_accidents: int, num_vehicles: int) -> str:
    """
    Generates GitHub/HuggingFace Flavored Markdown for the dataset card with metadata.
    """
    card = f"""---
license: mit
task_categories:
- object-detection
tags:
- traffic-safety
- accident-detection
- computer-vision
- hitl
- human-in-the-loop
size_categories:
- 1K<n<10K
---

# {repo_id.split('/')[-1].replace('-', ' ').title()}

## Dataset Description
This dataset contains real-world traffic surveillance frames curated through an **Active Human-in-the-Loop (HITL)** pipeline.
Candidate detections from fine-tuned RT-DETR models were human-verified and relabeled to distinguish genuine traffic accidents from false alarms (normal vehicles, shadows, and debris).

### Dataset Statistics
- **Total Images**: {num_train + num_val}
  - **Train split**: {num_train} samples
  - **Validation split**: {num_val} samples
- **Annotated Objects Breakdown**:
  - `accident` (Class 0): ~{num_accidents} verified collision scenes
  - `vehicle` (Class 1): ~{num_vehicles} relabeled normal vehicle scenes

## Class Labels
| Class ID | Label Name | Description |
|---|---|---|
| `0` | `accident` | Verified vehicular collision, overturn, or severe traffic hazard. |
| `1` | `vehicle` | Normal moving or stationary car, truck, bus, or motorcycle. |

## Quickstart Usage

```python
from datasets import load_dataset

# Load dataset from Hugging Face Hub
dataset = load_dataset("{repo_id}")

print(dataset)
sample = dataset["train"][0]
print("Image:", sample["image"])
print("Objects:", sample["objects"])
```

## Bounding Box Format
Bounding boxes are provided in standard **COCO format**: `[xmin, ymin, width, height]` (in pixels).
"""
    return card


def push_dataset_to_hub(
    repo_id: str,
    hf_token: str = None,
    private: bool = True,
    train_ratio: float = 0.85,
) -> str:
    """
    Converts curated SQLite records into Hugging Face DatasetDict and pushes directly to Hugging Face Hub.
    Returns direct URL to the published dataset.
    """
    token = hf_token or os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
    if not token:
        raise ValueError("Hugging Face API token is required. Set HF_TOKEN in your environment or provide it in the UI.")

    repo_clean = repo_id.strip()
    if "/" not in repo_clean:
        from huggingface_hub import HfApi
        api = HfApi(token=token)
        user_info = api.whoami()
        username = user_info["name"]
        repo_clean = f"{username}/{repo_clean}"

    # Build HF dataset
    ds_dict = build_hf_dataset(train_ratio=train_ratio)
    num_train = len(ds_dict["train"])
    num_val = len(ds_dict["validation"])

    summary = get_staging_summary()
    card_content = create_dataset_card_content(
        repo_id=repo_clean,
        num_train=num_train,
        num_val=num_val,
        num_accidents=summary["accidents"],
        num_vehicles=summary["vehicles"]
    )

    # Push Dataset to Hub
    ds_dict.push_to_hub(
        repo_id=repo_clean,
        token=token,
        private=private,
        commit_message="Upload active HITL verified traffic accident dataset"
    )

    # Upload README.md dataset card
    from huggingface_hub import upload_file
    import tempfile
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".md") as tf:
        tf.write(card_content)
        tf_path = tf.name

    try:
        upload_file(
            path_or_fileobj=tf_path,
            path_in_repo="README.md",
            repo_id=repo_clean,
            repo_type="dataset",
            token=token,
            commit_message="Add dataset card and documentation"
        )
    finally:
        if os.path.exists(tf_path):
            os.remove(tf_path)

    return f"https://huggingface.co/datasets/{repo_clean}"
