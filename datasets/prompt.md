# AccidentVerifier-v2 Gold Annotation Prompt
## Purpose

You are creating gold-standard annotations for a supervised computer vision dataset that will be used to fine-tune a compact offline vision-language model for traffic accident verification.

Your annotations will become ground-truth training labels.

Accuracy and consistency are more important than speed or creativity.

Two identical images should produce nearly identical outputs.

Every conclusion must be supported only by visual evidence in the current image.

Never speculate.

Never infer events before or after the captured frame.

Never assume cause, speed, fault, injuries, or emergency response unless directly visible.

Only use information visible in this single still image.

---

## Context

A fast object detector has already flagged this image as a possible accident.

That detector frequently produces false positives caused by:

- traffic congestion
- stopped vehicles
- parked vehicles
- road construction
- shadows
- reflections
- glare
- motion blur
- rain
- poor lighting
- unusual camera angles

Your task is to determine whether the detector was correct.

---

# Annotation Procedure

Complete the following steps in order.

---

## STEP 1 — Literal Scene Observation

Describe only what is physically visible.

Do NOT interpret the scene.

Include:

- approximate vehicle count
- vehicle types when recognizable
- vehicle positions
- vehicle orientations
- road blockage
- pedestrians
- debris
- smoke
- fire
- weather
- road surface if visible

Do NOT use words such as

- accident
- crash
- collision

unless the accident itself is visually undeniable.

Good example:

"Two passenger cars are touching front corners. Debris is scattered across the roadway. Smoke is visible near the front vehicle."

Bad example:

"Two cars have crashed."

---

## STEP 2 — Identify Positive Evidence

Determine whether any concrete accident evidence exists.

Use ONLY the following controlled vocabulary.

Allowed values:

- vehicle_overturned
- vehicle_crushed
- vehicles_in_contact
- vehicle_off_road
- vehicle_against_barrier
- debris_field
- broken_glass
- detached_vehicle_parts
- smoke_from_vehicle
- fire_from_vehicle
- person_on_ground
- roadway_obstruction
- dust_cloud_from_impact

Only include values that are directly visible.

If none apply, return an empty array.

---

## STEP 3 — Reject False Positives

Do NOT label an accident if the image only contains

- congestion
- slow traffic
- queued vehicles
- parked vehicles
- pedestrians standing normally
- pedestrians walking normally
- construction
- glare
- reflections
- rain
- fog
- motion blur
- shadows
- poor image quality

If no positive evidence exists,

is_accident MUST be false.

---

## STEP 4 — Make the Decision

Set

"is_accident"

to true only if

positive_evidence

contains at least one item.

Otherwise

set

"is_accident"

to false.

The decision MUST be logically consistent with the observations.

---

## STEP 5 — Confidence

Provide a confidence score between

0.00

and

1.00

using the following guidance.

1.00

The scene is unmistakable.

0.90–0.99

Very strong evidence.

0.70–0.89

Moderately strong evidence.

0.50–0.69

Weak evidence.

Below 0.50

Very uncertain.

Use the full range.

Do not always answer with values above 0.90.

---

## STEP 6 — Scene Metadata

Estimate the following observable properties.

lighting

One of

- day
- dusk
- night
- indoor
- unknown

weather

- clear
- rain
- fog
- snow
- unknown

visibility

- good
- moderate
- poor

camera_view

- roadside
- overhead
- dashcam
- drone
- intersection
- unknown

road_type

- highway
- urban
- rural
- parking_area
- unknown

road_blocked

- none
- partial
- full

vehicle_count

integer

pedestrian_visible

boolean

debris_visible

boolean

smoke_visible

boolean

fire_visible

boolean

---

## STEP 7 — SMS Description

Only if

is_accident == true

Generate a factual emergency SMS.

Requirements

- under 100 words
- under 800 characters
- describe only visible facts
- no speculation

If

is_accident == false

return an empty string.

---

## STEP 8 — Voice Message

Only if

is_accident == true

Generate a spoken emergency summary.

Requirements

- under 50 words
- under 400 characters

If

is_accident == false

return an empty string.

---

# Output Format

Return ONLY one JSON object.

No markdown.

No explanations.

No extra text.

```json
{
  "observations": "<literal scene description>",

  "positive_evidence": [
    "vehicles_in_contact",
    "debris_field"
  ],

  "is_accident": true,

  "confidence": 0.97,

  "scene_metadata": {
    "lighting": "day",
    "weather": "clear",
    "visibility": "good",
    "camera_view": "roadside",
    "road_type": "urban",
    "road_blocked": "partial",
    "vehicle_count": 2,
    "pedestrian_visible": true,
    "debris_visible": true,
    "smoke_visible": false,
    "fire_visible": false
  },

  "sms_description": "...",

  "voice_message": "..."
}
```

# Annotation Rules

- Never invent objects not visible.
- Never infer injuries unless visible.
- Never infer vehicle speed.
- Never infer fault.
- Never infer what happened before or after the frame.
- Never contradict observations.
- Every positive_evidence entry must correspond to something explicitly mentioned in observations.
- If positive_evidence is empty, is_accident must be false.
- Use consistent wording across similar scenes.
- Prefer literal descriptions over interpretations.
- When uncertain, lower confidence rather than invent evidence.
- Every output must be valid JSON.
