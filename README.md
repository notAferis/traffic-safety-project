# AI-Assisted Traffic Accident Detection and Emergency Dispatch System

<div align="center">

[![Python version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-lightgrey.svg)](./USAGE.md)

<h4>A live-monitoring dashboard that watches traffic camera footage, recognises when a real
accident has happened, and automatically dispatches SMS/voice alerts to emergency contacts —
designed to run fully offline for resource-constrained deployment environments.</h4>

</div>

-----------------------------------------

### Final-year undergraduate project (KNUST, Kumasi, Ghana)

Demoed to Kumasi Metropolitan Assembly (KMA) members, with discussion of piloting the system on
specific intersections within the city.

-----------------------------------------
### The Problem

Road traffic accidents in resource-constrained settings often go unreported for critical minutes —
no bystander calls it in, or there's no reliable connectivity to do so. This system watches live or
recorded traffic footage and closes that gap automatically, with no human needing to be watching a
screen.

### How It Works — a two-stage detection "gate"

A single AI detector alone is unreliable: strict enough to avoid false alarms and it misses real
accidents; loose enough to catch them and it fires on ordinary traffic. So every flagged frame goes
through two stages before anything is dispatched:

1. **Fast, always-on detector (DETR)** — scans every video frame in real time, flags anything that
   could plausibly be an accident. Deliberately sensitive, so it rarely misses a genuine incident.
2. **Careful, on-demand verifier (`qwen2.5vl:3b`, run fully locally via Ollama)** — looks at any
   flagged frame and decides whether it's *actually* an accident before an alert goes out, acting as
   a false-alarm filter.

Only if both stages agree does the system send an SMS report and place a voice call to configured
emergency contacts.

### Offline-First by Design

The central goal is a pipeline — detection, verification, *and* alerting — that needs no internet
connection at any stage, matching the real deployment constraint in the environments this is meant
to serve. Both AI models already run entirely on local hardware; SMS/call dispatch can route
through a repurposed Android phone acting as its own gateway over an ordinary SIM (via Termux), with
an internet-based option (mnotify) also available as a more feature-complete alternative. See
[`report.md`](./report.md) §3 for the full offline/online mode breakdown, including the one
remaining gap (a fully offline *spoken* voice alert, still in progress).

### Rigorously Evaluated

Detection and verification accuracy is benchmarked against a hand-labelled 54-frame test set, not
assumed to work — including a direct comparison of the detector alone vs. the full two-stage hybrid,
and a head-to-head comparison of candidate offline models against a cloud baseline. Full numbers and
methodology in [`results.md`](./results.md) and [`report.md`](./report.md) §4.

-----------------------------------------
### Getting Started

**Prerequisites:** Python 3.13+, [`uv`](https://docs.astral.sh/uv/). Supported platforms: Linux
x86_64 (CUDA GPU optional) and macOS/Apple Silicon (Metal/MPS accelerated automatically). See
[`USAGE.md`](./USAGE.md) for full setup, including offline SMS/call gateway configuration.

```sh
uv sync
uv run python run_on_gpu.py   # or run_on_cpu.py to force CPU
```

The dashboard opens at `http://localhost:8501`.

A [`Dockerfile`](./Dockerfile) is also provided for running the dashboard in a container (see the
file header for the GPU/MPS-passthrough caveat on Docker Desktop).

-----------------------------------------
### Documentation

| Doc | Contents |
|---|---|
| [`USAGE.md`](./USAGE.md) | Full setup and run instructions, including the offline Termux SMS/call gateway |
| [`report.md`](./report.md) | Project report — design rationale, offline/online modes, evaluation |
| [`results.md`](./results.md) | Full benchmark results and methodology |
| [`documentation.md`](./documentation.md) | Chapter-by-chapter final-year-report guide |
| [`PROGRESS.md`](./PROGRESS.md) | Running change log of the pipeline's development |

-----------------------------------------
### Acknowledgments

The project's early traffic-intersection simulation testbed (`simulation.py`/`main.py`, and the
`Demo.gif`/`images/` assets) is built on **Mihir Gandhi**'s
[Basic Traffic Intersection Simulation](https://github.com/mihir-m-gandhi/Basic-Traffic-Intersection-Simulation)
(MIT licensed), used as the starting point before the project was extended into the AI detection and
dispatch system described above.

-----------------------------------------
### License

This project is licensed under the MIT License — see [`LICENSE`](./LICENSE) for details.
