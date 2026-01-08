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


class DroneCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    drone_id: str = Field(..., description="Drone id from drones.json, e.g., 'drone_0'.")
    path: List[str] = Field(..., description="Round-trip route (node sequence) visiting all target_nodes in order and returning to drone start.")
    distance: float = Field(..., description="Total round-trip distance/cost returned by Dijkstra (terrain-weighted if enabled).")
    time_required: float = Field(..., description="Estimated round-trip flight time in minutes (simple: equal to distance).")
    location: str = Field(..., description="Drone start node (treated as base node).")
    altitude: float = Field(..., description="Drone altitude from drones.json.")
    camera_resolution: str = Field(..., description="Drone camera_resolution from drones.json.")


class DroneRejection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    drone_id: str = Field(..., description="Rejected drone id.")
    reason: str = Field(..., description="Why this drone cannot complete the goal (range/time/prohibited nodes/no path/etc).")

class GoalCandidates(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_id: str = Field(..., description="Goal id from cleaned mission context (keep exact).")
    description: str = Field(..., description="Goal description from cleaned mission context (keep exact).")
    priority: Priority = Field(..., description="Goal priority from context (expected: high/medium/low).")
    terrain: str = Field(..., description="Goal terrain from context (normalized to plain/rocky/sandy/icy/crater if possible).")
    target_nodes: List[str] = Field(..., description="Target nodes for this goal (keep exact order).")

    candidates: List[DroneCandidate] = Field(default_factory=list, description="Feasible drone candidates for this goal.")
    no_candidates: List[DroneRejection] = Field(default_factory=list, description="Non-feasible drones with reasons.")


class PossibleDroneAssignments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    possible_assignments: List[GoalCandidates] = Field(
        default_factory=list,
        description="One entry per input goal. Contains feasible candidates + rejections."
    )

class DroneGoalAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_id: str = Field(..., description="Goal id copied from possible_assignments[i].goal_id.")
    description: str = Field(..., description="Goal description copied from possible_assignments[i].description.")
    priority: Priority = Field(..., description="Goal priority copied from possible_assignments[i].priority (normalized).")
    terrain: str = Field(..., description="Goal terrain copied from possible_assignments[i].terrain.")
    target_nodes: List[str] = Field(..., description="Goal target_nodes copied from possible_assignments[i].target_nodes.")

    selected_drone: DroneCandidate = Field(
        ...,
        description="Chosen drone candidate. Must match DroneCandidate exactly (do not change structure)."
    )

    selection_reason: str = Field(
        ...,
        description="One short paragraph explaining why this drone was chosen (balance + feasibility + efficiency)."
    )

class DroneGoalFailure(BaseModel):
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

class DroneSelectionPlan(BaseModel):
    #model_config = ConfigDict(extra="forbid")

    assignments: List[DroneGoalAssignment] = Field(
        default_factory=list,
        description="One selected drone per goal when at least one candidate exists."
    )
    failures: List[DroneGoalFailure] = Field(
        default_factory=list,
        description="Goals that have zero candidates. Must include reason derived from no_candidates."
    )