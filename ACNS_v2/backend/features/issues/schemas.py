"""
features/issues/schemas.py — Request/response models for the issues feature.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from shared.utils.validators import validate_safe_url


class IssueCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    userId: str
    category: str
    subCategory: Optional[str] = None
    description: str
    imageUrl: Optional[str] = None
    lat: float
    lng: float
    locationText: str
    college: Optional[str] = None

    @field_validator("imageUrl")
    @classmethod
    def _validate_image_url(cls, value):
        return validate_safe_url(value)


class IssueStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    proofImageUrl: Optional[str] = None
    supervisorName: Optional[str] = None
    supervisorEmail: Optional[str] = None
    supervisorPhoto: Optional[str] = None
    supervisorDescription: Optional[str] = None

    @field_validator("proofImageUrl", "supervisorPhoto")
    @classmethod
    def _validate_photo_urls(cls, value):
        return validate_safe_url(value)


class VerifyIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: bool
