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

import os

# ---------------------------------------------------------------------------
# Verifier Model Factory — supports Qwen2.5-VL (Local/Ollama) & Gemini 2.5 Flash (Cloud)
# ---------------------------------------------------------------------------
def get_verifier(verifier_model: str = "qwen"):
    model_choice_lower = (verifier_model or "").lower()
    if "gemini" in model_choice_lower:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY / GOOGLE_API_KEY environment variable is missing in .env")
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            google_api_key=api_key,
        )
        return llm.with_structured_output(IncidentVerdict)
    else:
        # Default: local Qwen2.5-VL via Ollama
        llm = ChatOllama(
            model="qwen2.5vl:3b",
            temperature=0,
            top_k=1,
            seed=42,
        )
        return llm.with_structured_output(IncidentVerdict, method="json_schema")


# Default fallback verifier instance
verifier = get_verifier("qwen")


# ---------------------------------------------------------------------------
# Helper runner
# ---------------------------------------------------------------------------
def run_incident_response(
    alert: str,
    location: str,
    image_base64: str = None,
    contacts: list[str] = None,
    verification_confidence_threshold: float = 0.8,
    verifier_model: str = "qwen",
) -> str:
    """
    Feed an incident alert and optional image to the incident verifier, then dispatch
    SMS/voice reports directly in Python based on its structured verdict.
    """
    print("\n" + "=" * 60)
    print(f"🚨  INCIDENT VERIFIER [{verifier_model}]")
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
        active_verifier = get_verifier(verifier_model)
        verdict: IncidentVerdict = active_verifier.invoke(
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

    report_text = (
        verdict.sms_report.strip()
        if (hasattr(verdict, "sms_report") and verdict.sms_report and len(verdict.sms_report.strip()) > 5)
        else verdict.observations
    )

    send_incident_report(location, report_text, contacts=contacts)
    send_voice_incident_report(report_text, contacts=contacts)

    answer = (
        "Incident reports have been sent.\n"
        f'Report: "{report_text}"'
    )
    print("\nAgent Response:\n", answer)
    return answer

