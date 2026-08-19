# Project Report: AI-Assisted Traffic Accident Detection and Emergency Dispatch System

**Prepared for:** Project Supervisor
**Date:** 2026-07-22

*Updated following a meeting with the supervising T.A.: the system now launches in two explicit
modes — fully offline or online — via separate launch commands, rather than mixing both
automatically. See Section 3.*

---

## 1. Project Overview

Road traffic accidents often go unreported for critical minutes because there is no one nearby to
call for help, or because bystanders are unsure who to notify. This project explores whether an
automated system can watch traffic camera footage, recognise when an accident has happened, and
immediately alert emergency contacts — without needing a human to be watching the screen at all
times.

**The project's central goal is for this to work fully offline** — with no dependence on an
internet or mobile data connection at any stage, from detection through to alerting — since the
intended real-world setting (resource-constrained environments such as Ghana) cannot assume
reliable connectivity is available where and when an accident happens. An online mode also exists
today, mainly as the more feature-complete option while the last piece of the fully-offline path
(described in Section 3) is still being worked through; it is not the end goal of the project.

The final system is a live monitoring dashboard that:

1. Watches one or more video feeds (live cameras or recorded footage) continuously.
2. Uses an AI model to spot frames that look like they might show an accident.
3. Passes any suspicious frame to a second, more careful AI check to confirm it is a genuine
   accident and not a false alarm (e.g. a shadow, glare, or normal traffic that only looks unusual).
4. If confirmed, automatically sends an SMS report and places a voice call to a list of emergency
   contacts, describing what was seen and where.

The project also includes a supporting traffic-intersection simulation (built earlier in the
project) that models vehicles moving through a signal-controlled junction, which was used as an
early testbed before the system was extended to work with real accident footage.

## 2. Why a Two-Stage Approach

An early version of the system relied on a single AI detector to decide, on its own, whether
something was an accident. In testing, this proved too unreliable on its own: a detector strict
enough to avoid false alarms missed most real accidents, while a detector loose enough to catch
real accidents also triggered constantly on ordinary traffic.

To solve this, the system was redesigned as a **two-stage "gate"**:

- **Stage 1 (fast, always-on):** a computer-vision model scans every video frame in real time and
  flags anything that could plausibly be an accident. This stage is deliberately kept sensitive, so
  it rarely misses a genuine incident.
- **Stage 2 (careful, only runs when needed):** whenever Stage 1 raises a flag, a second, more
  capable AI model — one that can reason about the image rather than just detect shapes — looks at
  the same frame and decides whether it is *actually* an accident before anything is sent out. This
  stage acts as a safety net against false alarms, since sending emergency alerts for non-events
  wastes responder time and erodes trust in the system.

Only if both stages agree does the system dispatch an SMS and voice call. This mirrors how a human
observer would naturally behave: notice something unusual first, then look more closely before
raising an alarm.

## 3. Offline Capability — the Project's Central Goal

As stated above, going fully offline is the point of this project, not an optional extra — sharpened
further after feedback from a meeting with the supervising T.A. into a concrete requirement: the
system must not depend on having a reliable internet or mobile data connection at the accident
scene, since the intended real-world deployment context (resource-constrained environments such as
Ghana) cannot assume one. The project is not finished with this goal yet — the last remaining gap is
described below — so for now, the system can be run in **two ways**, launched with a distinct,
explicit command each, while that final piece is worked out:

- **Offline mode** (`runner_offline.sh`) — the mode the project is being built towards. The entire
  pipeline runs with no internet connection required at any point. Both AI models — the fast
  first-stage scanner and the careful second-stage confirmation check — already run entirely on
  local hardware with no cloud dependency. The alert step also now runs exclusively through a
  repurposed old Android phone acting as its own SMS/call gateway over the ordinary mobile network's
  own SIM card — no internet-based service is contacted at all, and no time is lost waiting on a
  dead internet connection to time out before an alert goes out.
- **Online mode** (`runner_online.sh`, currently still the default if no mode is chosen) — the more
  feature-complete mode for now, kept mainly as the practical option while the offline path's last
  gap (below) is still being worked through. It uses a standard internet-based SMS/voice service, in
  addition to the same offline phone channels as a backup if one is connected, and it is currently
  the only mode that can deliver a phone call that speaks the incident details aloud rather than
  just ringing.

**The final piece still being worked on:** offline mode today can alert by SMS text and a plain
attention-getting ring, but not yet by a phone call that speaks the incident details aloud with no
internet involved at all. The message audio itself already generates fully offline; what's missing
is a fully offline way to deliver it over a live call. This was investigated early on and judged too
fragile to finish at the time, but since it sits directly on the path to the project's central goal,
it remains an open, active item rather than a closed decision — we are still experimenting with how
to close this last gap, not treating the two-mode setup as the final state.

Both modes are documented step by step for whoever runs the system next, so switching between a
connected demo/lab setting and a fully offline field deployment does not require touching any code.

## 4. Testing and Evaluation

