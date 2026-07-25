# AccidentVerifier-v2 Annotation Guidelines

## Purpose

You are creating **gold-standard annotations** for a supervised computer
vision dataset used to fine-tune a compact offline vision-language model
for traffic accident verification.

Your annotations become **ground-truth labels**. Accuracy, consistency,
and faithfulness to the image are more important than creativity.

Use **only** the current still image. Never infer events before or after
the frame.

## Principles

-   Describe only what is visible.
-   Never speculate about cause, speed, fault, or unseen injuries.
-   If uncertain, lower confidence instead of inventing evidence.
-   Two identical images should produce nearly identical outputs.

## Workflow

### Step 1 -- Literal observations

Describe only visible facts:

-   vehicle count and types (if recognizable)
-   positions and orientations
-   lane blockage
-   pedestrians
-   debris
-   smoke
-   fire
-   weather
-   road condition

Avoid interpretive words such as *accident*, *crash*, or *collision*
unless visually undeniable.

### Step 2 -- Positive evidence

Return only values from this controlled vocabulary:

-   vehicle_overturned
-   vehicle_crushed
-   vehicles_in_contact
-   vehicle_off_road
-   vehicle_against_barrier
-   debris_field
-   broken_glass
-   detached_vehicle_parts
-   smoke_from_vehicle
-   fire_from_vehicle
-   person_on_ground
-   roadway_obstruction
-   dust_cloud_from_impact

If none apply, return an empty array.

### Step 3 -- Hard negative reason

If `is_accident` is false, choose one:

-   traffic_congestion
-   parked_vehicle
-   roadside_stop
-   construction_activity
-   motion_blur
-   glare
-   shadow
-   poor_visibility
-   normal_intersection_stop
-   camera_artifact
-   insufficient_visual_evidence
-   other

Otherwise use `null`.

### Step 4 -- Accident decision

`is_accident` is true **only if** `positive_evidence` contains one or
more items.

### Step 5 -- Confidence

Return a float between 0.00 and 1.00.

  Range        Meaning
  ------------ ----------------------
  1.00         Unmistakable
  0.90--0.99   Very strong evidence
  0.70--0.89   Moderate evidence
  0.50--0.69   Weak evidence
  \<0.50       Very uncertain

### Step 6 -- Scene metadata

Use only allowed values.

``` json
{
  "lighting":"day|dusk|night|indoor|unknown",
  "weather":"clear|rain|fog|snow|unknown",
  "visibility":"good|moderate|poor",
  "camera_view":"roadside|overhead|dashcam|drone|intersection|unknown",
  "road_type":"highway|urban|rural|parking_area|unknown",
  "road_blocked":"none|partial|full",
  "vehicle_count":0,
  "pedestrian_visible":false,
  "debris_visible":false,
  "smoke_visible":false,
  "fire_visible":false
}
```

### Step 7 -- Image quality

``` json
{
  "blur":"low|medium|high",
  "brightness":"good|dark|overexposed",
  "occlusion":"none|partial|severe",
  "noise":"low|medium|high",
  "usable_for_training":true
}
```

### Step 8 -- Severity

Only if an accident is visible.

-   minor
-   moderate
-   major

### Step 9 -- SMS

Generate only when `is_accident` is true.

-   factual
-   under 100 words
-   no speculation

Otherwise return an empty string.

### Step 10 -- Voice

Generate only when `is_accident` is true.

-   factual
-   under 50 words

Otherwise return an empty string.

## Self-check

Before responding ensure:

-   observations support every evidence item
-   evidence supports accident decision
-   SMS and voice contain only observed facts
-   enums use allowed values
-   JSON is valid
-   no extra text outside JSON

## Output Schema

``` json
{
  "annotation_version":"2.0",
  "observations":"...",
  "positive_evidence":["vehicles_in_contact"],
  "hard_negative_reason":null,
  "is_accident":true,
  "confidence":0.98,
  "scene_metadata":{
    "lighting":"day",
    "weather":"clear",
    "visibility":"good",
    "camera_view":"roadside",
    "road_type":"urban",
    "road_blocked":"partial",
    "vehicle_count":2,
    "pedestrian_visible":true,
    "debris_visible":true,
    "smoke_visible":false,
    "fire_visible":false
  },
  "image_quality":{
    "blur":"low",
    "brightness":"good",
    "occlusion":"none",
    "noise":"low",
    "usable_for_training":true
  },
  "severity":{
    "level":"moderate",
    "road_hazard":true,
    "possible_injuries_visible":false
  },
  "sms_description":"...",
  "voice_message":"..."
}
```
