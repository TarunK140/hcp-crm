"""
Tool 3: Search Interaction

Searches logged interactions by HCP name and/or date. Uses the LLM only to
pull the search parameters out of natural language (e.g. "show me my visits
with Dr. Mehta last week" -> hcp_name="Mehta"); the actual search is a
plain, deterministic DB query — no LLM is involved in ranking/matching,
which keeps search results predictable.
"""

from datetime import date
from sqlalchemy.orm import Session

from app.core.llm_client import chat_completion, safe_json_parse
from app.services import interaction_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

_EXTRACTION_PROMPT = """Extract search parameters from the user's request about finding logged HCP \
interactions. Return ONLY JSON: {{"hcp_name": <string or null>, "date": <"YYYY-MM-DD" or null>}}.
Today's date is {today}. If the user says something relative like "last week" or "yesterday", do \
your best to resolve it to an actual date; otherwise use null."""


def run(db: Session, user_message: str) -> dict:
    raw = chat_completion(
        messages=[
            {"role": "system", "content": _EXTRACTION_PROMPT.format(today=date.today().isoformat())},
            {"role": "user", "content": user_message},
        ],
        json_mode=True,
    )
    params = safe_json_parse(raw)
    logger.info("Search Interaction tool params: %s", params)

    hcp_name = params.get("hcp_name")
    search_date = None
    if params.get("date"):
        try:
            search_date = date.fromisoformat(params["date"])
        except ValueError:
            search_date = None

    results = interaction_service.search_interactions(db, hcp_name=hcp_name, interaction_date=search_date)

    return {
        "tool": "search_interaction",
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