Because this system's mistakes have real consequences (a missed accident delays help; a false alarm
wastes it), a substantial part of the project was dedicated to rigorously measuring accuracy rather
than assuming the design worked.

**Building a fair test set.** A set of 54 real photographs and video frames was assembled and
manually labelled by eye — 24 showing genuine accidents (overturned vehicles, visible wreckage,
emergency responders on scene, etc.) and 30 showing ordinary traffic with nothing wrong. This mix
was deliberately built to include tricky cases: night-time footage, distant CCTV angles, and normal
scenes that could easily be mistaken for accidents (e.g. queued traffic, shadows, motion blur).

**Comparing candidate AI models.** Several different AI models were tested head-to-head for the
"careful second check" role, including one cloud-based option and several models that run fully
offline. Each was scored on the same test set for accuracy, how many real accidents it correctly
caught, how many false alarms it raised, and how long it took to respond. The offline model that
performed best overall was selected for the final system.

**Standard approach vs. the two-stage hybrid, at the same sensitivity setting.** To check that the
second "careful check" stage was actually earning its keep, the project directly compared the
**standard approach** (the fast first-stage detector deciding alone, with no second opinion) against
the full **hybrid approach** (the same detector, but every flag it raises is then double-checked by
the second AI model before an alert goes out) — using the identical 54-item test set and the
identical sensitivity setting for each pairing, so the comparison isn't skewed by one side getting
an easier setting than the other. This was repeated at two sensitivity settings: the originally
planned one, and a lower one identified as worth testing.

| Sensitivity setting | Approach | Correct overall | Alerts that were genuine accidents (precision) | Real accidents caught (recall) | Average response time per frame |
|---|---|---|---|---|---|
| Original (stricter) | Standard (detector alone) | 55.6% | 50.0% | 25.0% | ~0.4 seconds |
| Original (stricter) | **Hybrid (detector + AI double-check)** | 61.1% | 80.0% | 16.7% | ~27 seconds |
| Lower (looser) | Standard (detector alone) | 66.7% | 60.0% | 75.0% | ~0.4 seconds |
| Lower (looser) | **Hybrid (detector + AI double-check)** | **75.9%** | **86.7%** | 54.2% | ~55 seconds |

The response-time figures make the trade-off concrete. The first-stage detector alone is fast
enough to run on every video frame continuously (roughly 0.4 seconds regardless of setting) — it
never needs to slow down. The AI double-check is what costs time: it only runs on the frames the
detector flags, but each check takes on average 99 seconds by itself (at the lower, adopted
setting), and since more frames get flagged at that setting, the *system-wide* average — spread
across every frame, flagged or not — rises to around 55 seconds. In other words, the accuracy gains
from the hybrid approach are not free: it is roughly 130 times slower per frame than the detector
running alone, because it deliberately trades speed for a second, more careful opinion before ever
notifying anyone. This is judged an acceptable trade for this system, since the check only ever
delays an alert by under two minutes and does not need to happen for every frame — but it is a real
cost, not a rounding error, and is factored into why the second stage exists only as a check on
top of the fast detector rather than replacing it.

Three findings came out of this side-by-side comparison:

1. **At either sensitivity setting, adding the second-stage AI check improves how trustworthy an
   alert is.** At the original stricter setting, precision rose from 50.0% to 80.0%; at the lower
   setting, from 60.0% to 86.7%. In other words, whenever the detector raises a flag, the second
   check meaningfully increases the odds that the flag is a genuine accident and not a false alarm,
   at both settings tested.
2. **The originally planned sensitivity setting was too cautious on its own.** It was filtering out
   roughly three-quarters of genuine accidents before the second stage ever got a chance to look at
   them (recall of only 25.0% for the standard approach). Lowering the sensitivity let the detector
   catch far more real accidents (recall up to 75.0%), and — importantly — the second-stage AI check
   was then able to clean up most of the extra false alarms that came with that looser setting,
   rather than simply passing them all through. The result is the best-performing configuration
   found overall: the detector at the lower sensitivity setting, combined with the AI double-check —
   76% of test cases classified correctly, and 87% of alerts genuine.
3. **That accuracy gain has a real time cost, and is not automatically "better" for every use
   case.** The hybrid approach is a genuine trade-off, not a free upgrade: it answers roughly 130
   times slower per frame than the detector alone, and it also catches fewer real accidents than the
   detector running by itself at the same lower setting (54.2% vs. 75.0% recall) — the AI
   double-check occasionally talks itself out of a real accident the detector correctly caught. For
   this project, that trade is judged worthwhile because a false alarm has a real cost (wasted
   responder time, eroded trust in the system) and a response delayed by under two minutes is
   acceptable — but it means the hybrid approach should be described as "better for this specific
   job" rather than a general, unconditional improvement over the detector alone.

This combination (lower sensitivity + hybrid double-check) was adopted as the new default for the
live dashboard. One caveat worth noting honestly: only two sensitivity settings were compared
head-to-head, not a full sweep of every possible value, so there may be a setting in between that
performs even better — this was not exhaustively searched.

