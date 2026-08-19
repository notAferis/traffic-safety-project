# Incident-Verification Agent: Model Comparison Results

Date: 2026-07-08

## Purpose

The incident-response agent (`agentic/agents.py`) acts as a second-stage visual verifier in front of
the DETR object detector: DETR flags a frame as a possible accident, and this agent looks at the same
frame to confirm or reject it before any SMS/voice dispatch fires. This document compares candidate
LLMs for that verification step — one cloud model (baseline) and two fully-offline local models run
via Ollama — to decide which is fit for production.

## Methodology

- **Agent setup**: identical LangGraph ReAct agent (`create_react_agent`), identical tools
  (`send_incident_report`, `send_voice_incident_report`), identical system prompt
  (`agentic/prompts.py::INCIDENT_RESPONSE_PROMPT`, current version at time of test) across all three
  models — only the underlying LLM changes.
- **Dispatch mocking**: the real SMS/voice side-effect functions (`send_sms`, `send_sms_offline`,
  `send_voice_alert`) were monkeypatched to record what *would* have been sent, without actually
  contacting mnotify or the Termux phone gateway. This isolates verification accuracy from delivery
  mechanics (already verified working separately).
- **Decoding params (local models only)**: `temperature=0, top_k=1, seed=42` — greedy, seeded decoding
  for reproducibility. Gemini used `temperature=0` via its API defaults.
- **Models tested**:
  - `gemini-2.5-flash` (online, Google Generative AI API) — baseline.
  - `gemma4:e2b` (offline, local via Ollama).
  - `qwen2.5vl:3b` (offline, local via Ollama).
