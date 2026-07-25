# Running the Project

This covers the AI traffic-incident detection dashboard (`ui/main_v2.py`) — live camera/video feeds,
DETR accident detection, and automatic SMS/voice incident dispatch.

## Prerequisites

- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/) package manager
- Supported platforms: Linux x86_64 and macOS (Apple Silicon/arm64)
- (Optional) NVIDIA GPU with CUDA for faster detection on Linux — this project is set up for
  `cu126` wheels there. On Apple Silicon Macs, `uv sync` instead installs the standard PyPI
  `torch`/`torchvision` build, which has Metal (MPS) support built in — DETR auto-detects and uses
  it (falling back to CPU if unavailable), no extra setup needed.
- (Optional) An old Android phone for fully offline SMS dispatch (see below)

## 1. Install dependencies

```sh
uv sync
```

This installs everything pinned in `uv.lock` — the CUDA build of `torch`/`torchvision` on Linux,
or the standard MPS-enabled build on macOS.

## 2. Configure environment variables

Create a `.env` file in the project root:

```env
API_KEY = "your-mnotify-api-key"

# Optional — only needed for offline SMS/call via a phone, see section 4
SMS_GATEWAY_URL = "http://<phone-ip>:8080/sms"
SMS_GATEWAY_TOKEN = "optional-shared-secret"
```

- `API_KEY` — [mnotify](https://mnotify.com) key used for SMS/voice dispatch over the internet.
  Only required in **online mode** (see section 4a) — the accident detector (DETR) and the
  incident-verification model (`qwen2.5vl:3b` via Ollama) already run fully locally regardless of
  mode, so no API key of any kind is needed to run the AI detection itself.

## 3. Set emergency contacts

Edit `phone_numbers.txt` in the project root — a comma-separated list of numbers to notify on a
detected incident:

```
0540552725,0551234567
```

## 4. Run the dashboard

Launching is controlled along two independent dimensions — **compute** (GPU vs CPU) and
**dispatch mode** (online vs offline) — all of which just launch `streamlit run ui/main_v2.py`
underneath with different environment variables set.

### 4a. Dispatch mode — online vs offline

This is the important one for **edge / resource-constrained deployment** (e.g. running the whole
system on a laptop with no reliable internet, such as in the field in Ghana):

| Script | `DISPATCH_MODE` | Behavior |
|---|---|---|
| `bash runner_offline.sh` | `offline` | **Zero internet dependency.** Detection (DETR) and incident verification (`qwen2.5vl:3b`) already run fully locally in either mode — this setting additionally restricts *dispatch* to the Termux phone gateway only: offline SMS + an offline attention-getting ring call, both over the phone's own SIM, no mnotify/cloud API calls attempted at all. This matters in the field: without this flag, a dead connection would leave the online SMS/voice call attempt to hang until it times out before the offline channels ever fire. |
| `bash runner_online.sh` | `online` | Full dispatch: mnotify SMS + mnotify spoken voice call, **plus** the offline Termux channels as redundancy if `SMS_GATEWAY_URL` is configured. Requires `API_KEY` and internet access. |
| `bash runner.sh` | *(unset → defaults to `online`)* | Same as `runner_online.sh` — kept for backward compatibility. |

`DISPATCH_MODE` is a plain environment variable, so it composes with any launch method, e.g.:

```sh
DISPATCH_MODE=offline uv run python run_on_cpu.py
```

### 4b. Compute — GPU/MPS vs CPU

| Script | Behavior |
|---|---|
| `uv run python run_on_gpu.py` | Uses the fastest available backend for DETR inference — CUDA GPU on Linux, Metal (MPS) on Apple Silicon — falling back to CPU if neither is available |
| `uv run python run_on_cpu.py` | Forces CPU-only inference, even if a CUDA GPU or MPS is present |

Accelerator vs CPU changes detection speed a lot: roughly ~0.4s/frame on an NVIDIA GPU (MX250
tested) vs ~3s/frame on CPU with the DETR model used here; MPS on Apple Silicon hasn't been
benchmarked yet in this project, but should land somewhere between those two — the dashboard paces
its display loop off whichever accelerator is actually detected. Combine with dispatch mode via
`DISPATCH_MODE=<online|offline>` as shown above.

The app opens in your browser at `http://localhost:8501`. From there you can add camera/video feeds,
enable AI detection, and watch the live incident console.

## 5. Offline SMS dispatch (required for `runner_offline.sh`, optional otherwise)

Incident SMS/call reports can go out via mnotify (`send_sms`, needs internet) and/or via an old
Android phone's own SIM with no internet required at all (`send_sms_offline` +
`send_call_offline`). Which of these actually fire is controlled by `DISPATCH_MODE` (section 4a):
in **online mode** both fire together (if the phone gateway is configured); in **offline mode**
only the phone gateway channels fire — mnotify is never called. This means the phone gateway below
**must** be set up for `runner_offline.sh` to have any dispatch channel at all; without
`SMS_GATEWAY_URL` set, offline mode would detect and verify incidents correctly but have nowhere to
send the alert.

