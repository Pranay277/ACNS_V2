"""
features/issues/schemas.py — Request/response models for the issues feature.
"""

from typing import Optional

from pydantic import BaseModel


class IssueCreate(BaseModel):
    userId: str
    category: str
    description: str
    imageUrl: Optional[str] = None
    lat: float
    lng: float
    locationText: str
    college: Optional[str] = None


class IssueStatusUpdate(BaseModel):
    status: str
    proofImageUrl: Optional[str] = None
    supervisorName: Optional[str] = None
    supervisorEmail: Optional[str] = None
    supervisorPhoto: Optional[str] = None
    supervisorDescription: Optional[str] = None


class VerifyIssue(BaseModel):
    verified: bool
