"""
benchmark_detr_hybrid.py
-------------------------
Compares two accident-detection approaches against the full calibration set
(agentic/test_incidents/calibration/, ground truth = neg_*/pos_* filename prefix):

  1. DETR-only   — hilmantm/detr-traffic-accident-detection, thresholded exactly like
                    the dashboard (ui/main.py): any box whose label contains
                    "accident"/"collision"/"crash"/"incident" with score >= 0.85.
  2. DETR + LLM   — the same DETR gate, but every DETR-positive frame is then passed to
     hybrid          the qwen2.5vl:3b structured-output verifier (agentic/agents.py's
                    IncidentVerdict), exactly as the production pipeline does: DETR
                    triggers, the LLM confirms/rejects before dispatch would fire.
                    A DETR-negative frame is never sent to the LLM (matches production —
                    the LLM only ever runs after a DETR trigger), so its hybrid verdict
                    is just "no accident".

Dispatch functions are never touched — this script only calls the DETR pipeline and the
LLM verifier directly, no SMS/voice/call side effects are possible.

Results are written incrementally (one line per item) to
agentic/test_results/benchmark_detr_hybrid_results_thresh<NNN>.jsonl so a hung LLM call
doesn't lose prior progress. Each LLM call is wrapped in a SIGALRM-based hard timeout
(LLM_TIMEOUT_S) so a genuine Ollama hang (seen previously with qwen3-vl:4b) can't stall
the whole run — matches the per-item timeout pattern used in earlier model-comparison
benchmarks.

Usage:
    uv run python -m agentic.tests.benchmark_detr_hybrid [--threshold 0.85]

Results for a given threshold are written to
agentic/test_results/benchmark_detr_hybrid_results_thresh<NNN>.jsonl (e.g. thresh085.jsonl
for 0.85), so runs at different thresholds don't overwrite each other.
"""
import argparse
import base64
import glob
import json
import os
import signal
import time
from pathlib import Path

import torch
from PIL import Image
from transformers import pipeline as hf_pipeline

from agentic.agents import verifier
from agentic.prompts import INCIDENT_RESPONSE_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage

CALIB_DIR = Path(__file__).parent.parent / "test_incidents" / "calibration"
RESULTS_DIR = Path(__file__).parent.parent / "test_results"

ACCIDENT_LABEL_KEYWORDS = ["accident", "collision", "crash", "incident"]  # matches ui/main.py
LLM_TIMEOUT_S = 300  # same per-call budget used in prior model-comparison benchmarks


class LLMTimeout(Exception):
    pass


def _alarm_handler(signum, frame):
    raise LLMTimeout()


def ground_truth(path: Path) -> bool:
    name = path.name
    if name.startswith("pos_"):
        return True
    if name.startswith("neg_"):
        return False
    raise ValueError(f"can't infer ground truth from filename: {name}")


def detr_verdict(detector, image: Image.Image, confidence_thresh: float):
    t0 = time.time()
    preds = detector(image)
    dt = time.time() - t0
    best_score = 0.0
    triggered = False
    for p in preds:
        label = p["label"].lower()
        if any(k in label for k in ACCIDENT_LABEL_KEYWORDS):
            best_score = max(best_score, p["score"])
            if p["score"] >= confidence_thresh:
                triggered = True
    return triggered, best_score, dt


def llm_verdict(image: Image.Image, detr_score: float):
    buf_path = "/tmp/_benchmark_frame.jpg"
    image.save(buf_path, format="JPEG")
    with open(buf_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    alert = (
        "Emergency: A vehicle accident has been detected on 'Benchmark Feed' located at "
        f"Calibration Set. The AI model confidence score is {detr_score * 100:.1f}%. "
        "Please immediately call and send SMS dispatch reports to notify emergency contacts."
    )
    message = HumanMessage(
        content=[
            {"type": "text", "text": alert},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
        ]
    )

    signal.signal(signal.SIGALRM, _alarm_handler)
    signal.alarm(LLM_TIMEOUT_S)
    t0 = time.time()
    try:
        verdict = verifier.invoke([SystemMessage(content=INCIDENT_RESPONSE_PROMPT), message])
        dt = time.time() - t0
        return verdict.is_accident, dt, None
    except LLMTimeout:
        dt = time.time() - t0
        return False, dt, "timeout"
    except Exception as e:
        dt = time.time() - t0
        return False, dt, str(e)
    finally:
        signal.alarm(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=0.85)
    args = parser.parse_args()
    confidence_thresh = args.threshold
    results_path = (
        RESULTS_DIR
        / f"benchmark_detr_hybrid_results_thresh{int(round(confidence_thresh * 100)):03d}.jsonl"
    )

    device = 0 if torch.cuda.is_available() else -1
    print(f"Loading DETR (device={'cuda' if device == 0 else 'cpu'}), threshold={confidence_thresh}...")
    detector = hf_pipeline(
        "object-detection", model="hilmantm/detr-traffic-accident-detection", device=device
    )

    items = sorted(CALIB_DIR.glob("*.jpg")) + sorted(CALIB_DIR.glob("*.png"))
    print(f"{len(items)} calibration items found.")

    done = {}
    if results_path.exists():
        with open(results_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                done[row["item"]] = row
        print(f"Resuming — {len(done)} items already have results.")

    with open(results_path, "a") as out:
        for i, path in enumerate(items, 1):
            name = path.stem
            if name in done:
                continue

            gt = ground_truth(path)
            image = Image.open(path).convert("RGB")

            detr_triggered, detr_score, detr_dt = detr_verdict(detector, image, confidence_thresh)

            if detr_triggered:
                llm_positive, llm_dt, llm_err = llm_verdict(image, detr_score)
                hybrid_verdict = llm_positive
            else:
                llm_dt, llm_err = None, None
                hybrid_verdict = False  # LLM never runs if DETR doesn't trigger (matches production)

            row = {
                "item": name,
                "ground_truth": gt,
                "detr_score": round(detr_score, 4),
                "detr_verdict": detr_triggered,
                "detr_latency_s": round(detr_dt, 2),
                "hybrid_verdict": hybrid_verdict,
                "llm_latency_s": round(llm_dt, 2) if llm_dt is not None else None,
                "llm_error": llm_err,
            }
            out.write(json.dumps(row) + "\n")
            out.flush()

            status = "✅" if detr_triggered == gt else "❌"
            hstatus = "✅" if hybrid_verdict == gt else "❌"
            print(
                f"[{i}/{len(items)}] {name}: gt={gt} "
                f"detr={detr_triggered}({detr_score:.2f}) {status}  "
                f"hybrid={hybrid_verdict}{'(llm ' + str(llm_dt) + 's)' if llm_dt else ''} {hstatus}"
            )

    print("Done. Results in", results_path)


if __name__ == "__main__":
    main()