**A note on priorities, revisited.** The comparison above frames the second-stage AI check as
valuable mainly because it reduces false alarms (precision). On reflection, for this system, missing
a real accident is the worse failure of the two — a false alarm wastes a few minutes of a
responder's attention, but a missed accident means nobody is told at all. Judged purely on catching
real accidents (recall), the standard detector-only approach at the lower sensitivity setting is
actually the strongest configuration measured so far (75.0% recall), ahead of the hybrid
double-check (54.2%) — the second-stage AI is currently rejecting some real accidents the detector
correctly flagged. This is a genuine open question for the project, not yet settled, and it is the
motivation for the comparison below.

**Bigger cloud models vs. smaller on-device models — the trade-off behind that open question.** One
way to recover the recall the AI double-check is currently costing is to use a larger, more capable
AI model for that check. Earlier in the project, before the full 54-item test set existed, a
smaller-scale comparison was run on 9 hand-picked test frames (6 real accidents, 3 normal scenes),
comparing a large cloud-hosted model against the small models that can run fully on local hardware:

| Model | Where it runs | Real accidents caught (recall) | False alarms (precision) | Response time |
|---|---|---|---|---|
| Large cloud model (Gemini 2.5 Flash) | **Online only** | **100%** (6/6) | 100% | ~10 seconds |
| Small on-device model (qwen2.5vl, adopted) | **Fully offline** | 66.7% (4/6) | 100% | ~90 seconds |
| Small on-device model (gemma, earlier candidate) | **Fully offline** | 33.3% (2/6) | 100% | ~66 seconds |

On this small test set, the large cloud model caught every real accident and was also faster — it
never missed a case, including subtle ones (damage with no debris, dust cloud, or obvious vehicle
overturn) that both smaller offline models missed. That result points at a real capability gap
between today's small on-device AI models and a large cloud-hosted one, at least on the hardest,
subtlest cases.

This creates a direct conflict with the project's central goal, though: routing the "careful check"
through a cloud model only works when there is internet, which is precisely the condition the
offline-first design exists to not depend on. Using it as the default would trade away the project's
main goal for a recall improvement that only exists when connectivity happens to be available — the
opposite of the target deployment reality in a resource-constrained environment. For that reason,
the current default keeps the AI check fully local, at the cost of the recall gap shown above; the
cloud model remains available only as an optional path in online mode.

Two things are worth being explicit about here, since this is unresolved rather than a finished
comparison:
- This specific comparison used only 9 test frames and an earlier version of the pipeline — it has
  not yet been re-run on the full 54-item test set or the current DETR-gated hybrid architecture, so
  the exact size of the recall gap at full scale is not yet confirmed.
- A middle option has not yet been tried: a **larger AI model that still runs fully offline** (the
  current on-device model is the smallest variant available; a bigger local model may close some of
  the recall gap without giving up the offline requirement at all). This is a natural next
  experiment rather than a closed door.

## 5. Current Status

- The end-to-end pipeline — detection, confirmation, and alert dispatch in both online and offline
  modes — is built and working, and has been tested against real footage and real phone hardware.
- The system's decision-making has been benchmarked against a hand-verified test set, with results
  and reasoning documented for future reference.
- Offline mode has been verified to correctly restrict dispatch to the phone-based channels only,
  with no attempt to reach the internet-based service. Confirming the phone-based channels
  themselves (SMS delivery and the ring call) work correctly on the real deployment phone was done
  separately and earlier in the project.
- The offline phone call feature has a known limitation on some newer Android versions where a call
  may silently fail to go through if the phone's screen is off — this is documented as a caveat
  rather than treated as resolved, and SMS remains the primary, more reliable alert channel in
  either mode.
- Work on expanding the test footage to include locally-sourced accident video (from Ghana) is in
  progress, to check how well the system generalises beyond the initial international test set.
- Closing the remaining gap in offline mode — a fully offline spoken-call alert — is an active,
  ongoing experiment (Section 3), not yet resolved; it is the last piece needed before offline mode
  is the complete, self-sufficient option the project is aiming for.
- Whether the current default configuration correctly prioritizes catching every real accident over
  avoiding false alarms is an open question under active review (Section 4) — early evidence suggests
  a larger, still-fully-offline AI model may recover missed accidents without compromising the
  offline-first goal, and testing that is a planned next step.

## 6. Summary

The project's central goal is a low-cost, two-stage AI pipeline that can reliably tell real traffic
accidents apart from ordinary footage and automatically notify emergency contacts **with no
dependence on internet connectivity at all**, matching the reality of resource-constrained
deployment environments such as Ghana. The current system meets that goal at a reasonable accuracy
level, backed by measured evidence rather than assumption, and — following the meeting with the
T.A. — now makes the offline-first focus explicit in how the system is launched and run, rather than
leaving it implicit in the code. One piece of that goal is not yet finished: fully offline delivery
of a spoken voice alert. Until that is resolved, the system offers both an offline mode (the target
end state) and an online mode (the more complete interim option), with the gap between them, and the
ongoing work to close it, clearly documented rather than glossed over.
