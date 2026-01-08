from __future__ import annotations

from typing import Any, Dict, List, Optional
from crewai.tools import BaseTool

# ✅ Adjust this import path to match your project structure
from mars_exploration.models.rover_models import (
    RoverCandidate,
    RoverGoalAssignment,
    RoverGoalFailure,
    RoverSelectionPlan,
)


def _priority_rank(p: str) -> int:
    p = (p or "").strip().lower()
    return {"high": 0, "medium": 1, "low": 2}.get(p, 3)


def _summarize_no_candidates(no_candidates: List[Dict[str, Any]], max_items: int = 5) -> str:
    """
    Build a short failure reason from no_candidates.
    Deterministic and grounded in the provided reasons.
    """
    if not no_candidates:
        return "No rover candidates were available for this goal."

    reasons: List[str] = []
    for item in no_candidates[:max_items]:
        rid = str(item.get("rover_id", "")).strip()
        r = str(item.get("reason", "")).strip()
        if rid and r:
            reasons.append(f"{rid}: {r}")
        elif r:
            reasons.append(r)

    if not reasons:
        return "No rover candidates were available for this goal."

    extra = len(no_candidates) - len(reasons)
    suffix = f" (and {extra} more)" if extra > 0 else ""
    return "No rover can complete this goal. " + "; ".join(reasons) + suffix


class RoverSelectionTool(BaseTool):
    """
    Deterministically select ONE rover candidate per goal from possible_assignments.

    Selection logic:
    - Process goals in priority order: high -> medium -> low
    - For each goal with candidates:
        pick candidate by (lowest usage count so far, lowest energy_required, lowest distance)
    - If candidates empty: create failure with summarized no_candidates reason

    Output is a RoverSelectionPlan (Pydantic).
    """

    name: str = "rover_selection_tool"
    description: str = (
        "Selects one rover candidate per goal from possible_assignments using balancing + efficiency rules. "
        "Returns a RoverSelectionPlan with assignments and failures."
    )

    def _run(self, possible_assignments: list) -> RoverSelectionPlan:

        # Sort goals by priority (stable)
        goals_sorted = sorted(
            possible_assignments,
            key=lambda g: _priority_rank(str((g or {}).get("priority", ""))),
        )

        rover_usage: Dict[str, int] = {}
        assignments: List[RoverGoalAssignment] = []
        failures: List[RoverGoalFailure] = []
        seen_goal_ids = set()

        for goal in goals_sorted:
            if not isinstance(goal, dict):
                continue

            goal_id = str(goal.get("goal_id", "")).strip()
            if not goal_id:
                # malformed goal -> skip (do not invent)
                continue

            if goal_id in seen_goal_ids:
                # upstream duplication -> ignore duplicates deterministically
                continue
            seen_goal_ids.add(goal_id)

            description = str(goal.get("description", ""))
            priority = str(goal.get("priority", "")).strip().lower() or "medium"
            terrain = str(goal.get("terrain", ""))
            target_nodes = goal.get("target_nodes") or []
            if not isinstance(target_nodes, list):
                target_nodes = []

            raw_candidates = goal.get("candidates") or []
            if not isinstance(raw_candidates, list):
                raw_candidates = []

            raw_no_candidates = goal.get("no_candidates") or []
            if not isinstance(raw_no_candidates, list):
                raw_no_candidates = []
            print(f"RAW {raw_no_candidates}")
            # ✅ Failure when candidates empty
            if len(raw_candidates) == 0:
                failures.append(
                    RoverGoalFailure(
                        goal_id=goal_id,
                        description=description,
                        priority=priority,
                        terrain=terrain,
                        target_nodes=[str(n) for n in target_nodes],
                        reason=_summarize_no_candidates(raw_no_candidates),
                    )
                )
                continue

            # ✅ Parse candidates as RoverCandidate models (skip invalid ones)
            candidates: List[RoverCandidate] = []
            for c in raw_candidates:
                if not isinstance(c, dict):
                    continue
                print(f"HOLAAA {c}")
                candidates.append(RoverCandidate(
                        rover_id=c["rover_id"],
                        path=c["path"],
                        distance=float(c["distance"]),
                        energy_required=float(c["energy_required"]),
                        recharge_before=bool(c["recharge_before"]),
                        speed=float(c["speed"]),
                        location=c["location"]
                ))


            # ✅ Choose best candidate by (usage, energy_required, distance)
            best: Optional[RoverCandidate] = None
            best_key: Optional[tuple] = None

            for c in candidates:
                rid = (c.rover_id or "").strip()
                if not rid:
                    continue
                usage = rover_usage.get(rid, 0)
                energy_req = c.energy_required
                dist = c.distance

                key = (usage, energy_req, dist)
                if best is None or key < best_key:
                    best = c
                    best_key = key

            if best is None:
                failures.append(
                    RoverGoalFailure(
                        goal_id=goal_id,
                        description=description,
                        priority=priority,
                        terrain=terrain,
                        target_nodes=[str(n) for n in target_nodes],
                        reason="Candidates were present but none had a valid rover_id.",
                    )
                )
                continue

            rover_usage[best.rover_id] = rover_usage.get(best.rover_id, 0) + 1

            selection_reason = (
                f"Selected {best.rover_id} to balance rover usage across goals; "
                f"it is efficient among available candidates (lower energy_required {best.energy_required} and distance {best.distance})."
            )

            assignments.append(
                RoverGoalAssignment(
                    goal_id=goal_id,
                    description=description,
                    priority=priority,
                    terrain=terrain,
                    target_nodes=[str(n) for n in target_nodes],
                    selected_rover=best,  # ✅ exact RoverCandidate object
                    selection_reason=selection_reason,
                )
            )

        plan = RoverSelectionPlan(assignments=assignments, failures=failures)
        return plan
