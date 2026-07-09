"""
REST API routes.

- /interactions/*  -> plain CRUD, used by the manual form (Workflow 1)
- /chat            -> conversational entry point, used by the AI assistant (Workflow 2)
- /langgraph/execute -> lower-level endpoint that runs the graph directly
  (useful for the video demo / debugging each tool in isolation)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.interaction import (
    InteractionCreate,
    InteractionUpdate,
    InteractionResponse,
    ChatRequest,
    ChatResponse,
)
from app.services import interaction_service
from app.langgraph.graph import run_graph
from app.core.llm_client import chat_completion
from app.prompts.prompts import CHAT_REPLY_PROMPT
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Manual CRUD endpoints (Workflow 1: structured form)
# ---------------------------------------------------------------------------

@router.post("/interactions", response_model=InteractionResponse, status_code=201)
def create_interaction(data: InteractionCreate, db: Session = Depends(get_db)):
    return interaction_service.create_interaction(db, data)


@router.get("/interactions", response_model=list[InteractionResponse])
def list_interactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return interaction_service.list_interactions(db, skip, limit)


@router.get("/interactions/{interaction_id}", response_model=InteractionResponse)
def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = interaction_service.get_interaction(db, interaction_id)
    if interaction is None:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@router.put("/interactions/{interaction_id}", response_model=InteractionResponse)
def update_interaction(interaction_id: int, data: InteractionUpdate, db: Session = Depends(get_db)):
    interaction = interaction_service.update_interaction(db, interaction_id, data)
    if interaction is None:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@router.delete("/interactions/{interaction_id}", status_code=204)
def delete_interaction(interaction_id: int, db: Session = Depends(get_db)):
    deleted = interaction_service.delete_interaction(db, interaction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return None


# ---------------------------------------------------------------------------
# AI Assistant endpoint (Workflow 2: conversational logging)
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        result = run_graph(db, request.message, request.current_interaction_id)
    except Exception as exc:
        logger.error("LangGraph execution failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Assistant failed to process request: {exc}")

    if "error" in result:
        return ChatResponse(reply=result["error"], tool_used=result.get("tool"))

    # Ask the LLM for a short, natural confirmation message.
    try:
        reply_raw = chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": CHAT_REPLY_PROMPT.format(tool_name=result.get("tool", "unknown")),
                },
                {"role": "user", "content": str(result)},
            ],
            temperature=0.5,
        )
    except Exception as exc:
        logger.error("Reply generation failed: %s", exc)
        # The tool itself already succeeded (data is saved) — only the
        # natural-language confirmation failed, so fall back to a plain
        # message rather than losing the whole request.
        reply_raw = f"Done — {result.get('tool', 'action')} completed successfully."

    try:
        return ChatResponse(
            reply=reply_raw,
            tool_used=result.get("tool"),
            interaction=result.get("interaction"),
            interactions=result.get("interactions"),
            recommendation=(
                {"hcp_name": result.get("hcp_name"), **result.get("recommendation", {})}
                if result.get("recommendation")
                else None
            ),
        )
    except Exception as exc:
        logger.error("ChatResponse validation failed for tool=%s: %s", result.get("tool"), exc)
        raise HTTPException(
            status_code=500,
            detail=f"Tool '{result.get('tool')}' ran but its result didn't match the response schema: {exc}",
        )


# ---------------------------------------------------------------------------
# Direct LangGraph execution endpoint (useful for demoing each tool)
# ---------------------------------------------------------------------------

@router.post("/langgraph/execute")
def langgraph_execute(request: ChatRequest, db: Session = Depends(get_db)):
    """Runs the graph and returns the raw tool result, without the chat-reply wrapping."""
    return run_graph(db, request.message, request.current_interaction_id)
