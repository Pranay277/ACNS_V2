"""
features/supervisors/schemas.py — Request/response models for the supervisors
feature (admin-managed supervisor lifecycle).
"""

from typing import Optional

from pydantic import BaseModel


class SupervisorCreateRequest(BaseModel):
    """Body for POST /api/supervisors — admin-provisioned supervisor account."""
    email: str
    displayName: str
    department: str
    phoneNumber: Optional[str] = None
    preferredLanguage: Optional[str] = None
    campusId: Optional[str] = None
    # Optional temporary password. When omitted the backend auto-generates one
    # and returns it once in the response (``temporaryPassword``).
    password: Optional[str] = None


class SupervisorUpdateRequest(BaseModel):
    """Admin edits for a supervisor profile (whitelisted by the service)."""
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
    displayName: Optional[str] = None
    phoneNumber: Optional[str] = None
    preferredLanguage: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    """Body for POST /api/supervisors/{uid}/reset-password."""
    newPassword: str


class ChangeEmailRequest(BaseModel):
    """Body for POST /api/supervisors/{uid}/change-email (admin-only)."""
    newEmail: str
