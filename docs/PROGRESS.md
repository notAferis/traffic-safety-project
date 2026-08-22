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

## 2026-07-22 — Added explicit online/offline dispatch modes; separate launcher scripts

**What changed:**
`agentic/tools.py` gained a `DISPATCH_MODE` environment variable (`"online"` default, or
`"offline"`), read via a new `_is_offline_mode()` helper:
- `send_incident_report()` now only calls `send_sms` (mnotify) when not in offline mode; the
  Termux-gateway SMS and ring-call channels fire in both modes.
- `send_voice_incident_report()` (the spoken-message call, still mnotify-only — no offline path
  exists for that) is now a no-op in offline mode instead of being attempted and failing/hanging.

Two new launcher scripts, `runner_offline.sh` and `runner_online.sh`, set `DISPATCH_MODE`
explicitly and are otherwise identical to the existing `runner.sh`; `DISPATCH_MODE` also composes
with `run_on_gpu.py`/`run_on_cpu.py` as a plain env var. `runner.sh` is unchanged (defaults to
online, same as before). `USAGE.md` section 4 rewritten to document both dimensions (compute:
GPU/CPU, dispatch: online/offline) and their interaction; also corrected a stale reference to a
`GOOGLE_API_KEY`/Gemini dependency that no longer exists in the code (the verifier has used local
Ollama models only since the 2026-07-11/07-20 entries below).

**Why:** requested to make the offline/edge-deployment path an explicit, selectable mode rather
than an implicit side effect of `SMS_GATEWAY_URL` being set or unset — important for this project's
target deployment context (resource-constrained environments, e.g. Ghana, where a live internet
connection at the accident scene can't be assumed). Previously, `send_incident_report` always
attempted the mnotify SMS call regardless of connectivity, meaning a dead connection would sit
waiting on that call's timeout before the offline Termux channels ever got a chance to fire — a real
latency cost in exactly the scenario offline dispatch exists for. Note: the AI detection/verification
models (DETR, `qwen2.5vl:3b`) were **already** fully local before this change (see 2026-07-11 and
2026-07-20 entries) — this change is scoped to the dispatch layer only, not the detection pipeline.

**Files touched:** `agentic/tools.py`, `runner_offline.sh` (new), `runner_online.sh` (new),
`USAGE.md`, `report.md`.

**Verified:** smoke-tested with `send_sms`/`send_sms_offline`/`send_call_offline`/`send_voice_alert`
monkeypatched (no real network/phone calls) — confirmed offline mode fires only the two Termux
channels and skips the voice call entirely; online mode and the unset-default case both fire all
four channels as before. Not yet run against the real Termux phone gateway with `runner_offline.sh`
specifically (the underlying `send_sms_offline`/`send_call_offline` calls themselves were already
verified against real hardware in earlier entries; only the new mode-gating logic is new here).

## 2026-07-20 — Benchmarked DETR-only vs. DETR+LLM hybrid on full 54-item set; lowered default confidence threshold to 0.6

**What changed:**
`ui/main_v2.py`'s confidence-threshold slider default changed from `0.85` to `0.60` (two spots:
`st.session_state.confidence` init and the `st.slider(..., value=...)` default). No detection logic
changed — same DETR model, same label-keyword matching, same hybrid gate structure.

**Why:** built a new benchmark (`agentic/benchmark_detr_hybrid.py`) to evaluate the *whole* detection
pipeline — not just the LLM verification stage in isolation, as all prior comparisons in `results.md`
had done — by comparing DETR alone against the production DETR→LLM hybrid, across the full 54-item
calibration set (see the 2026-07-20 calibration-expansion entry above) and two confidence thresholds
(the old default 0.85, and a lower candidate 0.6).

**Result** (full table and per-item breakdown in `results.md`, "DETR-Only vs. DETR + LLM Hybrid"):

| Approach | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| DETR-only @0.85 | 55.6% | 50.0% | 25.0% | 33.3% |
| Hybrid @0.85 | 61.1% | 80.0% | 16.7% | 27.6% |
| DETR-only @0.6 | 66.7% | 60.0% | 75.0% | 66.7% |
| Hybrid @0.6 | **75.9%** | **86.7%** | 54.2% | 66.7% |

0.85 was filtering out most real accidents before the LLM ever saw them (many genuine crashes score
0.6–0.85 on DETR's "accident" label). At 0.6, DETR alone catches far more real accidents (recall
25%→75%) at the cost of more false alarms (12 on normal-traffic frames), and the LLM hybrid stage
cleans up 10 of those 12 (precision 60.0%→86.7%), making hybrid@0.6 the best configuration on every
metric except recall, where it still trails DETR-only@0.6 (the LLM occasionally rejects a real accident
DETR correctly flagged, or the call times out — same visual-grounding ceiling seen in the earlier
9-item model comparisons, now visible at pipeline scale).

**Decision:** switched the dashboard's default confidence threshold to 0.6, since hybrid@0.6 never
trades away precision relative to any other tested configuration — the direction that matters most for
a gate sitting in front of real SMS/call dispatch. 0.6 was not exhaustively swept against finer
thresholds (e.g. 0.65/0.70); this was a two-point comparison (0.85 vs 0.6), not a full sweep.

