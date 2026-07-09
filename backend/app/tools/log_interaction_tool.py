"""
Tool 1: Log Interaction

Takes a natural-language description of a rep's visit/call/email with an
HCP, uses the LLM to extract structured fields, validates them with the
same Pydantic schema the manual form uses, and saves the record via the
shared interaction_service — so it lands in the identical `interactions`
table the form writes to.
"""

import re
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.core.llm_client import chat_completion, safe_json_parse
from app.prompts.prompts import LOG_INTERACTION_EXTRACTION_PROMPT
from app.schemas.interaction import InteractionCreate
from app.services import interaction_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

_VALID_TIME_RE = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")


def _sanitize_time(value, fallback):
    """
    The LLM sometimes returns vague phrases like 'morning' or 'afternoon'
    instead of HH:MM — or simply returns null. Rather than letting Pydantic
    reject the whole extraction, or leaving the field blank, always fall
    back to the current time (matching how `date` defaults to today) unless
    the LLM gave us a genuinely valid HH:MM value.
    """
    if isinstance(value, str) and _VALID_TIME_RE.match(value.strip()):
        return value.strip()
    if value is not None:
        logger.warning("Discarding non-standard time value from LLM extraction: %r", value)
    return fallback


def run(db: Session, user_message: str) -> dict:
    """
    Extract structured interaction data from `user_message` and persist it.

    Returns a dict with the created interaction (as a plain dict) for the
    caller (LangGraph node) to pass back to the frontend.
    """
    now = datetime.now()
    current_time_str = now.strftime("%H:%M")
    system_prompt = LOG_INTERACTION_EXTRACTION_PROMPT.format(
        today=date.today().isoformat(), current_time=current_time_str
    )

    raw = chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        json_mode=True,
    )
    extracted = safe_json_parse(raw)
    logger.info("Log Interaction tool extracted fields: %s", extracted)

    # Defensive defaults so a partially-confident LLM extraction still validates.
    extracted.setdefault("hcp_name", "Unknown HCP")
    extracted.setdefault("interaction_type", "In-Person")
    extracted.setdefault("date", date.today().isoformat())
    # ALWAYS ends up with a real HH:MM value — either what the LLM gave us,
    # or the current time as a fallback. Never left blank.
    extracted["time"] = _sanitize_time(extracted.get("time"), fallback=current_time_str)
    if not extracted.get("attendees"):
        extracted["attendees"] = extracted["hcp_name"]

    interaction_data = InteractionCreate(**extracted)
    created = interaction_service.create_interaction(db, interaction_data)

    return {
        "tool": "log_interaction",
        "interaction": {
            "id": created.id,
            "hcp_name": created.hcp_name,
            "interaction_type": created.interaction_type,
            "date": created.date.isoformat(),
            "time": created.time.isoformat() if created.time else None,
            "attendees": created.attendees,
            "topics_discussed": created.topics_discussed,
            "materials_shared": created.materials_shared,
            "samples_distributed": created.samples_distributed,
            "sentiment": created.sentiment,
            "outcomes": created.outcomes,
            "follow_up": created.follow_up,
            "created_at": created.created_at.isoformat(),
            "updated_at": created.updated_at.isoformat(),
        },
    }