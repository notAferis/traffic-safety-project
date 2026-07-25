"""
agents.py
---------
Structured-output incident verifier: the LLM is given an alert + image and returns a
JSON-schema-constrained verdict (no tool-calling involved), which is then used to decide
in plain Python whether to actually dispatch SMS/voice reports.

Public API:
  run_incident_response(alert: str, location: str, image_base64: str = None,
                         contacts: list[str] = None, verification_confidence_threshold: float = 0.8) → str
"""

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

try:
    from agentic.models import IncidentVerdict
    from agentic.prompts import INCIDENT_RESPONSE_PROMPT
    from agentic.tools import send_incident_report, send_voice_incident_report
except ModuleNotFoundError:
    # pyrefly: ignore [missing-import]
    from models import IncidentVerdict
    # pyrefly: ignore [missing-import]
    from prompts import INCIDENT_RESPONSE_PROMPT
    # pyrefly: ignore [missing-import]
    from tools import send_incident_report, send_voice_incident_report

load_dotenv()

# ---------------------------------------------------------------------------
# Shared LLM — runs fully offline via Ollama (no internet/API key required)
llm = ChatOllama(
    model="qwen2.5vl:3b",
    temperature=0,
    top_k=1,
    seed=42,
)


# ---------------------------------------------------------------------------
# Structured verdict schema. Field order is generation order — `observations`
# comes first so the model reasons before committing to `is_accident`.
# ---------------------------------------------------------------------------

# method="json_schema" is pinned explicitly (rather than relying on the library default) since
# this is a hard requirement: constrained decoding + Pydantic validation, never tool-calling
# fallback, so unsupported models (e.g. qwen2.5vl) fail loudly instead of silently misbehaving.
verifier = llm.with_structured_output(IncidentVerdict, method="json_schema")


# ---------------------------------------------------------------------------
# Helper runner
# ---------------------------------------------------------------------------
def run_incident_response(
    alert: str,
    location: str,
    image_base64: str = None,
    contacts: list[str] = None,
    verification_confidence_threshold: float = 0.8,
) -> str:
    """
    Feed an incident alert and optional image to the incident verifier, then dispatch
    SMS/voice reports directly in Python based on its structured verdict.

    Args:
        alert: Natural-language description of the incident (context for the model).
        location: The known location of the incident, used directly for dispatch —
            not extracted from the alert text, so a small model can't mangle it.
        image_base64: Optional base64 encoded image string of the accident scene.
        contacts: Recipient phone numbers, sourced from the dashboard's Contacts tab —
            passed straight through to the dispatch functions.
        verification_confidence_threshold: Minimum verdict.confidence_score required to
            actually dispatch. is_accident=True alone is not enough — a low-confidence
            "yes" is still treated as a false positive. Sourced from the dashboard's
            Verification Confidence Threshold slider (default 0.8).

    Returns:
        A confirmation string, or a "FALSE POSITIVE: ..." string if rejected.
    """
    print("\n" + "=" * 60)
    print("🚨  INCIDENT VERIFIER")
    print("=" * 60)

    if image_base64:
        content_blocks = [
            {"type": "text", "text": alert},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
        ]
        message = HumanMessage(content=content_blocks)
    else:
        message = HumanMessage(content=alert)

    try:
        verdict: IncidentVerdict = verifier.invoke(
            [SystemMessage(content=INCIDENT_RESPONSE_PROMPT), message]
        )
    except Exception as e:
        # Fail safe: an unparseable/invalid verdict must never fall through to a real dispatch.
        answer = f"FALSE POSITIVE: verifier output failed validation ({e})"
        print(answer)
        return answer

    print(f"\nVerdict: {verdict}")

    if not verdict.is_accident:
        answer = f"FALSE POSITIVE: {verdict.observations} (model verdict: not an accident)"
        print(answer)
        return answer

    if verdict.confidence_score < verification_confidence_threshold:
        answer = (
            f"FALSE POSITIVE: {verdict.observations} "
            f"(verifier confidence {verdict.confidence_score:.2f} below the "
            f"{verification_confidence_threshold:.2f} dispatch threshold)"
        )
        print(answer)
        return answer

    send_incident_report(location, verdict.observations, contacts=contacts)
    send_voice_incident_report(verdict.observations, contacts=contacts)

    answer = (
        "Incident reports have been sent.\n"
        f'Report: "{verdict.observations}"'
    )
    print("\nAgent Response:\n", answer)
    return answer

