from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional, Literal


class ScientificGoal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique goal identifier, e.g., 'G1'")
    description: str = Field(..., description="Short goal statement")
    target_nodes: List[str] = Field(default_factory=list, description="Target graph nodes, e.g., ['N22','N23']")
    terrain: Optional[str] = Field(default=None, description="Terrain type if specified in the report (e.g., 'icy')")
    priority: str = Field(..., description="Priority level for this goal: high/medium/low.")



# class Constraint(BaseModel):
#     model_config = ConfigDict(extra="forbid")

#     applies_to: str = Field(..., description="Which agent type the constraint applies to")
#     description: str = Field(..., description="Constraint in plain language")


# class Hazard(BaseModel):
#     model_config = ConfigDict(extra="forbid")

#     location: str = Field(..., description="Location identifier, typically a node id like 'N88'")
#     description: str = Field(..., description="Hazard description")


class MissionSpec(BaseModel):
    """
    Final Mission Crew output model (simple + traceable).
    """
    model_config = ConfigDict(extra="forbid")

    mission_title: str = Field(
        ...,
        description="Short title of the mission as stated or inferred from the mission report."
    )

    mission_description: str = Field(
        ...,
        description="Concise, non-empty summary of the overall mission purpose and scope."
    )

    scientific_goals: List[ScientificGoal] = Field(
        default_factory=list,
        description="List of scientific objectives the mission aims to accomplish."
    )

    constraints: List[str] = Field(
        default_factory=list,
        description="List of operational or environmental constraints that limit agent behavior."
    )

    hazards: List[str] = Field(
        default_factory=list,
        description="List of known or suspected hazards that may affect mission execution."
    )

    assumptions: List[str] = Field(
        default_factory=list,
        description="List of assumptions inferred during mission interpretation due to missing or implicit information in the report."
    )

    risks: List[str] = Field(
        default_factory=list,
        description="List of mission risks, including ambiguities, conflicts, or missing details that could impact planning."
    )

    @field_validator("scientific_goals")
    @classmethod
    def _unique_goal_ids(cls, goals: List[ScientificGoal]) -> List[ScientificGoal]:
        ids = [g.id for g in goals]
        dupes = {x for x in ids if ids.count(x) > 1}
        if dupes:
            raise ValueError(f"Duplicate goal ids found: {sorted(dupes)}")
        return goals

