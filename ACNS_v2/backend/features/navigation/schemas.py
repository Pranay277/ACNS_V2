"""
features/navigation/schemas.py — Request/response models for navigation.
"""

from pydantic import BaseModel, ConfigDict


class NavigationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    campus_id: str
    start_node: str
    end_node: str
    accessibility_mode: bool = False
