"""
Tool 2: Edit Interaction

Takes a correction request in natural language plus the id of the
interaction being edited, asks the LLM to figure out ONLY the fields that
should change, and applies a partial update — preserving every other
existing field untouched.
"""

import re
from sqlalchemy.orm import Session

from app.core.llm_client import chat_completion, safe_json_parse
from app.prompts.prompts import EDIT_INTERACTION_EXTRACTION_PROMPT
from app.schemas.interaction import InteractionUpdate
from app.services import interaction_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

_VALID_TIME_RE = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")


def _sanitize_time(value):
    """Drop non-HH:MM time values from the LLM instead of letting validation crash."""
    if value is None:
        return None
    if not isinstance(value, str) or not _VALID_TIME_RE.match(value.strip()):
        logger.warning("Discarding non-standard time value from LLM edit: %r", value)
        return None
    return value.strip()


def _interaction_to_dict(interaction) -> dict:
    return {
        "id": interaction.id,
        "hcp_name": interaction.hcp_name,
        "interaction_type": interaction.interaction_type,
        "date": interaction.date.isoformat(),
        "time": interaction.time.isoformat() if interaction.time else None,
        "attendees": interaction.attendees,
        "topics_discussed": interaction.topics_discussed,
        "materials_shared": interaction.materials_shared,
        "samples_distributed": interaction.samples_distributed,
        "sentiment": interaction.sentiment,
        "outcomes": interaction.outcomes,
        "follow_up": interaction.follow_up,
        "created_at": interaction.created_at.isoformat(),
        "updated_at": interaction.updated_at.isoformat(),
    }


def run(db: Session, user_message: str, interaction_id: int) -> dict:
    existing = interaction_service.get_interaction(db, interaction_id)
    if existing is None:
        return {"tool": "edit_interaction", "error": f"No interaction found with id={interaction_id}"}

    current_data = _interaction_to_dict(existing)

    raw = chat_completion(
        messages=[
            {"role": "system", "content": EDIT_INTERACTION_EXTRACTION_PROMPT},
            {
                "role": "user",
                "content": f"CURRENT DATA:\n{current_data}\n\nREQUESTED CHANGE:\n{user_message}",
            },
        ],
        json_mode=True,
    )
    changes = safe_json_parse(raw)
    if "time" in changes:
        changes["time"] = _sanitize_time(changes["time"])
    logger.info("Edit Interaction tool applying changes: %s", changes)

    update_data = InteractionUpdate(**changes)
    updated = interaction_service.update_interaction(db, interaction_id, update_data)

    return {"tool": "edit_interaction", "interaction": _interaction_to_dict(updated)}