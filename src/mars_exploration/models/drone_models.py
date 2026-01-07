from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

Priority = Literal["high", "medium", "low"]

class DroneGoal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_id: str = Field(..., description="Scientific goal id, e.g. SG1.")
    description: str = Field(..., description="Goal description.")
    target_nodes: List[str] = Field(default_factory=list, description="Target nodes for this goal.")
    terrain: Optional[str] = Field(default=None, description="Terrain type (plain/rocky/sandy/icy/crater/air) if given.")
    priority: Priority = Field(..., description="Priority normalized to: high, medium, low. Must be lower case")

class DroneMissionContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    drone_goals: List[DroneGoal] = Field(default_factory=list, description="Drone-relevant mission goals only.")
    constraints: List[str] = Field(default_factory=list, description="Only constraints relevant to drone operations.")
    hazards: List[str] = Field(default_factory=list, description="Hazards relevant to drone operations.")

