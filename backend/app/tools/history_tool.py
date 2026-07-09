"""
Tool 4: View Interaction History

Returns the full, chronologically-sorted interaction history, optionally
filtered to a single HCP. Like Search, the retrieval itself is a plain DB
query — the LLM is only used to pull an optional HCP name out of the
user's phrasing (e.g. "show me all my history with Dr. Rao").
"""

from sqlalchemy.orm import Session

from app.core.llm_client import chat_completion, safe_json_parse
from app.services import interaction_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

_EXTRACTION_PROMPT = """Extract the HCP name (if any) the user wants interaction history for. \
Return ONLY JSON: {"hcp_name": <string or null>}. If they want history across ALL HCPs, use null."""


def run(db: Session, user_message: str) -> dict:
    raw = chat_completion(
        messages=[
            {"role": "system", "content": _EXTRACTION_PROMPT},
            {"role": "user", "content": user_message},
        ],
        json_mode=True,
    )
    params = safe_json_parse(raw)
    hcp_name = params.get("hcp_name")
    logger.info("History tool hcp_name filter: %s", hcp_name)

    results = interaction_service.get_history_for_hcp(db, hcp_name=hcp_name)

    return {
        "tool": "view_history",
        "interactions": [
            {
                "id": r.id,
                "hcp_name": r.hcp_name,
                "interaction_type": r.interaction_type,
                "date": r.date.isoformat(),
                "time": r.time.isoformat() if r.time else None,
                "attendees": r.attendees,
                "topics_discussed": r.topics_discussed,
                "materials_shared": r.materials_shared,
                "samples_distributed": r.samples_distributed,
                "sentiment": r.sentiment,
                "outcomes": r.outcomes,
                "follow_up": r.follow_up,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat(),
            }
            for r in results
        ],
    }
