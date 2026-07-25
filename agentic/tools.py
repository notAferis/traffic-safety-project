import os
from typing import Dict, List

try:
    from agentic.utils import (
        generate_tts_audio,
        send_call_offline,
        send_sms,
        send_sms_offline,
        send_voice_alert,
    )
except ModuleNotFoundError:
    # pyrefly: ignore [missing-import]
    from utils import (
        generate_tts_audio,
        send_call_offline,
        send_sms,
        send_sms_offline,
        send_voice_alert,
    )


def _is_offline_mode() -> bool:
    """
    DISPATCH_MODE controls which dispatch channels are attempted:
      - "online"  (default): mnotify SMS + mnotify spoken voice call, alongside the
        offline Termux channels (SMS + ring) for redundancy — set by runner_online.sh.
      - "offline": only the Termux gateway channels (SMS + ring) are attempted — no
        mnotify/internet call is made at all, so a dead connection in the field can't
        stall dispatch waiting on a timeout. Set by runner_offline.sh. There is no
        offline path for a *spoken* message, so send_voice_incident_report is a no-op
        in this mode; the offline ring + SMS text are the alert.
    """
    return os.getenv("DISPATCH_MODE", "online").strip().lower() == "offline"




def send_incident_report(location: str, description: str = None, contacts: List[str] = None) -> str:
    """
    Send an emergency SMS incident report to the nearby emergency services.

    Args:
        location: The location of the incident (e.g. 'Tema Community 18').
        description: A detailed description of the accident scene (e.g., vehicles, colors, license plates, civilians).
        contacts: Recipient phone numbers, sourced from the dashboard's Contacts tab
            (st.session_state.phone_numbers) by the caller — not read from disk here.

    Returns:
        A confirmation string.
    """
    if not contacts:
        print("send_incident_report: no contacts supplied; skipping dispatch.")
        return "Incident report skipped: no emergency contacts configured."

    message = f"EMERGENCY: {description}"
    offline_mode = _is_offline_mode()
    print(
        f"\n--- DISPATCHING SMS ({'offline' if offline_mode else 'online'} mode) ---\n"
        f"Recipients: {contacts}\nMessage: {message}\n---------------------"
    )
    if not offline_mode:
        try:
            send_sms(contacts, message)
        except Exception as e:
            print(f"send_sms (mnotify) failed: {e}")
    try:
        send_sms_offline(contacts, message)
    except Exception as e:
        print(f"send_sms_offline (termux gateway) failed: {e}")
    try:
        # Real phone call to the primary contact, purely to get their attention and prompt
        # them to check the SMS above — not a spoken-message call (see send_voice_incident_report).
        send_call_offline(contacts)
    except Exception as e:
        print(f"send_call_offline (termux gateway) failed: {e}")
    return f"Incident report sent for location: {location} to contacts: {', '.join(contacts)}"


def send_voice_incident_report(message: str = None, contacts: List[str] = None) -> str:
    """
    Send an emergency voice incident report to the nearby emergency services.

    Args:
        message: Optional spoken message content describing the incident.
        contacts: Recipient phone numbers, sourced from the dashboard's Contacts tab
            (st.session_state.phone_numbers) by the caller — not read from disk here.

    Returns:
        A confirmation string.
    """
    if _is_offline_mode():
        print(
            "\n--- VOICE CALL SKIPPED (offline mode) ---\nNo internet path exists for a spoken "
            "message; the offline ring + SMS text already sent by send_incident_report are the "
            "alert in this mode.\n-----------------------------"
        )
        return "Voice report skipped: DISPATCH_MODE=offline has no spoken-message delivery path."

    if not contacts:
        print("send_voice_incident_report: no contacts supplied; skipping dispatch.")
        return "Voice report skipped: no emergency contacts configured."

    audio_path = None

    if message:
        print(
            f"\n--- DISPATCHING VOICE CALL ---\nRecipients: {contacts}\nSpeech: {message}\n-----------------------------"
        )
        try:
            audio_path = generate_tts_audio(message)
        except Exception:
            pass

    if not audio_path:
        audio_path = os.path.join(os.path.dirname(__file__), "audio", "base_audio.wav")

    send_voice_alert(contacts, audio_path)

    if message and audio_path and audio_path.endswith(".mp3"):
        try:
            os.remove(audio_path)
        except Exception:
            pass

    return f"Incident report sent via voice alert to contacts: {', '.join(contacts)}"



