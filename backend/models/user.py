from pydantic import BaseModel
from typing import Optional


class UserDetails(BaseModel):
    target_role: str
    skills: Optional[str] = None
    projects: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    career_goals: Optional[str] = None