from pydantic import BaseModel
from typing import Optional


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


class NavigationRequest(BaseModel):
    campus_id: str
    start_node: str
    end_node: str
    accessibility_mode: bool = False


class GamificationAward(BaseModel):
    userId: str
    reason: str
    points: Optional[int] = None
    issueId: Optional[str] = None
    displayName: Optional[str] = None
