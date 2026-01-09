from typing import Any, Dict
from crewai.tools import BaseTool

class SplitGoalsTool(BaseTool):
    """
    Decide which goals must be assignments vs failures, purely by checking
    whether candidates list is empty or not.
    """

    name: str = "split_goals_tool"
    description: str = (
        "Given possible_assignments (list of goal objects), returns goal_id lists:\n"
        '- assignments: goal_ids where candidates is non-empty\n'
        '- failures: goal_ids where candidates is empty\n'
        "No other logic."
    )

    def _run(self, possible_assignments: list) -> Dict[str, Any]:
        assignments = []
        failures = []
        if not isinstance(possible_assignments, list):
            return {
                "error": "possible_assignments must be a list of goal objects",
                "assignments": [],
                "failures": [],
            }

        for g in possible_assignments:
            if not isinstance(g, dict):
                continue
            goal_id = g.get("goal_id")
            candidates = g.get("candidates", [])

            if not goal_id:
                continue

            if isinstance(candidates, list) and len(candidates) > 0:
                assignments.append(goal_id)
            else:
                failures.append(goal_id)

        return {"assignments": assignments, "failures": failures}