**One-time phone setup:**

1. Install [Termux](https://f-droid.org/packages/com.termux/) and the **Termux:API** companion app
   from the *same source* (both from F-Droid, or both from the same GitHub release — don't mix).
2. In Termux: `pkg install termux-api python`
3. Grant the Termux:API app SMS **and Phone** permissions (Android Settings → Apps → Termux:API →
   Permissions). If Android doesn't prompt for the phone permission automatically, grant it manually
   via adb: `adb shell pm grant com.termux.api android.permission.CALL_PHONE`.
4. Test SMS directly: `termux-sms-send -n <a real number> "test"`.
5. Test the call directly: `termux-telephony-call <a real number>` — confirm it actually dials.

**Running the gateway:**

1. Copy `termux_gateway/sms_server.py` onto the phone (e.g. serve it from your laptop with
   `python3 -m http.server 8000` in that folder, then `curl -O http://<laptop-ip>:8000/sms_server.py`
   in Termux). If you already had an older copy of this file on the phone, re-copy it — the `/call`
   endpoint was added later and won't exist until you do.
2. Turn on the phone's Wi-Fi hotspot and connect your laptop to it (campus/shared Wi-Fi networks
   often block device-to-device traffic, so a direct hotspot connection is the reliable option).
3. On the phone: `python sms_server.py` — leave it running. It listens on port `8080`.
4. Find the phone's IP as seen from the laptop: `ip route | grep default` (the gateway address on
   the hotspot connection is the phone).
5. Set `SMS_GATEWAY_URL=http://<phone-ip>:8080/sms` in `.env` (see section 2). This one variable
   covers both endpoints — the call gateway URL is derived from it automatically.

Once running, every dispatched incident sends SMS through the phone (plus mnotify in online mode),
**and** places a real phone call from the phone's own SIM to the primary contact
(`phone_numbers.txt`, first entry) as an attention-getting nudge to check the SMS — it's just a
ring, not a spoken message.

⚠️ **Known reliability caveat**: `termux-telephony-call` has documented issues on newer Android
versions when Termux is backgrounded (screen off / app not visible) — the call can silently fail to
place due to Android's background-activity restrictions (see
[termux-api-package#197](https://github.com/termux/termux-api-package/issues/197)). SMS delivery does
not have this problem. Test the call specifically with the phone's screen off and Termux not in the
foreground before relying on it operationally — if it's unreliable in that state on your device, the
SMS dispatch is still the primary, reliable alert path.

There is still no offline path for a **spoken** message: `send_voice_incident_report` only ever
places its call via mnotify (online mode), even though the spoken audio itself is generated fully
offline with Pocket TTS — in offline mode that function is skipped entirely rather than attempted.
The offline ring above is a separate, simpler mechanism (attention-getting only, no audio payload),
not a replacement for a spoken call.

## Other entry points

- `simulation.py` / `main.py` — the standalone Pygame traffic-intersection simulation (no AI
  detection, no dispatch), unrelated to the dashboard above.
