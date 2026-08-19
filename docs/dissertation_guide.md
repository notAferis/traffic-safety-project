# Project Documentation Guide

This is a **guide, not a finished chapter** — short notes and real project facts under each
heading from your table of contents, so you can expand each into full prose yourself. Sections
marked **[Your input needed]** are things I have no factual basis for (personal reflections,
literature review, formal diagrams) — I've left pointers on what belongs there instead of making
something up.

Source material used throughout: `report.md`, `results.md`, `PROGRESS.md`, `USAGE.md`,
`pyproject.toml`, and the actual code in `ui/`, `agentic/`, `termux_gateway/`.

---

## DECLARATION / ACKNOWLEDGEMENT / DEDICATION

**[Your input needed]** — these are personal/institutional statements (your declaration of
originality, thanking your supervisor and the T.A. who gave the offline-mode feedback, whoever you
want to dedicate the work to). Nothing to base on the codebase.

## TABLE OF FIGURES / TABLE OF TABLES

Don't type these by hand in the final document — caption each figure/table as you insert it
(Word/LibreOffice: right-click → Insert Caption), then generate the list itself via
References → Table of Figures once the document is complete, so the page numbers stay accurate as
the report grows. What's below is a **draft numbered list for this specific project**, in the
order figures/tables would naturally appear chapter-by-chapter — use it as your shot list (what to
screenshot/diagram) and starting caption text; the exact numbers/pages will shift once you insert
them for real. Skip anything you decide not to include; the sample below (a different, unrelated
student's IoT project) shows the *format* expected, not the content — treat it as a style
reference only.

**TABLE OF FIGURES**

| # | Caption | Where it comes from |
|---|---|---|
| Figure 1 | Manual, bystander-dependent accident reporting process (problem illustration) | Your own diagram — **[Your input needed]** |
| Figure 2 | AI-assisted automated detection and dispatch process (proposed solution) | Your own diagram, mirrors Figure 1 |
| Figure 3 | Two-stage detection and verification pipeline | Diagram from §2.8's pipeline sketch in this guide |
| Figure 4 | Overview of proposed system architecture | Diagram from §2.9 (presentation / intelligence / dispatch layers) |
| Figure 5 | Use case diagram | §3.4 |
| Figure 6 | Activity diagram — two-stage gate decision flow | §3.4 |
| Figure 7 | Sequence diagram — detection → verification → dispatch | §3.4 |
| Figure 8 | Block diagram — compute/hardware mapping (laptop, local Ollama server, Android Termux gateway) | §4.1 ("Mapping Logical Design onto Physical Platform") |
| Figure 9 | Dashboard — Live Feed view with detection overlay | Screenshot, `streamlit run ui/main_v2.py` |
| Figure 10 | Dashboard — AI Settings panel (confidence threshold, detection toggle) | Screenshot, same session |
| Figure 11 | Dashboard — Incident console after a confirmed detection | Screenshot, same session |
| Figure 12 | Termux SMS/call gateway running on the Android phone | Screenshot/photo, `termux_gateway/sms_server.py` in Termux |
| Figure 13 | Ollama serving `qwen2.5vl:3b` (terminal output) | Screenshot, `ollama run` / `ollama ps` |
| Figure 14 | Snapshot of verifier code (`agentic/agents.py`) | Code screenshot |
| Figure 15 | Snapshot of dashboard render loop code (`ui/main_v2.py`) | Code screenshot |
| Figure 16 | Accuracy/precision/recall vs. confidence threshold | Plot from the DETR-only vs. hybrid benchmark numbers in §4.3 |
| Figure 17 | Kumasi Metropolitan Assembly demo | Photo, if you have one from that meeting — **[Your input needed]** |

**TABLE OF TABLES**

| # | Caption | Where it comes from |
|---|---|---|
| Table 1 | Development tools and environment | §2.11 |
| Table 2 | Functional requirements | §3.2 |
| Table 3 | DETR-only vs. Hybrid results @ 0.85 confidence threshold | §4.3 / `results.md` |
| Table 4 | DETR-only vs. Hybrid results @ 0.6 confidence threshold (adopted) | §4.3 / `results.md` |
| Table 5 | Model comparison — `qwen2.5vl:3b` vs. `gemma4:e2b` vs. Gemini 2.5 Flash | §4.3 / `results.md` |
| Table 6 | Project timeline / milestones | §1.8 |
| Table 7 | Test set composition (24 accident frames, 30 normal-traffic frames) | §4.3 |

---

## CHAPTER 1

### 1.1 Introduction

Base this on `report.md` §1. Core framing: road traffic accidents in resource-constrained
settings (Ghana) often go unreported for critical minutes because no bystander calls it in, or
there's no reliable connectivity to do so. This project builds a system that watches traffic
camera footage, recognises when an accident has actually happened, and automatically alerts
emergency contacts — no human needs to be watching the screen.

### 1.2 Problem Statement

- Accidents go undetected/unreported for minutes in areas without constant human monitoring.
- Naive single-model detection is unreliable in both directions: strict enough to avoid false
  alarms → misses real accidents; loose enough to catch accidents → fires on ordinary traffic
  (this is the concrete problem that motivated the two-stage design — see `report.md` §2).
- Existing dispatch/alerting solutions typically assume internet connectivity, which cannot be
  assumed at the accident scene in the target deployment context.

### 1.3 Project Aim

To design and build a system that automatically detects road traffic accidents from video feeds
and dispatches emergency alerts (SMS and voice) to responders, with the central goal of doing so
**with no dependence on internet connectivity at any stage** (`report.md` §3, §6).

### 1.4 Specific Objectives

Phrase these as objectives; each maps to something actually built:

1. Detect potential accident frames in real time from live or recorded video using a computer
   vision object detector (DETR).
2. Reduce false positives by adding a second-stage vision-language model that confirms a flagged
   frame is a genuine accident before any alert is sent.
3. Dispatch SMS and voice alerts to emergency contacts automatically on a confirmed incident.
4. Make the entire pipeline — detection, verification, and dispatch — runnable fully offline, via
   local models (DETR + Ollama-hosted `qwen2.5vl:3b`) and a phone-based SMS/call gateway (Termux),
   as an explicit, selectable mode alongside an online mode.
5. Evaluate detection/verification accuracy rigorously against a hand-labelled test set rather
   than assuming the design works, and use that evaluation to tune the system (confidence
   threshold, model choice).
6. Provide a live monitoring dashboard for operators to configure feeds, thresholds, and dispatch
   settings, and observe incidents as they happen.

### 1.5 Project Justification

- Grounded in a real deployment conversation: your supervisor arranged a demo to **Kumasi
  Metropolitan Assembly (KMA)** members, which led to discussion of piloting the system on
  specific intersections in Kumasi — i.e. a real stakeholder sees a real use case for this,
  not just a class exercise.
- Addresses a genuine gap: commercial/cloud-based incident-detection systems assume reliable
  connectivity and infrastructure that doesn't hold everywhere; this project targets the case
  where it doesn't.

### 1.6 Project Motivation

**[Your input needed for the personal angle]** — e.g. why you personally care about road safety /
emergency response in Ghana specifically. Project-grounded facts you can build on: you are a
KNUST student based in Kumasi, the same city the KMA discussion concerns, so the offline-first
constraint is the actual condition you're building and testing under, not a hypothetical.

### 1.7 Project Scope

**In scope (built and working):**
- Real-time and recorded-video accident detection (DETR object detector).
- Two-stage verification via a local vision-language model (`qwen2.5vl:3b` via Ollama).
- Automated SMS dispatch, both online (mnotify) and fully offline (Termux phone gateway).
- An offline "attention-getting" ring call (Termux), fully offline.
- Online spoken voice call alert (mnotify) — online mode only.
- A Streamlit dashboard for feed management, live viewing, threshold configuration, and incident
  console.
- Rigorous benchmarking of detection/verification accuracy on a 54-item hand-labelled calibration
  set.

**Out of scope / explicitly deferred (be upfront about this — it's a strength, not a weakness, to
state it clearly):**
- **Fully offline spoken voice call** — the offline path currently only delivers SMS + a plain
  ring; a spoken message over a call with zero internet dependency was investigated and judged too
  fragile to finish within this project's timeline, and remains an open item rather than a
  solved one (`report.md` §3). This was a deliberate scope decision, not an oversight.
- A custom, fine-tuned accident-scene explainer model (SFT on Qwen2.5(-VL)) — identified as
  future work, not part of the current system.
- Multi-camera simultaneous large-scale deployment / production hardening (rate limiting,
  authentication on the dashboard, persistent incident database) — this is a research/pilot-stage
  system, not a hardened production one.

### 1.8 Project Timeline

Actual commit history (`git log`) for this project (the pygame intersection simulation base
template predates this — real work started here):

| Date | Milestone |
|---|---|
| 2026-06-24 | Project start — first commit on the accident-detection/dispatch system |
| 2026-07-04 | Core pipeline functional |
| 2026-07-06 | Voice alert generation moved to local Pocket TTS; DETR inference decoupled from the render loop; GPU (MX250) support added |
| 2026-07-08 | Offline SMS dispatch via Termux phone gateway added; CPU/GPU run scripts; usage docs; verifier switched to local Ollama (`gemma4:e2b`) with first model comparison results |
| 2026-07-20 | Calibration set expanded to 54 frames; offline phone call (ring) added; verifier switched to structured JSON output; verifier model switched to `qwen2.5vl:3b`; DETR-only vs. hybrid benchmarked on the full set; confidence threshold retuned to 0.6 |
| 2026-07-22 | Explicit online/offline dispatch modes added and documented; dashboard UI redesign |

**[Your input needed]** — add the KMA demo date and any earlier milestones (proposal approval,
supervisor meetings) you have dates for; add planned dates for remaining work (write-up, defence).

---

## CHAPTER 2

### 2.1 Review of Similar Systems

**[Your input needed]** — this is a literature review section; it needs real citations to actual
existing accident-detection systems/papers (e.g. CCTV-based accident detection research, commercial
traffic-monitoring platforms, academic work combining CNN detectors with LLM/VLM verification).
Nothing in this codebase constitutes "other systems" you can cite — this needs your own research
(Google Scholar / IEEE Xplore search terms: "automatic traffic accident detection CCTV",
"vision-language model incident verification", "offline emergency dispatch IoT").

### 2.2 Processes of the Existing System

**[Your input needed]** — describes how accident reporting currently works *without* a system like
this (a bystander sees the accident and calls emergency services, or nobody does). Frame it as a
manual, human-dependent process with no automation and no fallback when no one is watching.

### 2.3 Pros and Cons of Existing Related Systems

**[Your input needed, once 2.1's research is done]** — general shape you'll likely find, to guide
the research:

**Pros (typical of existing/commercial systems):** mature, well-tested, often cloud-integrated
with emergency services directly.

**Cons (the gap this project targets):** usually assume reliable internet/cellular connectivity;
often single-stage detection without a second verification step (higher false-alarm rates); costly
to deploy widely in low-resource settings.

### 2.4 Problem Identification

Same content as 1.2, stated more formally as the identified gap: no automated, low-cost,
offline-capable accident detection and dispatch system suited to resource-constrained deployment
contexts.

### 2.5 Project Evaluation

Frame as feasibility across the usual axes, grounded in what you actually confirmed:

- **Technical feasibility** — demonstrated: DETR + local VLM pipeline runs on a laptop
  (CPU or a low-end discrete GPU, MX250, tested), no cloud dependency required for detection or
  verification.
- **Economic feasibility** — low-cost by design: open-weight models run on modest hardware, and
  the offline dispatch channel repurposes an old Android phone as an SMS/call gateway rather than
  requiring paid infrastructure.
- **Operational feasibility** — validated with a real stakeholder (KMA) as plausible for pilot
  deployment on specific intersections.

### 2.6 Review of Related Project Methodologies

The project was actually built **iteratively/incrementally** — each `PROGRESS.md` entry is a
self-contained change, benchmarked and verified before the next one: build a working pipeline →
measure it against a real test set → identify the weakest point (e.g. threshold too strict,
recall too low, tool-calling unreliable) → change one thing → re-measure. This matches an
**Agile/iterative development methodology** rather than a big-upfront-design (waterfall) approach
— useful to name explicitly here, since you can point to the actual commit-by-commit evidence of
it in `PROGRESS.md`.

### 2.7 The Proposed System

Directly from `report.md` §2 — the two-stage "gate" design:

- **Stage 1 (fast, always-on):** DETR object detector scans every video frame, flags anything
  that could plausibly be an accident. Deliberately sensitive — rarely misses a genuine incident.
- **Stage 2 (careful, only runs when flagged):** a vision-language model (`qwen2.5vl:3b`, local)
  looks at the flagged frame and decides if it's a *genuine* accident before anything is
  dispatched — acts as a false-alarm filter.
- Only if both stages agree does the system dispatch SMS/voice.

### Key Components of the Proposed System

- Video ingestion (live camera / uploaded or path-referenced video file)
- Stage-1 detector: DETR (`hilmantm/detr-traffic-accident-detection`, via HuggingFace
  `transformers`)
- Stage-2 verifier: `qwen2.5vl:3b` via Ollama, structured JSON output validated against a Pydantic
  schema (`agentic/agents.py`)
- Dispatch layer: SMS + voice, online (mnotify) and offline (Termux phone gateway)
  (`agentic/tools.py`, `agentic/utils.py`, `termux_gateway/sms_server.py`)
- Dashboard: Streamlit app for feed management, live view, thresholds, incident console
  (`ui/main_v2.py`)

### 2.8 Conceptual Design

Pipeline, end to end:

```
Video feed (camera / file)
        │
        ▼
 DETR object detector  ── every frame, fast ──▶ candidate accident frame?
        │ (if flagged, above confidence threshold)
        ▼
 qwen2.5vl:3b verifier ── structured verdict: is_accident, sms_description, voice_message
        │ (if is_accident = true)
        ▼
 Dispatch: SMS (mnotify and/or Termux) + voice (mnotify online, ring-only offline)
```

### Key Components
Same list as under 2.7 — restate briefly, or merge these two subsections when you write the
chapter (the TOC has them nearly adjacent).

### 2.9 System Architecture

Describe as a three-layer architecture:

1. **Presentation layer** — Streamlit dashboard (`ui/main_v2.py`), runs the video render loop,
   shows detections, exposes controls (confidence threshold, AI on/off, dispatch settings).
2. **Intelligence layer** — DETR (always-on, background inference thread decoupled from the
   render loop so display stays smooth) + Ollama-hosted `qwen2.5vl:3b` verifier, invoked only on
   flagged frames.
3. **Dispatch layer** — `agentic/tools.py`/`agentic/utils.py`, branches on `DISPATCH_MODE`
   (online/offline) to mnotify (cloud SMS/voice API) and/or the Termux phone gateway
   (`termux_gateway/sms_server.py`, running on a physical Android phone, reachable over local
   Wi-Fi hotspot).

**[Your input needed]** — redraw this as a proper architecture/component diagram (boxes and
arrows) for the actual figure; the description above is the content to diagram.

### 2.10 Components Designs and Components Descriptions

**● Data Flow**

1. Frame captured from the video source (`cv2.VideoCapture` or file read).
2. Frame handed to the background DETR inference worker (non-blocking — the render loop never
   waits on it; it always processes the latest available frame and drops what it can't keep up
   with).
3. If a DETR detection's confidence exceeds the configured threshold (default 0.6), the frame and
   an alert string go to `run_incident_response()` (`agentic/agents.py`).
4. The verifier returns a structured `IncidentVerdict` (observations, is_accident, sms_description,
   voice_message) — validated by Pydantic, `extra="forbid"`/`strict=True`, so a malformed response
   fails safe (treated as no dispatch, never a silent pass-through).
5. If `is_accident` is true, `send_incident_report()` and `send_voice_incident_report()`
   (`agentic/tools.py`) fire, branching on `DISPATCH_MODE`.

**● User Interaction**

- Operator adds one or more feeds (camera index, RTSP/HTTP stream, or video file) via the
  dashboard.
- Operator toggles "Real-time Detection" on/off, sets the confidence threshold, and sets emergency
  contacts (`phone_numbers.txt`).
- Live feed(s) render continuously with detection overlays (bounding boxes, labels) when AI
  detection is on.
- Confirmed incidents appear in an incident console; SMS/voice dispatch happens automatically, no
  operator action required.

### 2.11 Development Tools and Environment

From `pyproject.toml` and the actual stack used:

| Category | Tool / library |
|---|---|
| Language / runtime | Python 3.13 |
| Package manager | `uv` |
| Dashboard framework | Streamlit |
| Object detection | HuggingFace `transformers` pipeline, DETR (`hilmantm/detr-traffic-accident-detection`), PyTorch/`torchvision` (CUDA `cu126` build for GPU) |
| Video/image processing | OpenCV (`opencv-python`) |
| Verification LLM/VLM | `qwen2.5vl:3b`, served locally via Ollama, orchestrated with `langchain-ollama` |
| Structured output validation | Pydantic |
| Text-to-speech (offline) | Pocket TTS (`pocket-tts`), replacing an earlier gTTS (cloud) dependency |
| Online SMS/voice dispatch | mnotify API (`httpx`) |
| Offline SMS/voice dispatch | Termux + Termux:API, custom `sms_server.py` gateway running on an Android phone over local Wi-Fi hotspot |
| Version control | Git / GitHub |
| Earlier prototyping | Pygame (traffic-intersection simulation, `simulation.py`/`main.py`) — an earlier testbed, not part of the final detection pipeline |

**Development machine:** describe your actual hardware here — **[Your input needed]** (CPU model,
optional MX250 GPU already referenced throughout the benchmarks as the discrete-GPU test target).

### 2.12 Benefits of Implementation of the Proposed System

- Removes the dependency on a bystander noticing and reporting an accident.
- Two-stage design measurably reduces false alarms vs. a single detector alone (precision
  60.0% → 86.7% at the deployed configuration — see Chapter 4).
- Fully offline capability (bar the one documented gap) means the system can be deployed where
  cloud-dependent alternatives can't — directly relevant to the KMA pilot-deployment conversation.
- Low hardware/infrastructure cost: open-weight local models, a repurposed old phone as the
  dispatch gateway.

---

## CHAPTER 3: REQUIREMENTS SPECIFICATIONS

### 3.1 Requirement Gathering

- Initial requirements set by the project's own aim (accident detection + automated dispatch).
- **Refined through supervisor and stakeholder engagement**: a meeting with the supervising T.A.
  produced a concrete requirement — offline and online must be explicit, separately launched
  modes rather than mixed automatically (`report.md`, updated note at the top, dated 2026-07-22).
  The KMA demo (**[confirm your date]**) further validated the offline-deployment requirement as
  a real, not hypothetical, need.

### 3.2 Functional Requirements

1. The system shall ingest live camera and recorded video feeds.
2. The system shall detect candidate accident frames using an object detector in real time.
3. The system shall allow the operator to configure a confidence threshold for triggering
   verification.
4. The system shall verify a flagged frame using a second AI model before any alert is dispatched.
5. The system shall dispatch an SMS alert describing the incident and location to configured
   emergency contacts on a confirmed accident.
6. The system shall dispatch a voice alert (spoken, online mode; attention-getting ring, offline
   mode) on a confirmed accident.
7. The system shall support two explicit dispatch modes — online and offline — selected at launch.
8. The system shall provide a live dashboard for monitoring feeds and incidents.
9. The system shall log/benchmark detection and verification results against a labelled test set.

### 3.3 Non-Functional Requirements

- **Reliability:** a malformed or failed verification response must never result in an
  unvalidated dispatch (fail-safe by design — `agentic/agents.py`'s try/except around the
  verifier call).
- **Performance:** display loop should render smoothly (dashboard paces itself relative to
  detection cadence: ~0.4s/frame GPU, ~3s/frame CPU for DETR).
- **Availability/offline-capability:** core detection and verification must function with zero
  internet connectivity; only the online dispatch path and the spoken-voice-call feature require
  connectivity.
- **Usability:** dashboard controls (thresholds, feed management, AI on/off) must be operable
  without touching code.
- **Accuracy:** verification stage must be evaluated against a held-out, hand-labelled test set,
  not assumed correct.

### 3.4 UML Diagrams

**[Your input needed — draw these in a UML tool, e.g. draw.io/Lucidchart]**. What each should
show, based on the actual system:

- **Use Case Diagram:** Actor = Operator/Monitoring Station. Use cases: configure feed, set
  threshold, view live feed, receive incident alert (SMS/voice), review incident console.
- **Sequence Diagram:** Frame capture → DETR detection → (if flagged) verifier call → (if
  confirmed) SMS dispatch + voice dispatch, showing the online/offline branch.
- **Activity Diagram:** The two-stage gate decision flow (from 2.8's pipeline diagram).
- **Class/Component Diagram:** `IncidentVerdict` schema, dispatch functions
  (`send_incident_report`, `send_voice_incident_report`), the background inference worker.

### 3.5 Project Design Consideration (Logical Designs)

- **Verdict schema** (`agentic/agents.py`) — the actual data contract between the verifier and the
  dispatch layer:
  ```python
  class IncidentVerdict(BaseModel):
      observations: str      # forces reasoning before the verdict
      is_accident: bool
      sms_description: str   # empty if not an accident
      voice_message: str     # empty if not an accident
  ```
  Field order matters: `observations` is generated before `is_accident`, which preserves a
  chain-of-thought effect that measurably improved accuracy on the small local model.
- **Fail-safe design:** any parsing/validation error from the verifier is treated as "no
  dispatch" (`FALSE POSITIVE: verifier output failed validation ...`), never as a silent pass.
- **Decoupled inference:** DETR runs in a background thread against whatever frame is "latest,"
  independent of the render loop, so a slow model never blocks smooth video display.
- **Dispatch mode as a plain environment variable** (`DISPATCH_MODE`), so it composes with any
  launch method rather than being a hardcoded branch — a deliberate design choice for flexibility
  between demo/lab and field deployment.

---

## CHAPTER 4: IMPLEMENTATION AND RESULTS

### 4.1 Overview

Summarize: the system was implemented as a Streamlit dashboard driving a two-stage detection
pipeline with dual-mode (online/offline) dispatch, built and refined iteratively with each stage
benchmarked against a real, hand-labelled test set before being adopted (see Chapter 2.6).

### 4.1 Mapping Logical Design onto Physical Platform

*(Note: this repeats "4.1" in your outline — likely meant to be 4.2 in the original numbering;
keep as given or renumber when you finalize.)*

- **Compute:** runs on a standard laptop; DETR inference on CPU or, if available, a discrete GPU
  (tested on an MX250) via `run_on_cpu.py`/`run_on_gpu.py`.
- **Verifier model hosting:** `qwen2.5vl:3b` served locally through Ollama — no external API.
- **Dispatch hardware:** an old Android phone running Termux + Termux:API as a standalone SMS/call
  gateway (`termux_gateway/sms_server.py`), reachable from the laptop over the phone's own Wi-Fi
  hotspot — this is the concrete offline "physical platform" for dispatch.
- **Launch configuration:** two independent axes, both plain env-var driven — compute
  (`run_on_cpu.py` / `run_on_gpu.py`) and dispatch mode (`runner_offline.sh` / `runner_online.sh`).

### 4.2 Construction

Walk through what was actually built, module by module:

- `ui/main_v2.py` — the dashboard: feed management, live render loop, detection overlay, controls,
  incident console.
- `agentic/agents.py` — the structured-output verifier (`qwen2.5vl:3b` + Pydantic schema).
- `agentic/tools.py` / `agentic/utils.py` — dispatch functions, mode branching, phone-number
  handling, TTS audio generation.
- `termux_gateway/sms_server.py` — the on-phone HTTP server exposing `/sms` and `/call` endpoints.
- `agentic/benchmark_detr_hybrid.py` — the benchmarking harness comparing DETR-only vs. the full
  hybrid pipeline across thresholds.
- Build order (from `PROGRESS.md`, useful as a "how it was constructed" narrative): core pipeline
  → GPU support + decoupled inference → offline SMS gateway → offline call (ring) → local LLM
  verifier (first `gemma4:e2b`, evaluated, then switched to `qwen2.5vl:3b`) → structured-output
  rewrite (replacing an earlier, less reliable tool-calling agent) → full-scale benchmarking →
  explicit online/offline modes → dashboard redesign.

### 4.3 TESTING

This is where your real numbers go — pull directly from `report.md` §4 and `results.md`:

**Test set:** 54 hand-labelled frames (24 accidents, 30 normal traffic), including deliberately
hard cases (night footage, distant CCTV angles, shadows/motion blur).

**DETR-only vs. hybrid, at two confidence thresholds:**

| Threshold | Approach | Accuracy | Precision | Recall | Avg. time/frame |
|---|---|---|---|---|---|
| 0.85 | DETR-only | 55.6% | 50.0% | 25.0% | ~0.4s |
| 0.85 | Hybrid | 61.1% | 80.0% | 16.7% | ~27s |
| 0.6 | DETR-only | 66.7% | 60.0% | 75.0% | ~0.4s |
| 0.6 | **Hybrid (adopted)** | **75.9%** | **86.7%** | 54.2% | ~55s |

**Model comparison (earlier, 9-item calibration set, for choosing the verifier):**

| Model | Where it runs | Recall | Precision | Latency |
|---|---|---|---|---|
| Gemini 2.5 Flash | Online only | 100% | 100% | ~10s |
| qwen2.5vl:3b (adopted) | Fully offline | 66.7% | 100% | ~90s |
| gemma4:e2b (earlier candidate) | Fully offline | 33.3% | 100% | ~66s |

**Key findings to write up:** the hybrid stage improves precision at both thresholds tested; the
originally-planned stricter threshold (0.85) was too conservative and filtered out most real
accidents before verification ever saw them; lowering the threshold to 0.6 combined with the
hybrid check gives the best overall accuracy/precision found, at a real (roughly 130×) per-frame
time cost, judged acceptable since alerts are still delivered within about two minutes; and there
is an unresolved, honestly-documented recall gap (the offline verifier rejects some real accidents
a cloud model or the detector alone would have caught) — framed in `report.md` §4 as an active
open question, not a hidden weakness.

---

## CHAPTER 5: FINDINGS AND CONCLUSION

### 5.0 Overview

Restate the aim (fully offline, two-stage accident detection and dispatch) and that it was met at
a measured, documented accuracy level, with one specific piece intentionally left open.

### 5.1 Summary of Main Findings

- A two-stage detector+verifier pipeline measurably outperforms a single detector on precision
  (60.0% → 86.7% at the adopted configuration), confirming the core design hypothesis.
- Threshold tuning mattered more than expected — the originally planned threshold was
  significantly too conservative.
- Small, fully-offline vision-language models are viable for this task but have a real capability
  gap against larger cloud models on subtle cases (100% vs. 66.7% recall on the hardest 6-item
  subset tested) — offline capability was still chosen over closing that gap, per the project's
  central goal.

### 5.2 Comparison with Initial Aim

- **Met:** real-time detection, two-stage verification, offline detection + offline verification,
  offline SMS dispatch, rigorous benchmarking, an explicit online/offline mode switch.
- **Not fully met:** fully offline *spoken* voice alert — offline mode currently only delivers SMS
  text plus a plain attention-getting ring call, not a spoken message, because a reliable
  zero-internet delivery path for the spoken audio wasn't finished in this project's timeframe.
  Be candid about this — it's a scoped, documented gap (`report.md` §3), not a failure.

### 5.3 Main Contributions

- A working, evaluated two-stage (fast detector + careful local VLM) accident-verification
  architecture, with a documented, reproducible benchmark methodology (`agentic/benchmark_detr_hybrid.py`,
  `results.md`) rather than an unvalidated design.
- A genuinely offline SMS/call dispatch path via a repurposed Android phone acting as its own
  gateway — a low-cost approach to a real deployment constraint.
- An explicit, empirically-grounded account of the accuracy/latency/offline-capability trade-offs
  involved in choosing a small local model over a larger cloud one for a safety-relevant decision.

### 5.4 Limitations

- No fully offline spoken voice alert yet (see 5.2).
- Calibration/test set is 54 frames — meaningful for a final-year project but small by
  production-ML standards; not exhaustively swept across every threshold value.
- `termux-telephony-call` has a known Android background-restriction reliability issue on newer
  Android versions (documented upstream: termux-api-package#197) — not fully verified in the
  screen-off/backgrounded state on the deployment phone.
- The offline verifier trades away some recall relative to both the detector-alone configuration
  and a cloud-hosted alternative — an open, not-yet-closed question at time of writing.
- Test footage so far is largely international/generic; locally-sourced Ghana accident footage was
  still being incorporated as of the last progress entry.

### 5.5 Suggestions for Future Research and Development

- Close the offline spoken-voice-call gap (the audio itself already generates fully offline via
  Pocket TTS — only the call-delivery path is missing).
- Evaluate a larger, still-fully-local vision-language model to see whether the recall gap against
  the cloud model can be closed without giving up offline capability.
- Fine-tune (SFT) a Qwen2.5(-VL)-based model specifically on accident-scene imagery to produce
  richer, more useful scene explanations for responders (beyond the current yes/no + short
  description) — already identified as the concrete next stage of this project, including a
  planned undergraduate paper built around it.
- Expand the calibration set, particularly with locally-sourced Ghana footage, to better validate
  generalisation to the actual target deployment environment.
- Pilot deployment at the specific Kumasi intersections discussed with KMA, to get real-world
  operational data beyond the lab-benchmarked results in this report.
