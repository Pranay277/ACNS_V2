"""
features/auth/schemas.py — Request/response models for the auth feature.

Request models reject unknown fields (``extra="forbid"``, P2-10) so client
typos and sneaked-in fields fail fast with a 422.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    """Body for POST /api/auth/login — a Firebase ID token."""

    model_config = ConfigDict(extra="forbid")

    idToken: str


class SignupRequest(BaseModel):
    """Body for POST /api/auth/signup — a Firebase ID token plus profile fields."""

    model_config = ConfigDict(extra="forbid")

    idToken: str
    displayName: Optional[str] = None
    campusId: Optional[str] = None
    phoneNumber: Optional[str] = None
    preferredLanguage: Optional[str] = None


class UserUpdateRequest(BaseModel):
    """Admin updates for a user profile (whitelisted by the router/service)."""

    model_config = ConfigDict(extra="forbid")

    displayName: Optional[str] = None
    campusId: Optional[str] = None
    role: Optional[str] = None
    phoneNumber: Optional[str] = None
    preferredLanguage: Optional[str] = None
    department: Optional[str] = None
