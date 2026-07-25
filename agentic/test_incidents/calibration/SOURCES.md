# Calibration Set — Sources & Ground Truth

54 hand-verified frames (30 negative / no accident, 24 positive / real accident), used by
`results.md`'s model benchmarks. Ground truth is encoded in the filename prefix: `neg_*` = no
accident, `pos_*` = real accident. Every image was visually inspected before labeling — none are
synthetic or model-generated.

## Original 9 (2026-07-08)

`neg_1` `neg_2` `neg_3` `pos_1`–`pos_6` — sourced and labeled in an earlier session; original
provenance notes were not preserved beyond the descriptive filenames and the summaries in
`results.md`.

## Video-extracted frames (2026-07-20): `neg_10`–`neg_30`, `pos_10`–`pos_20`

Extracted with OpenCV from the 5 source videos already in `agentic/test_incidents/` (not otherwise
attributed — treat as local project test material, not for redistribution):

| Video file | Content | Frames used |
|---|---|---|
| `video (1).mp4` | Daytime T-bone collision at "1st Ave S and Spokane" — car flipped by a pickup truck at an intersection, normal traffic before/after | `neg_10` (f25), `neg_11` (f50), `pos_10` (f76), `pos_11` (f89), `pos_12` (f101) |
| `video (2).mp4` | Night intersection, normal traffic under traffic lights/headlights — initially mislabeled as a possible accident from thumbnail review, corrected to negative after full-resolution inspection (car mid-turn, not a crash) | `neg_12` (f38), `neg_13` (f95), `neg_14` (f172) |
| `video (3).mp4` | Night intersection ("MLK & Norfolk"-style), normal traffic, no incident anywhere in the clip | `neg_15` (f29), `neg_16` (f104), `neg_17` (f194) |
| `video.mp4` | "Westlake & Denny"-style daytime intersection, normal traffic throughout | `neg_18` (f34), `neg_19` (f102), `neg_20` (f204) |
| `video-4.mp4` | 76s dashcam crash-compilation ("Car Crash Time" YouTube watermark) — multiple distinct real incidents plus normal traffic between them: an intersection collision with visible debris, a truck spilling cargo with a dust cloud, a car crushed under fallen rubble, and a roadside incident with a person down near a stopped vehicle | `neg_21` (f0), `pos_13` (f117), `pos_14` (f176), `neg_22` (f353), `neg_23` (f530), `neg_24` (f647), `pos_15` (f824), `pos_16` (f942), `pos_17` (f1001), `pos_18` (f1060), `neg_25` (f1236), `neg_26` (f1354), `pos_19` (f1590), `pos_20` (f1649), `neg_27` (f1825), `neg_28` (f2002), `neg_29` (f2179), `neg_30` (f2297) |

Frame indices are 0-based, extracted via `cv2.VideoCapture.set(CAP_PROP_POS_FRAMES, idx)`.

## Web-sourced frames (2026-07-20): `neg_31`–`neg_36`, `pos_21`–`pos_27`

Downloaded from Wikimedia Commons (public domain / Creative Commons licensed, redistribution
permitted with attribution). Source category pages:
[Category:Road accidents](https://commons.wikimedia.org/wiki/Category:Road_accidents),
[Category:Road traffic](https://commons.wikimedia.org/wiki/Category:Road_traffic).

| File | Original Commons file | Label |
|---|---|---|
| `neg_31_autobahn_highway_normal.jpg` | Autobahn_A6_0480.jpg | negative |
| `neg_32_balikpapan_traffic_normal.jpg` | Balikpapan_Traffic.jpg | negative |
| `neg_33_bucharest_street_normal.jpg` | Bucharest_Traffic_2x.JPG | negative |
| `neg_34_chiangmai_traffic_normal.jpg` | Chiangmai_traffic.jpg | negative |
| `neg_35_coventry_ringroad_dusk_normal.jpg` | Coventry_Ring_Road_at_dusk.jpg | negative |
| `neg_36_hanoi_traffic_normal.jpg` | Hanoi_traffic.jpg | negative |
| `pos_21_airbags_deployed_damage.jpg` | Car_crash_nobody_hurt_airbags_deployed.jpg | positive |
| `pos_22_suv_frontend_crash_responders.jpg` | Car_crash_scene_with_police_nobody_hurt.jpg | positive |
| `pos_23_porsche_frontend_crash.jpg` | Crash_of_a_Porsche.jpg | positive |
| `pos_24_suv_crashed_into_storefront.jpg` | Car_accident_1.JPG | positive |
| `pos_25_overturned_car_night_responders.jpg` | Coche_volcado_12.jpg | positive |
| `pos_26_overturned_truck_debris_responders.jpg` | September_26,_2007_accident,_highway_9,_CT,_flipped_truck.jpg | positive |
| `pos_27_ambulance_stretcher_guardrail_wreck.jpg` | Rollover_on_101.jpg | positive |

Fetched via `https://commons.wikimedia.org/wiki/Special:FilePath/<filename>`. Each was opened and
visually confirmed (real crash damage / emergency response for `pos_*`, no incident visible for
`neg_*`) before inclusion — not accepted on filename/category alone.

## Notes for reuse

- Any benchmark script can rebuild ground truth generically from the filename prefix instead of a
  hardcoded per-item dict (`"positive" if name.startswith("pos") else "negative"`), since that
  convention is now enforced across all 54 items.
- The set skews toward more dramatic/unambiguous positives (overturned vehicles, visible debris,
  emergency response) since those are the easiest to verify by eye from a still frame. It likely
  still under-represents subtle damage (e.g. minor dents, no debris) relative to real-world accident
  distributions — worth stating as a limitation in the dissertation.
