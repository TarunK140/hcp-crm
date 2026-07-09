"""
SQLAlchemy ORM model for an HCP interaction log entry.

This is the single source of truth for interaction data — both the manual
form workflow and the AI chat workflow write to this same table, which is
what keeps the two logging methods synchronized.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Date, Time, DateTime
from app.database.db import Base


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)

    hcp_name = Column(String(255), nullable=False, index=True)
    interaction_type = Column(String(50), nullable=False)  # In-Person, Virtual, Phone, Email

    date = Column(Date, nullable=False)
    time = Column(Time, nullable=True)

    attendees = Column(Text, nullable=True)          # comma-separated or free text
    topics_discussed = Column(Text, nullable=True)
    materials_shared = Column(Text, nullable=True)
    samples_distributed = Column(Text, nullable=True)
    sentiment = Column(String(50), nullable=True)     # Positive, Neutral, Negative
    outcomes = Column(Text, nullable=True)
    follow_up = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Interaction id={self.id} hcp_name={self.hcp_name!r} date={self.date}>"
