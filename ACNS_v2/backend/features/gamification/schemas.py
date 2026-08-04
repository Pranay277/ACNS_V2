"""
features/gamification/schemas.py — Request/response models for gamification.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class GamificationAward(BaseModel):
    model_config = ConfigDict(extra="forbid")

    userId: str
    reason: str
    points: Optional[int] = None
    issueId: Optional[str] = None
    displayName: Optional[str] = None
