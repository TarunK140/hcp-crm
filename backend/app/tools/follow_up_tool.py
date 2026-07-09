"""
Tool 5: Generate Follow-up Recommendation

Uses an HCP's full interaction history to have the LLM recommend next
steps: visit timing, materials, samples, talking points, and follow-up
actions. This is the one tool that is genuinely generative/advisory rather
than a structured data operation, since it needs real reasoning over
historical patterns (sentiment trend, topics already covered, etc.).
"""

from sqlalchemy.orm import Session

from app.core.llm_client import chat_completion, safe_json_parse
from app.prompts.prompts import FOLLOW_UP_RECOMMENDATION_PROMPT
from app.services import interaction_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

_HCP_EXTRACTION_PROMPT = """Extract the HCP name the user wants a follow-up recommendation for. \
Return ONLY JSON: {"hcp_name": <string>}."""


def run(db: Session, user_message: str) -> dict:
    raw_name = chat_completion(
        messages=[
            {"role": "system", "content": _HCP_EXTRACTION_PROMPT},
            {"role": "user", "content": user_message},
        ],
        json_mode=True,
    )
    hcp_name = safe_json_parse(raw_name).get("hcp_name")

    history = interaction_service.get_history_for_hcp(db, hcp_name=hcp_name)
    if not history:
        return {
            "tool": "follow_up_recommendation",
            "error": f"No interaction history found for '{hcp_name}' to base a recommendation on.",
        }

    history_payload = [
        {
            "date": h.date.isoformat(),
            "interaction_type": h.interaction_type,
            "topics_discussed": h.topics_discussed,
            "materials_shared": h.materials_shared,
            "samples_distributed": h.samples_distributed,
            "sentiment": h.sentiment,
            "outcomes": h.outcomes,
            "follow_up": h.follow_up,
        }
        for h in history
    ]

    raw = chat_completion(
        messages=[
            {"role": "system", "content": FOLLOW_UP_RECOMMENDATION_PROMPT},
            {"role": "user", "content": f"HCP: {hcp_name}\nHistory:\n{history_payload}"},
        ],
        json_mode=True,
        temperature=0.4,
    )
    recommendation = safe_json_parse(raw)
    logger.info("Follow-up recommendation generated for hcp=%s", hcp_name)

    return {"tool": "follow_up_recommendation", "hcp_name": hcp_name, "recommendation": recommendation}
