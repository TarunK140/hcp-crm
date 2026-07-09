"""
Interaction service layer.

All database access for interactions goes through this module. Both the
REST API (app/api/routes.py) and the LangGraph tools (app/tools/*) call
these same functions, which is what guarantees the manual form workflow
and the AI chat workflow stay perfectly in sync — there is only one
code path that ever touches the `interactions` table.
"""

from datetime import date as date_type
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.interaction import Interaction
from app.schemas.interaction import InteractionCreate, InteractionUpdate
from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_interaction(db: Session, data: InteractionCreate) -> Interaction:
    interaction = Interaction(**data.model_dump())
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    logger.info("Created interaction id=%s for hcp=%s", interaction.id, interaction.hcp_name)
    return interaction


def get_interaction(db: Session, interaction_id: int) -> Optional[Interaction]:
    return db.query(Interaction).filter(Interaction.id == interaction_id).first()


def list_interactions(db: Session, skip: int = 0, limit: int = 100) -> list[Interaction]:
    return (
        db.query(Interaction)
        .order_by(Interaction.date.desc(), Interaction.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_interaction(
    db: Session, interaction_id: int, data: InteractionUpdate
) -> Optional[Interaction]:
    interaction = get_interaction(db, interaction_id)
    if interaction is None:
        return None

    # Only overwrite fields that were actually provided — this is what
    # "preserve all other existing values" means for the Edit Interaction tool.
    updates = data.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in updates.items():
        setattr(interaction, field, value)

    db.commit()
    db.refresh(interaction)
    logger.info("Updated interaction id=%s fields=%s", interaction_id, list(updates.keys()))
    return interaction


def delete_interaction(db: Session, interaction_id: int) -> bool:
    interaction = get_interaction(db, interaction_id)
    if interaction is None:
        return False
    db.delete(interaction)
    db.commit()
    logger.info("Deleted interaction id=%s", interaction_id)
    return True


def search_interactions(
    db: Session,
    hcp_name: Optional[str] = None,
    interaction_date: Optional[date_type] = None,
) -> list[Interaction]:
    query = db.query(Interaction)
    if hcp_name:
        query = query.filter(Interaction.hcp_name.ilike(f"%{hcp_name}%"))
    if interaction_date:
        query = query.filter(Interaction.date == interaction_date)
    return query.order_by(Interaction.date.desc()).all()


def get_history_for_hcp(db: Session, hcp_name: Optional[str] = None) -> list[Interaction]:
    query = db.query(Interaction)
    if hcp_name:
        query = query.filter(Interaction.hcp_name.ilike(f"%{hcp_name}%"))
    return query.order_by(Interaction.date.asc()).all()
