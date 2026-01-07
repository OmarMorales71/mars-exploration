from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal

Priority = Literal["high", "medium", "low"]

# Clean goals agent 
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

# Process paths agent
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


# Selecter agent

class RoverGoalAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_id: str = Field(..., description="Goal id copied from possible_assignments[i].goal_id.")
    description: str = Field(..., description="Goal description copied from possible_assignments[i].description.")
    priority: Priority = Field(..., description="Goal priority copied from possible_assignments[i].priority (normalized).")
    terrain: str = Field(..., description="Goal terrain copied from possible_assignments[i].terrain.")
    target_nodes: List[str] = Field(..., description="Goal target_nodes copied from possible_assignments[i].target_nodes.")

    selected_rover: RoverCandidate = Field(
        ...,
        description="Chosen rover candidate. Must match RoverCandidate exactly (do not change structure)."
    )

    selection_reason: str = Field(
        ...,
        description="One short paragraph explaining why this rover was chosen (balance + feasibility + efficiency)."
    )

class RoverGoalFailure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_id: str = Field(..., description="Goal id copied from possible_assignments[i].goal_id.")
    description: str = Field(..., description="Goal description copied from possible_assignments[i].description.")
    priority: Priority = Field(..., description="Goal priority copied from possible_assignments[i].priority.")
    terrain: str = Field(..., description="Goal terrain copied from possible_assignments[i].terrain.")
    target_nodes: List[str] = Field(..., description="Goal target_nodes copied from possible_assignments[i].target_nodes.")

    reason: str = Field(
        ...,
        description="Explain why the goal cannot be completed based on the no_candidates reasons (summary)."
    )

class RoverSelectionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assignments: List[RoverGoalAssignment] = Field(
        default_factory=list,
        description="One selected rover per goal when at least one candidate exists."
    )
    failures: List[RoverGoalFailure] = Field(
        default_factory=list,
        description="Goals that have zero candidates. Must include reason derived from no_candidates."
    )