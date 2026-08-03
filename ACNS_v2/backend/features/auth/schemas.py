"""
features/auth/schemas.py — Request/response models for the auth feature.
"""

from typing import Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Body for POST /api/auth/login — a Firebase ID token."""
    idToken: str


class SignupRequest(BaseModel):
    """Body for POST /api/auth/signup — a Firebase ID token plus profile fields."""
    idToken: str
    displayName: Optional[str] = None
    campusId: Optional[str] = None
    phoneNumber: Optional[str] = None
    preferredLanguage: Optional[str] = None


class UserUpdateRequest(BaseModel):
    """Admin updates for a user profile (whitelisted by the router/service)."""
    displayName: Optional[str] = None
    campusId: Optional[str] = None
    role: Optional[str] = None
    phoneNumber: Optional[str] = None
    preferredLanguage: Optional[str] = None
    department: Optional[str] = None
