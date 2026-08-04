"""
features/supervisors/schemas.py — Request/response models for the supervisors
feature (admin-managed supervisor lifecycle).

Request models reject unknown fields (``extra="forbid"``, P2-10) so typos and
sneaked-in fields fail fast with a 422 instead of being silently dropped.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from shared.utils.validators import validate_password


class SupervisorCreateRequest(BaseModel):
    """Body for POST /api/supervisors — admin-provisioned supervisor account."""

    model_config = ConfigDict(extra="forbid")

    email: str
    displayName: str
    department: str
    phoneNumber: Optional[str] = None
    preferredLanguage: Optional[str] = None
    campusId: Optional[str] = None
    # Optional temporary password. When omitted the backend auto-generates one
    # and returns it once in the response (``temporaryPassword``).
    password: Optional[str] = None

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value):
        if value is None:
            return value
        return validate_password(value)


class SupervisorUpdateRequest(BaseModel):
    """Admin edits for a supervisor profile (whitelisted by the service)."""

    model_config = ConfigDict(extra="forbid")

    displayName: Optional[str] = None
    campusId: Optional[str] = None
    department: Optional[str] = None
    phoneNumber: Optional[str] = None
    preferredLanguage: Optional[str] = None


class SupervisorSelfUpdateRequest(BaseModel):
    """Self-service edits a supervisor may make to their OWN profile.

    Only displayName, phoneNumber and preferredLanguage are exposed. Email,
    department, role, uid and isActive are admin-managed and never accepted
    here.
    """

    model_config = ConfigDict(extra="forbid")

    displayName: Optional[str] = None
    phoneNumber: Optional[str] = None
    preferredLanguage: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    """Body for POST /api/supervisors/{uid}/reset-password."""

    model_config = ConfigDict(extra="forbid")

    newPassword: str

    @field_validator("newPassword")
    @classmethod
    def _validate_new_password(cls, value):
        return validate_password(value)


class ChangeEmailRequest(BaseModel):
    """Body for POST /api/supervisors/{uid}/change-email (admin-only)."""

    model_config = ConfigDict(extra="forbid")

    newEmail: str
