from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal

Priority = Literal["high", "medium", "low"]

class RoverGoal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_id: str = Field(..., description="Scientific goal id, e.g. SG1.")
    description: str = Field(..., description="Goal description.")
    target_nodes: List[str] = Field(default_factory=list, description="Target nodes for this goal.")
    terrain: Optional[str] = Field(default=None, description="Terrain type (plain/rocky/sandy/icy/crater) if given.")
    priority: Priority = Field(..., description="Priority normalized to: high, medium, low. Must be lower case")


class RoverMissionContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rover_goals: List[RoverGoal] = Field(default_factory=list, description="Rover-relevant mission goals only.")
    constraints: List[str] = Field(default_factory=list, description="Only constraints relevant to rover operations.")
    hazards: List[str] = Field(default_factory=list, description="Hazards relevant to rover operations.")


class RoverCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rover_id: str = Field(..., description="Rover id from rovers.json.")
    path: List[str] = Field(..., description="Round-trip path: start -> targets -> start.")
    distance: float = Field(..., description="Total round-trip distance/cost.")
    energy_required: float = Field(..., description="Energy required = distance * energy_cost.")
    recharge_before: bool = Field(
        ...,
        description="True if rover must recharge before departing to avoid dropping below threshold.",
    )
    speed: float = Field(..., description="Rover speed")
    location: str = Field(..., description="initial location")

class RoverRejection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rover_id: str = Field(..., description="Rover id.")
    reason: str = Field(..., description="Reason rover is not feasible for this goal.")


class GoalCandidates(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_id: str = Field(..., description="Goal id (e.g., SG1).")
    description: str = Field(..., description="Goal description")
    priority: Literal["high", "medium", "low"] = Field(
        ...,
        description="Priority normalized to lowercase for stable ordering and downstream processing.",
    )
    terrain: str = Field(..., description="Goal terrain (lowercase).")
    target_nodes: List[str] = Field(..., description="Target nodes to visit in order.")
    candidates: List[RoverCandidate] = Field(default_factory=list, description="Feasible rover candidates.")
    no_candidates: List[RoverRejection] = Field(
        default_factory=list, description="All non-feasible rovers with reasons."
    )


class PossibleAssignments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    possible_assignments: List[GoalCandidates] = Field(
        default_factory=list,
        description="Tool output: per-goal rover candidates ordered by priority (high, medium, low).",
    )


# class PrimitiveGoal(BaseModel):
#     model_config = ConfigDict(extra="forbid")
#     id: str = Field(..., description="Unique primitive goal id, e.g., SG1_1.")
#     parent_id: str = Field(..., description="Original goal id, e.g., SG1.")
#     description: str = Field(..., description="Goal description (infered from parent goal).")
#     target_node: str = Field(..., description="Single target node for this primitive goal.")
#     terrain: str = Field(..., description="Terrain type.")
#     priority: str = Field(..., description="Priority normalized to high/medium/low.")

# class PrimitiveGoalsOutput(BaseModel):
#     model_config = ConfigDict(extra="forbid")
#     primitive_goals: List[PrimitiveGoal] = Field(default_factory=list, description="Expanded primitive goals.")
#     constraints: List[str] = Field(default_factory=list, description="Only constraints relevant to rover operations.")
#     hazards: List[str] = Field(default_factory=list, description="Hazards relevant to rover operations.")

# class RoverCandidate(BaseModel):
#     model_config = ConfigDict(extra="forbid")

#     rover_id: str = Field(..., description="Rover id that can execute the primitive goal.")
#     path: List[str] = Field(..., description="Shortest path from rover location to target node.")
#     distance: float = Field(..., description="Total route distance returned by the tool.")


# class CandidatesForGoal(BaseModel):
#     model_config = ConfigDict(extra="forbid")

#     primitive_goal_id: str = Field(..., description="Primitive goal id.")
#     candidates: List[RoverCandidate] = Field(default_factory=list, description="Rovers that can complete this goal.")

# class RoverCandidatesPlan(BaseModel):
#     model_config = ConfigDict(extra="forbid")

#     assignments: List[CandidatesForGoal] = Field(default_factory=list, description="Candidate rovers for each primitive goal.")
#     failures: List[dict] = Field(default_factory=list, description="Primitive goals that no rover can complete.")