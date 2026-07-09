"""
Pydantic schemas used for request validation and response serialization.

Kept separate from the SQLAlchemy model (app/models/interaction.py) so the
API contract can evolve independently of the DB schema.
"""

from datetime import date as date_type, time as time_type, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class InteractionBase(BaseModel):
    hcp_name: str = Field(..., description="Name of the healthcare professional")
    interaction_type: str = Field(..., description="In-Person, Virtual, Phone, or Email")
    date: date_type
    time: Optional[time_type] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up: Optional[str] = None


class InteractionCreate(InteractionBase):
    """Used for POST /interactions and the Log Interaction tool."""
    pass


class InteractionUpdate(BaseModel):
    """
    Used for PUT /interactions/{id} and the Edit Interaction tool.
    Every field is optional: only the fields the user actually wants
    changed should be sent, and everything else is preserved.
    """
    hcp_name: Optional[str] = None
    interaction_type: Optional[str] = None
    date: Optional[date_type] = None
    time: Optional[time_type] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up: Optional[str] = None


class InteractionResponse(InteractionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    message: str = Field(..., description="Natural language user message")
    current_interaction_id: Optional[int] = Field(
        None, description="If editing an existing interaction, its id"
    )
    conversation_history: Optional[list[dict]] = Field(
        default_factory=list, description="Prior turns: [{role, content}, ...]"
    )


class ChatResponse(BaseModel):
    reply: str
    tool_used: Optional[str] = None
    interaction: Optional[InteractionResponse] = None
    interactions: Optional[list[InteractionResponse]] = None
    recommendation: Optional[dict] = None