**Cost tradeoff:** at 0.6, 30/54 calibration frames (56%) trigger the LLM stage vs. 12/54 (22%) at
0.85, ~99s average per LLM call — more frequent LLM round-trips per live camera feed in exchange for
the accuracy/precision gain.

**Files touched:** `ui/main_v2.py` (two-line threshold default change), `agentic/benchmark_detr_hybrid.py`
(new benchmark script, reusable for future threshold/model sweeps), `results.md`.

**Verified:** benchmark run directly against DETR + the production `IncidentVerdict` verifier, no
dispatch functions touched (no real SMS/voice/call side effects). Not yet re-validated live against
the dashboard itself with the new default — worth a quick manual smoke test before relying on it in a
real run.

## 2026-07-20 — Added offline phone call (Termux) as an SMS attention-getter

**What changed:**
`termux_gateway/sms_server.py` now also serves `POST /call` alongside the existing `POST /sms` —
it runs `termux-telephony-call <number>` to place a real call over the phone's own SIM. Only the
first recipient (`phone_numbers.txt`'s primary contact) is dialed, since a phone call occupies the
SIM's one call slot and dialing a list back-to-back the way SMS does isn't meaningful.

`agentic/utils.py` gained `send_call_offline(recipients)`, which posts to the gateway's `/call`
endpoint (URL derived automatically from `SMS_GATEWAY_URL`, no new env var needed).
`agentic/tools.py::send_incident_report()` now calls it right after the offline SMS dispatch, wrapped
in the same fail-safe try/except pattern as the other dispatch calls.

**Why:** this is a plain ring to get the primary contact's attention and prompt them to check the SMS
that was just sent — not a way to deliver a spoken message (that remains
`send_voice_incident_report`, still online-only via mnotify). Requested directly to extend the
existing offline-SMS gateway with an offline call path.

**Reliability caveat (documented in `USAGE.md`):** `termux-telephony-call` has known issues on newer
Android when Termux is backgrounded — Android's background-activity restrictions can silently block
the call (see [termux-api-package#197](https://github.com/termux/termux-api-package/issues/197)).
Unlike SMS, this hasn't been empirically verified to work with the phone's screen off / Termux not in
the foreground — worth testing explicitly on the actual deployment phone before relying on it, and
worth stating as a known limitation in the dissertation regardless of the test outcome.

**Files touched:** `termux_gateway/sms_server.py`, `agentic/utils.py`, `agentic/tools.py`,
`USAGE.md`.

**Verified:** dispatch wiring smoke-tested with `httpx.post` monkeypatched (no real network calls) —
confirmed `send_incident_report()` now fires three dispatch calls in order (mnotify SMS, offline SMS,
offline call) with correct URLs/payloads. Not yet verified against a real phone — the gateway URL in
this environment's `.env` points to a real device, so live testing was deliberately avoided during
development to not trigger a real call/SMS; verify manually before considering this feature
production-ready.

## 2026-07-20 — Evaluated qwen3-vl:4b, kept qwen2.5vl:3b as the offline model

**What changed:** nothing in code — this was an evaluation that ended in "no change."

**Why evaluated:** `qwen3-vl:4b` (Qwen3's vision-language variant) was newly pulled into Ollama and
is a larger/newer model than the current `qwen2.5vl:3b`, so it was worth benchmarking as a possible
upgrade using the same 9-item calibration set / structured-output harness as the other model
comparisons (see `results.md`, "Three-Way Model Comparison").

**Result:**

| Model | Accuracy | Recall | Avg. latency | Reliability |
|---|---|---|---|---|
| qwen2.5vl:3b (current) | 7/9 = 77.8% | 66.7% | 90.0s | no timeouts |
| qwen3-vl:4b | 6/9 = 66.7% | 50.0% | 113.3s (completed items only) | **hung on pos_3, never returned even after a retry at 600s (2x the normal 300s budget)** |

`qwen3-vl:4b` did not beat `qwen2.5vl:3b` on accuracy despite being larger, ran slower across every
item, and genuinely hung (not just slow — no output at all) on one calibration image, most likely
because it has `thinking` mode enabled by default and generated an unbounded reasoning trace instead
of converging. Same failure signature as the Ollama hangs hit earlier during the multi-frame
experiment (unresponsive process, flat CPU time).

**Decision:** kept `agentic/agents.py` on `qwen2.5vl:3b`. A hang in a real deployment would mean a
detected incident silently never gets verified/dispatched, which is disqualifying for this gate
regardless of accuracy on the other 8 items — not worth revisiting unless `thinking` mode can be
disabled and re-tested.

**Files touched:** none (evaluation only).

## 2026-07-20 — Switched offline verifier model from gemma4:e2b to qwen2.5vl:3b

**What changed:**
`agentic/agents.py`'s `llm` now uses `model="qwen2.5vl:3b"` instead of `gemma4:e2b` (same
`temperature=0, top_k=1, seed=42` settings). No other code changed — the structured-output
architecture (see 2026-07-11 entry) already didn't depend on tool-calling support, which is what
excluded `qwen2.5vl:3b` from consideration originally.

**Why:**
Re-benchmarked both models on the full 9-item calibration set, single frame, identical prompt/schema,
differing only in `model=` (see `results.md`, "Model Comparison — Structured-Output Architecture"):

| Model | Accuracy | Precision | Recall | Avg. latency |
|---|---|---|---|---|
| gemma4:e2b | 6/9 = 66.7% | 100% | 33.3% | 66.4s |
| qwen2.5vl:3b | 7/9 = 77.8% | 100% | 66.7% | 90.0s* |

qwen2.5vl:3b catches double the real accidents (recovers pos_5, pos_6 in addition to pos_1, pos_2)
with the same zero-false-alarm precision as gemma4:e2b. Both models still miss pos_3 and pos_4 (subtle
damage, no debris/dust/overturn) — likely a shared visual-grounding ceiling for local models this
size, not something the model swap fixes.

*qwen2.5vl:3b's average is skewed by one 267.5s outlier; typical latency is comparable to gemma4:e2b.

**Side finding from the same benchmark run:** re-measuring gemma4:e2b itself under the structured-
output architecture (vs. the original tool-calling architecture) improved its own accuracy from
44.4% to 66.7% — the architecture migration was a net accuracy win independent of which model is
configured, not just a tool-calling-compatibility fix.

**Files touched:** `agentic/agents.py` (one-line model string change).

**Verified:** smoke-tested against the same two calibration frames used to verify the 2026-07-11
migration (`neg_2`, `pos_2`) with dispatch mocked — `neg_2` correctly returned `is_accident=False`
with no dispatch, `pos_2` correctly returned `is_accident=True` and dispatched both SMS and voice
reports, no Pydantic validation errors.

## 2026-07-11 — Replaced tool-calling with strict structured JSON output for incident verification

**What changed:**
The incident-verification agent (`agentic/agents.py`) previously used a LangGraph ReAct agent that
decided whether to dispatch an incident report by directly invoking LangChain tools
(`send_incident_report`, `send_voice_incident_report`) via the model's native tool-calling API.

That's been replaced with a simpler, stricter flow:

```
DETR detection → LLM (structured output) → validated JSON verdict → plain Python dispatch
```

The LLM now returns a single structured object, validated against a Pydantic schema:

```python
class IncidentVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    observations: str      # literal description of the frame (forces reasoning before the verdict)
    is_accident: bool       # the actual decision
    sms_description: str    # empty if is_accident is False
    voice_message: str      # empty if is_accident is False
```

via `llm.with_structured_output(IncidentVerdict, method="json_schema")`, which uses Ollama's native
JSON-schema-constrained decoding rather than tool-calling. The dispatch functions are then called
directly in Python based on `verdict.is_accident` — the model no longer decides *how* to call
anything, only *what* the verdict is.

**Why:**
- Tool-calling reliability was inconsistent on the small local model (`gemma4:e2b`) — in earlier
  testing it sometimes dispatched only one of the two tools, or returned an empty final reply after a
  confirmed accident (see `results.md`).
- `qwen2.5vl:3b` couldn't be evaluated as an offline option at all, because Ollama reported it has no
  tool-calling support (`does not support tools`, status 400) — a hard incompatibility with the old
  ReAct architecture. Structured JSON output has no such requirement, since it constrains decoding
  directly rather than depending on function-calling support.
- Field order in the schema (`observations` before `is_accident`) preserves the chain-of-thought
  benefit of the old step-by-step prompt (see `agentic/prompts.py`) — the model has to write its
  literal observations before committing to a boolean, which was important for the small model's
  accuracy in earlier testing.
- `location` is now passed into `run_incident_response()` as an explicit argument (from
  `ui/main_v2.py`'s already-known `location_info`) instead of being extracted from free text by the
  model — removes a failure mode where a small model could mangle the location string.

**Strictness added on top of the base structured-output design:**
- `ConfigDict(extra="forbid", strict=True)` — rejects unexpected fields and disables type coercion
  (e.g. a string `"true"` will not silently pass as a bool).
- `max_length` bounds on `observations`/`sms_description`/`voice_message` — hard character caps
  roughly matching the prompt's word-count guidance, enforced by Pydantic rather than only requested
  in the prompt text.
- `method="json_schema"` pinned explicitly rather than relying on the library default, so a model
  without structured-output support fails loudly instead of silently degrading.
- `run_incident_response()` wraps the verifier call in a try/except and fails safe — any
  parsing/validation error is treated as a false positive (no dispatch), since this gate sits in front
  of a real SMS/voice call and must never forward an unvalidated response.

**Files touched:** `agentic/agents.py`, `agentic/prompts.py`, `ui/main_v2.py` (one-line call-site
change to pass `location`).

**Verified:** smoke-tested against two calibration frames from `agentic/test_incidents/calibration/`
with dispatch mocked — a normal-traffic frame correctly returned `is_accident=False` with no dispatch,
and a real-accident frame (truck crash, dust cloud) correctly returned `is_accident=True` and
dispatched both SMS and voice reports, with no Pydantic validation errors under the stricter schema.
