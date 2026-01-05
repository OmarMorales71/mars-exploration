from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal



class RoverGoal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Scientific goal id, e.g. SG1.")
    description: str = Field(..., description="Goal description.")
    target_nodes: List[str] = Field(default_factory=list, description="Target nodes for this goal.")
    terrain: Optional[str] = Field(default=None, description="Terrain type (plain/rocky/sandy/icy/crater) if given.")
    priority: str = Field(..., description="Priority normalized to: high, medium, low.")


class RoverMissionContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rover_goals: List[RoverGoal] = Field(default_factory=list, description="Rover-relevant mission goals only.")
    constraints: List[str] = Field(default_factory=list, description="Only constraints relevant to rover operations.")
    hazards: List[str] = Field(default_factory=list, description="Hazards relevant to rover operations.")



class PrimitiveGoal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., description="Unique primitive goal id, e.g., SG1_1.")
    parent_id: str = Field(..., description="Original goal id, e.g., SG1.")
    description: str = Field(..., description="Goal description (infered from parent goal).")
    target_node: str = Field(..., description="Single target node for this primitive goal.")
    terrain: str = Field(..., description="Terrain type.")
    priority: str = Field(..., description="Priority normalized to high/medium/low.")

class PrimitiveGoalsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    primitive_goals: List[PrimitiveGoal] = Field(default_factory=list, description="Expanded primitive goals.")