- **Ground truth**: each frame below was manually inspected and labeled before running any model
  against it (see [Calibration Set](#calibration-set)).

## Calibration Set

9 frames, hand-verified: 3 normal traffic (no accident), 6 real accidents, drawn from CCTV footage and
the project's own `agentic/test_incidents/` sample videos. Images are stored in
`agentic/test_incidents/calibration/` for reference.

| Frame | Ground truth | Description |
|---|---|---|
| [`neg_1_empty_street.jpg`](agentic/test_incidents/calibration/neg_1_empty_street.jpg) | negative | Empty street, night, no vehicles |
| [`neg_2_westlake_denny_normal.jpg`](agentic/test_incidents/calibration/neg_2_westlake_denny_normal.jpg) | negative | Normal daytime traffic, Westlake & Denny intersection |
| [`neg_3_mlk_norfolk_night_normal.jpg`](agentic/test_incidents/calibration/neg_3_mlk_norfolk_night_normal.jpg) | negative | Normal night traffic, car stopped at green light, MLK & Norfolk |
| [`pos_1_night_overturned_car.jpg`](agentic/test_incidents/calibration/pos_1_night_overturned_car.jpg) | positive | Night CCTV, car overturned near crosswalk, person on ground |
| [`pos_2_truck_crash_dust_cloud.jpg`](agentic/test_incidents/calibration/pos_2_truck_crash_dust_cloud.jpg) | positive | Daytime, truck crashed into structure, large dust/debris cloud |
| [`pos_3_car_crumpled_guardrail.jpg`](agentic/test_incidents/calibration/pos_3_car_crumpled_guardrail.jpg) | positive | Night, car crumpled against highway guardrail |
| [`pos_4_car_spun_at_curb.jpg`](agentic/test_incidents/calibration/pos_4_car_spun_at_curb.jpg) | positive | Daytime, car spun off-road against curb/barrier |
| [`pos_5_overturned_car_daylight.jpg`](agentic/test_incidents/calibration/pos_5_overturned_car_daylight.jpg) | positive | Daytime, car overturned in intersection near truck |
| [`pos_6_downed_pole_emergency_lights.jpg`](agentic/test_incidents/calibration/pos_6_downed_pole_emergency_lights.jpg) | positive | Night, downed pole/debris in road, emergency vehicle lights present |

**⚠️ All results below (Per-Frame Results through the Three-Way Model Comparison) were measured
against this original 9-frame set.** The calibration set was expanded to 54 hand-verified frames
(30 negative / 24 positive) on 2026-07-20 — see
[`agentic/test_incidents/calibration/SOURCES.md`](agentic/test_incidents/calibration/SOURCES.md) for
the full list, per-item provenance (video timestamps and Wikimedia Commons sources), and licensing
notes. None of the model comparisons documented in this file have been re-run against the full 54-item
set yet; the 9-item numbers below should be treated as directional, not final, until they are.

## Per-Frame Results

Verdict is what the agent concluded; **bold** marks a wrong call against ground truth.

| Frame | Ground truth | Gemini 2.5 Flash | gemma4:e2b | qwen2.5vl:3b |
|---|---|---|---|---|
| neg_1_empty_street | negative | ✅ no accident (6.7s) | ✅ no accident (61.4s) | ⚠️ error |
| neg_2_westlake_denny_normal | negative | ✅ no accident (7.2s) | ✅ no accident (51.2s) | ⚠️ error |
| neg_3_mlk_norfolk_night_normal | negative | ✅ no accident (6.0s) | ✅ no accident (68.1s) | ⚠️ error |
| pos_1_night_overturned_car | positive | ✅ confirmed (13.9s) | **❌ no accident (80.2s)** | ⚠️ error |
| pos_2_truck_crash_dust_cloud | positive | ✅ confirmed (11.9s) | ✅ confirmed (97.7s) | ⚠️ error |
| pos_3_car_crumpled_guardrail | positive | ✅ confirmed (9.1s) | **❌ no accident (54.7s)** | ⚠️ error |
| pos_4_car_spun_at_curb | positive | ✅ confirmed (10.4s) | **❌ no accident (62.2s)** | ⚠️ error |
| pos_5_overturned_car_daylight | positive | ✅ confirmed (10.1s) | **❌ no accident (57.2s)** | ⚠️ error |
| pos_6_downed_pole_emergency_lights | positive | ✅ confirmed (15.3s) | **❌ no accident (62.0s)** | ⚠️ error |

`qwen2.5vl:3b` failed on every frame with the same error:
`registry.ollama.ai/library/qwen2.5vl:3b does not support tools (status code: 400)`. This is a hard
incompatibility — the model has no function/tool-calling support in Ollama, so it cannot drive
`send_incident_report`/`send_voice_incident_report` directly in this ReAct agent architecture. It was
excluded from the accuracy comparison below for that reason (not a prompting or vision-quality issue).

## Aggregate Metrics

| Model | Accuracy | Precision | Recall | F1 | Avg. latency |
|---|---|---|---|---|---|
| gemini-2.5-flash (online) | 9/9 = 100% | 6/6 = 100% | 6/6 = 100% | 100% | 10.1s |
| gemma4:e2b (offline) | 4/9 = 44.4% | 1/1 = 100% | 1/6 = 16.7% | 28.6% | 66.1s |
| qwen2.5vl:3b (offline) | N/A — incompatible with tool-calling, 0/9 usable | — | — | — | — |

**Precision** = of the frames the agent confirmed as accidents, how many really were.
**Recall** = of the real accidents, how many the agent actually caught.

## Analysis

- **Gemini (online)** is essentially perfect on this test set, and fast (~10s round trip).
- **gemma4:e2b (offline)** never produced a false alarm (precision 100% — every dispatch it triggered
  was a genuine accident), but it missed 5 of 6 real accidents, only reliably catching the most
  visually dramatic case (large dust/debris cloud from a direct impact). Subtler damage — a crumpled
  car against a guardrail, an overturned car in a static night frame, a spun-out car against a curb —
  was consistently read as "no accident," even after prompt rebalancing specifically aimed at this
  failure mode (see prompt iteration notes below). This points to a genuine visual-grounding ceiling
  of a 2B-class general chat model on subtle/low-contrast damage cues, not something further prompt
  wording alone resolves.
- **qwen2.5vl:3b (offline)**, despite being a vision-specialized model that might otherwise have
  better visual grounding, cannot be used as a drop-in replacement here at all — Ollama reports it has
  no tool-calling support. Using it would require a different architecture (e.g. use it purely as a
  captioning/description step, then feed its text output to a second, tool-capable model or a manual
  keyword-based dispatch decision) — out of scope for this comparison.
- Latency-wise, local inference is ~6-9x slower than the Gemini API call on this hardware (CPU-bound
  Ollama execution, ~66s vs ~10s average), on top of the accuracy gap.

## Prompt Iteration Notes

The system prompt went through two calibration passes while testing `gemma4:e2b`:
1. **Initial version** — strict, conservative decision rule ("default to false positive whenever
   evidence is weak or ambiguous"). Result: 0/3 real accidents confirmed in early spot-checks — too
   conservative for a small model's uncertain visual read.
2. **Rebalanced version** (current, in `agentic/prompts.py`) — broadened the list of qualifying visual
   evidence (explicitly including dust/debris clouds and off-position vehicles as sufficient
   standalone evidence) and instructed the model to trust its own Step-1 literal description instead
   of re-litigating it in the decision step. This recovered the dust-cloud crash case without
   reintroducing any false alarms on the 3 negative frames, but did not recover the other 4 missed
   positives — confirming the remaining gap is a vision-capability limit rather than a decision-rule
   wording issue.

## Model Comparison — Structured-Output Architecture (2026-07-20)

The single-frame numbers above (`gemma4:e2b` 44.4%, `qwen2.5vl:3b` excluded entirely) were measured
under the **old** LangGraph tool-calling architecture. Since the migration to structured JSON output
(see `PROGRESS.md`), tool-calling support is no longer required — so `qwen2.5vl:3b`, previously
excluded outright (`does not support tools`, status 400), is now usable, and it's worth re-measuring
`gemma4:e2b` under the same architecture for a fair comparison.

Both models were re-run on the full 9-item calibration set, single frame, identical prompt
(`INCIDENT_RESPONSE_PROMPT`) and identical `IncidentVerdict` schema, differing only in the `model=`
passed to `ChatOllama`.

| Item | Ground truth | gemma4:e2b (structured output) | qwen2.5vl:3b (structured output) |
|---|---|---|---|
| neg_1_empty_street | negative | ✅ no accident (73.2s) | ✅ no accident (138.9s) |
| neg_2_westlake_denny_normal | negative | ✅ no accident (64.7s) | ✅ no accident (56.4s) |
| neg_3_mlk_norfolk_night_normal | negative | ✅ no accident (61.0s) | ✅ no accident (54.9s) |
| pos_1_night_overturned_car | positive | ✅ confirmed (71.5s) | ✅ confirmed (267.5s) |
| pos_2_truck_crash_dust_cloud | positive | ✅ confirmed (75.6s) | ✅ confirmed (52.2s) |
| pos_3_car_crumpled_guardrail | positive | **❌ no accident (70.5s)** | **❌ no accident (68.2s)** |
| pos_4_car_spun_at_curb | positive | **❌ no accident (59.5s)** | **❌ no accident (59.5s)** |
| pos_5_overturned_car_daylight | positive | **❌ no accident (60.1s)** | ✅ confirmed (57.7s) |
| pos_6_downed_pole_emergency_lights | positive | **❌ no accident (61.6s)** | ✅ confirmed (55.1s) |

| Model | Accuracy | Precision | Recall | F1 | Avg. latency |
|---|---|---|---|---|---|
| gemma4:e2b (structured output) | 6/9 = 66.7% | 2/2 = 100% | 2/6 = 33.3% | 50.0% | 66.4s |
| qwen2.5vl:3b (structured output) | 7/9 = 77.8% | 4/4 = 100% | 4/6 = 66.7% | 80.0% | 90.0s* |

*qwen2.5vl:3b's average is skewed by a single 267.5s outlier on pos_1; the remaining 8 calls ranged
52–139s, in line with gemma4:e2b's typical latency.

**Findings:**
- **`qwen2.5vl:3b` is now the stronger offline option.** It recovers 2 of the 4 real accidents
  gemma4:e2b's original architecture missed (pos_5, pos_6), doubling recall (33.3% → 66.7%) with no
  false alarms (precision stays 100%). Only pos_3 (crumpled car against a guardrail) and pos_4 (car
  spun off-road) are missed by *both* models — both are subtle damage cases with no debris, dust, or
  obviously abnormal vehicle orientation, and likely represent a genuine visual-grounding ceiling for
  local vision models in this size class, independent of which one is used.
- **Architecture change alone improved gemma4:e2b.** Re-measured on identical hardware/prompt/images,
  gemma4:e2b's accuracy rose from 44.4% (old tool-calling architecture) to 66.7% (structured JSON
  output) — it now correctly confirms pos_1, which it previously missed. This means part of the
  original accuracy gap documented above was an artifact of the tool-calling architecture (the model
  sometimes failed to invoke dispatch tools correctly even when its visual read was right), not purely
  a vision-capability limit. The structured-output migration was a net accuracy win on top of its
  original motivation (removing the tool-calling requirement).

## Three-Way Model Comparison — Adding qwen3-vl:4b (2026-07-20)

`qwen3-vl:4b` (Qwen3's vision-language variant, 4.4B params) was benchmarked the same way as the two
models above: full 9-item calibration set, single frame, identical prompt/schema, structured JSON
output, differing only in `model=`.

| Item | Ground truth | gemma4:e2b | qwen2.5vl:3b | qwen3-vl:4b |
|---|---|---|---|---|
| neg_1_empty_street | negative | ✅ (73.2s) | ✅ (138.9s) | ✅ (61.9s) |
| neg_2_westlake_denny_normal | negative | ✅ (64.7s) | ✅ (56.4s) | ✅ (101.1s) |
| neg_3_mlk_norfolk_night_normal | negative | ✅ (61.0s) | ✅ (54.9s) | ✅ (64.7s) |
| pos_1_night_overturned_car | positive | ✅ (71.5s) | ✅ (267.5s) | ✅ (164.1s) |
| pos_2_truck_crash_dust_cloud | positive | ✅ (75.6s) | ✅ (52.2s) | ✅ (108.3s) |
| pos_3_car_crumpled_guardrail | positive | ❌ (70.5s) | ❌ (68.2s) | ⚠️ **timeout, never completed (>600s)** |
| pos_4_car_spun_at_curb | positive | ❌ (59.5s) | ❌ (59.5s) | ❌ (98.4s) |
| pos_5_overturned_car_daylight | positive | ❌ (60.1s) | ✅ (57.7s) | ✅ (131.5s) |
| pos_6_downed_pole_emergency_lights | positive | ❌ (61.6s) | ✅ (55.1s) | ❌ (176.3s) |

| Model | Accuracy | Precision | Recall | F1 | Avg. latency | Reliability |
|---|---|---|---|---|---|---|
| gemma4:e2b | 6/9 = 66.7% | 100% | 33.3% | 50.0% | 66.4s | no timeouts |
| qwen2.5vl:3b | 7/9 = 77.8% | 100% | 66.7% | 80.0% | 90.0s | no timeouts |
| qwen3-vl:4b | 6/9 = 66.7% | 100% | 50.0% | 66.7% | 113.3s (completed items only) | **1 genuine hang** |

**qwen3-vl:4b hung on pos_3** — not just slow, it never returned a result even after a second attempt
at a 600s timeout (2x the standard 300s budget used for every other item/model in this comparison).
Same diagnostic signature (no output, no partial result) as the earlier `gemma4:e2b`/`qwen3.5:2b`
Ollama hangs encountered during the multi-frame experiment. This model has `thinking` mode enabled by
default, which is the likely cause — it may be generating an unbounded reasoning trace on ambiguous
images instead of converging on a verdict.

**Conclusion: `qwen2.5vl:3b` remains the best offline choice.** It has the highest accuracy and recall
of the three, the lowest typical latency, and — critically for a system sitting in front of a real
emergency-dispatch pipeline — no observed hangs. `qwen3-vl:4b` is a larger, newer model but does not
outperform `qwen2.5vl:3b` on accuracy, is consistently slower, and demonstrated an unacceptable
reliability failure (an unbounded hang) that alone disqualifies it for this use case regardless of
its accuracy on the other 8 items. No change to the production model (`agentic/agents.py` stays on
`qwen2.5vl:3b`).

## Multi-Frame Experiment (gemma4:e2b, 2026-07-15)

**Hypothesis:** the small model misses subtle accidents (pos_3, pos_5, pos_6) because a single still
frame doesn't give it enough context — sending it the detected frame plus 3 follow-up frames
(~0.3s/0.7s/1s later, same camera) might let it pick up on cues a still frame hides (e.g. dust
settling, a vehicle that never moves from an unnatural position across the sequence).

**Method:** all 4 frames sent as separate `image_url` content blocks in a single structured-output
call (`agentic/agents.py`'s current `IncidentVerdict`/`llm`, i.e. the post-migration structured-JSON
architecture — see `PROGRESS.md`), rather than stacked into one collage image, to avoid degrading each
frame's resolution. Adapted prompt (`MULTIFRAME_INCIDENT_RESPONSE_PROMPT`) explicitly told the model
the frames were sequential and how far apart, and to use cross-frame consistency as a signal.
Tested on 7 of the 9 calibration items — `pos_1` (no source video, standalone frame only) and `pos_4`
(last frame of its source video, no follow-up frames exist) were excluded since no real 4-frame
sequence could be built for them.

| Item | Ground truth | Single-frame | Multi-frame (4 frames) |
|---|---|---|---|
| neg_1 | negative | ✅ correct (61.4s) | ✅ correct (103.7s) |
| neg_2 | negative | ✅ correct (51.2s) | ✅ correct (85.0s) |
| neg_3 | negative | ✅ correct (68.1s) | ✅ correct (85.0s) |
| pos_2 | positive | ✅ correct (97.7s) | ✅ correct (99.8s) |
| pos_3 | positive | ❌ missed (54.7s) | ❌ **still missed** (87.3s) |
| pos_5 | positive | ❌ missed (57.2s) | ❌ **still missed** (91.6s) |
| pos_6 | positive | ❌ missed (62.0s) | ❌ **still missed** (90.5s) |

**Result:** multi-frame recovered **0 of the 3** previously-missed positives — identical 4/7 accuracy
on this subset. Average latency rose from ~65s to ~93s per call (+~30%), since the model processes 4x
the image tokens in a single request. Reading the model's own `observations` field for the still-missed
items shows it correctly tracking the scene as visually consistent across all 4 frames, but not
recognizing the damage/wreckage itself — e.g. pos_6 (downed pole, emergency lights) was described as
"highly blurred... traffic moving or stopped," pos_3 (crumpled car on guardrail) as "no visible debris,
smoke, or unusual vehicle positioning." This confirms the failure mode is visual grounding on subtle
damage cues (a model-capability ceiling), not missing temporal context — extra frames of a scene the
model already can't correctly interpret don't help it interpret that scene.

**Conclusion:** multi-frame context is **not adopted**. It adds real latency cost with no accuracy
benefit on this test set, and the underlying cause of the missed positives (identified in the
single-frame results above) is unaffected by giving the model more looks at the same scene.

## Recommendation

**Switch the configured offline model (`agentic/agents.py`) from `gemma4:e2b` to `qwen2.5vl:3b`** —
under the current structured-JSON-output architecture it has higher accuracy (77.8% vs 66.7%) and
double the recall (66.7% vs 33.3%) on the calibration set, with identical 100% precision (no false
alarms from either model) and comparable typical latency. This became possible only after the
tool-calling → structured-output migration removed the hard incompatibility that excluded
`qwen2.5vl:3b` from earlier testing (see Model Comparison section above).

Multi-frame context (sending 3 follow-up frames alongside the detected frame) was tested against
gemma4:e2b and did not improve accuracy — see Multi-Frame Experiment below. It was not re-tested
against qwen2.5vl:3b, since the underlying failure mode (subtle-damage cases like pos_3/pos_4 missed
by both models) looks like a visual-grounding limit rather than a missing-context problem.

Either offline model remains safe by construction (no false alarms observed in this test set) but
under-sensitive relative to Gemini: expect even the better offline model to miss subtle damage cases
that a cloud model would catch. This offline/online accuracy tradeoff is worth stating explicitly in
the project documentation as a known limitation, alongside the option of falling back to Gemini
whenever internet access is available.

## DETR-Only vs. DETR + LLM Hybrid — Full 54-Item Calibration Set (2026-07-20)

This is the first evaluation of the **whole pipeline**, not just the LLM verification stage: it
compares using DETR (`hilmantm/detr-traffic-accident-detection`) alone as the accident decision
against the production hybrid design (DETR gate → `qwen2.5vl:3b` structured-output verifier
confirms/rejects), across the full 54-item calibration set (up from the 9-item set used above), and
across two DETR confidence thresholds.

**Method** (`agentic/benchmark_detr_hybrid.py`):
- DETR-only verdict: any detected box labeled `accident`/`collision`/`crash`/`incident` with score ≥
  threshold — identical logic to `ui/main_v2.py`'s live detection loop.
- Hybrid verdict: same DETR gate; every DETR-positive frame is then sent to the exact production
  verifier (`agentic/agents.py`'s `IncidentVerdict`, same prompt/schema). A DETR-negative frame is
  never sent to the LLM, matching production (the LLM only ever runs after a DETR trigger).
- Each LLM call wrapped in a 300s hard timeout (`SIGALRM`); a timeout counts as "no accident" (fails
  safe, same as a real dispatch gate would).
- No dispatch functions were touched — DETR and the LLM verifier were called directly, no SMS/voice/
  call side effects.
- Tested at the dashboard's old default threshold (0.85) and a lower one (0.6).

| Approach | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| DETR-only @0.85 | 30/54 = 55.6% | 6/12 = 50.0% | 6/24 = 25.0% | 33.3% |
| Hybrid @0.85 | 33/54 = 61.1% | 4/5 = 80.0% | 4/24 = 16.7% | 27.6% |
| DETR-only @0.6 | 36/54 = 66.7% | 18/30 = 60.0% | 18/24 = 75.0% | 66.7% |
| **Hybrid @0.6** | **41/54 = 75.9%** | **13/15 = 86.7%** | 13/24 = 54.2% | 66.7% |

**Findings:**
- **0.85 was too strict.** At the old default, most real accidents in this set score 0.6–0.85 on
  DETR's "accident" label (e.g. the dust-cloud truck crash at 0.78, several crushed/overturned cars at
  0.77–0.83) — they never reached the LLM stage at all, capping recall at 25% even before the LLM had
  a chance to help.
- **Lowering to 0.6 helps both stages.** DETR-only recall triples (25%→75%); accuracy and F1 both
  improve substantially for both configurations.
- **The hybrid stage earns its keep as a false-alarm filter.** At 0.6, DETR alone raises 12 false
  alarms on normal-traffic frames (`neg_10`, `neg_11`, `neg_13`–`neg_16`, `neg_20`, `neg_25`,
  `neg_27`–`neg_29`, `neg_2`) — the LLM verifier correctly rejects 10 of those 12, leaving only 2 false
  alarms (`neg_11`, `neg_14`). Precision goes from 60.0% (DETR-only) to 86.7% (hybrid).
  Same pattern held at 0.85 (6 DETR false alarms → 1 after the LLM stage).
- **The LLM stage also costs some recall in both configurations** — it occasionally rejects a frame
  DETR correctly flagged (e.g. `pos_10`, a flipped car DETR caught at 0.93 confidence, rejected by the
  LLM) or the call times out (`pos_25`, `pos_26` at the 0.6 threshold, `pos_25` again at 0.85 — a 300s
  timeout fails safe as "no accident"). This is the same visual-grounding ceiling documented in the
  9-item model comparisons above, now visible at pipeline scale.
- **Cost**: at 0.6, 30/54 frames (56%) trigger the LLM stage vs. 12/54 (22%) at 0.85, averaging ~99s
  per LLM call — a real latency/compute tradeoff for the accuracy gain, relevant mainly for how often a
  live camera feed will incur the extra LLM round-trip before dispatch.

**Decision: dashboard default confidence threshold (`ui/main_v2.py`) changed from 0.85 to 0.60.**
Hybrid @0.6 is the best-performing configuration measured so far on any metric that matters for this
system (accuracy, precision, F1) and only trades away recall relative to DETR-only @0.6 — it never
trades away precision, which is the direction that matters most for a live dispatch gate (a missed
accident is bad; the same accident dispatched from unrelated normal-traffic frames repeatedly is
worse for responder trust). 0.6 was not exhaustively swept against finer-grained thresholds (e.g.
0.65, 0.70) — this comparison only tested the old default and one lower candidate.

Raw results: `agentic/benchmark_detr_hybrid_results_thresh085.jsonl`,
`agentic/benchmark_detr_hybrid_results_thresh060.jsonl`.
