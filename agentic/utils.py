import httpx
from dotenv import load_dotenv
import os

load_dotenv()

endPoint = 'https://api.mnotify.com/api/sms/quick'
apiKey = os.getenv('API_KEY')
url = endPoint + '?key=' + apiKey

def send_sms(recipients: list[str], message: str):
    data = {
        "recipient": recipients,
        "sender": "TrafqReport",
        "message": message,
        "schedule_date": "",
    }
    response = httpx.post(url, json=data)
    print(response.json())


def send_sms_offline(recipients: list[str], message: str):
    """
    Sends SMS via a local Termux gateway running on an Android phone, using the
    phone's own SIM over the cellular network. No internet or external API involved.

    Requires SMS_GATEWAY_URL to be set, e.g. http://<phone-ip>:8080/sms
    """
    gateway_url = os.getenv("SMS_GATEWAY_URL")
    if not gateway_url:
        print("SMS_GATEWAY_URL is not set; cannot send offline SMS.")
        return

    headers = {}
    token = os.getenv("SMS_GATEWAY_TOKEN")
    if token:
        headers["X-Auth-Token"] = token

    response = httpx.post(
        gateway_url, json={"recipients": recipients, "message": message}, headers=headers
    )
    print(response.json())


def _call_gateway_url() -> str | None:
    base = os.getenv("SMS_GATEWAY_URL")
    if not base:
        return None
    if base.endswith("/sms"):
        return base[: -len("/sms")] + "/call"
    return base.rstrip("/") + "/call"


def send_call_offline(recipients: list[str]):
    """
    Places a real phone call via the same local Termux gateway used for offline SMS, using
    the phone's own SIM (termux-telephony-call). This is a plain ring to the first recipient
    to get their attention and prompt them to check the SMS that was just sent — not a way to
    deliver a spoken message (that's still send_voice_alert, over mnotify).

    Requires SMS_GATEWAY_URL to be set (same variable as offline SMS); the /call endpoint is
    derived from it automatically.
    """
    call_url = _call_gateway_url()
    if not call_url:
        print("SMS_GATEWAY_URL is not set; cannot place offline call.")
        return

    headers = {}
    token = os.getenv("SMS_GATEWAY_TOKEN")
    if token:
        headers["X-Auth-Token"] = token

    response = httpx.post(call_url, json={"recipients": recipients}, headers=headers)
    print(response.json())


_tts_model = None
_tts_voice_state = None


def _get_tts_model():
    """Lazily loads and caches the Pocket TTS model (CPU, runs fully offline)."""
    global _tts_model, _tts_voice_state
    if _tts_model is None:
        from pocket_tts.default_parameters import get_default_voice_for_language
        from pocket_tts.models.tts_model import TTSModel

        _tts_model = TTSModel.load_model()
        _tts_model.to("cpu")
        voice = get_default_voice_for_language(None)
        _tts_voice_state = _tts_model.get_state_for_audio_prompt(voice)
    return _tts_model, _tts_voice_state


def generate_tts_audio(text: str) -> str:
    """
    Generates a TTS audio file from the text using Pocket TTS (offline, CPU-only).
    Saves it to a temporary wav file and returns the path.
    """
    try:
        import tempfile

        from pocket_tts.data.audio import stream_audio_chunks

        tts_model, voice_state = _get_tts_model()
        audio_chunks = tts_model.generate_audio_stream(
            model_state=voice_state, text_to_generate=text
        )
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        stream_audio_chunks(temp_file.name, audio_chunks, tts_model.config.mimi.sample_rate)
        return temp_file.name
    except Exception as e:
        print(f"Error generating TTS audio: {e}")
        return None


def send_voice_alert(recipients: list[str], voice_file_path: str):
    endPoint = 'https://api.mnotify.com/api/voice/quick'
    apiKey = os.getenv('API_KEY')
    url = endPoint + '?key=' + apiKey
    
    content_type = 'audio/mpeg' if voice_file_path.endswith('.mp3') else 'audio/wav'
    with open(voice_file_path, 'rb') as f:
        files = {'file': (os.path.basename(voice_file_path), f, content_type)}
        data = {
            'campaign': 'First Voice Campaign',
            'recipient[]': recipients,
            'voice_id': '',
            'is_schedule': 'false',
            'schedule_date': ''
        }
        response = httpx.post(url, data=data, files=files)
        print(response.json())
