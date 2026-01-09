from __future__ import annotations

from typing import Any, Dict, List, Literal, Set

import networkx as nx
from crewai.tools import BaseTool

from mars_exploration.models.rover_models import GoalCandidates, RoverCandidate, RoverRejection


# Terrain traversal multipliers
TERRAIN_MULTIPLIERS: Dict[str, float] = {
    "plain": 1.0,
    "rocky": 1.3,
    "sandy": 1.6,
    "icy": 2.0,
    "crater": 2.5,
}


def terrain_weight(graph: nx.Graph, s: str, t: str, data: Dict[str, Any]) -> float:
    """Compute a terrain-dependent traversal cost between two nodes."""
    terrain_s = str(graph.nodes[s].get("terrain", "plain")).strip().lower()
    terrain_t = str(graph.nodes[t].get("terrain", "plain")).strip().lower()

    base_weight = 10.0
    multiplier = (
        TERRAIN_MULTIPLIERS.get(terrain_s, 1.0) + TERRAIN_MULTIPLIERS.get(terrain_t, 1.0)
    ) / 2.0
    return base_weight * multiplier

def normalize_terrain(value: str) -> str:
    if not value:
        return ""

    v = value.strip().lower()

    # common noise removal
    v = v.replace(" terrain", "")
    v = v.replace(" area", "")
    v = v.replace("_", " ")
    v = v.replace("-", " ")

    # canonical mapping
    if "rock" in v:
        return "rocky"
    if "sand" in v:
        return "sandy"
    if "ice" in v:
        return "icy"
    if "crater" in v:
        return "crater"
    if "plain" in v:
        return "plain"

    return v

Priority = Literal["high", "medium", "low"]


def _priority_rank(p: str) -> int:
    """Sort order: high -> medium -> low. Unknown goes last."""
    p = (p or "").strip().lower()
    return {"high": 0, "medium": 1, "low": 2}.get(p, 3)

# -----------------------------
# Tool
# -----------------------------
class RoversPathTool(BaseTool):
    """
    CrewAI tool that computes rover feasibility candidates for each goal.

    - Iterates goals in priority order: High -> Medium -> Low (case-insensitive).
    - For each goal, evaluates every rover.
    - A rover is a candidate only if:
        * terrain compatible
        * a route exists to visit all targets and return to start
        * route does NOT pass through prohibited nodes (if provided)
        * energy feasibility: 100 - (distance * energy_cost) >= energy_threshold
    - distance returned is ROUND TRIP (go through all targets, then return).
    """

    name: str = "rovers_path_tool"
    description: str = (
        "For each goal, evaluates all rovers and returns feasible candidates with round-trip path, "
        "distance, energy_required, and recharge_before. A rover is feasible only if terrain is compatible, "
        "a route exists (including return), prohibited_nodes are avoided, and energy feasibility holds."
    )

    mars_map: str = ""
    rovers: dict = List[Dict]

    def __init__(self, mars_map, rovers, **kwargs):
        super().__init__(**kwargs)

        self.mars_map = mars_map
        self.rovers = rovers

    def _run(
        self,
        goals: list,
        prohibited_nodes: list = None,
        use_terrain_weight: bool = True,
        energy_cost: float = 0.2,
        energy_threshold: float = 5.0,
    ) -> List[GoalCandidates]:
        """
        Compute candidates for each goal (ordered high -> medium -> low).

        Params:
        - goals: list of goal dicts with keys: id, target_nodes, terrain, priority
        - prohibited_nodes: list of node ids that must NOT appear in the route
        - use_terrain_weight: if True, use terrain_weight for Dijkstra edge costs
        - energy_cost: multiplier applied to distance to compute energy_required
        - energy_threshold: rover should not end below this threshold

        Output:
        - List[dict], one per goal, each containing candidates and no_candidates.
        """
        prohibited_nodes = prohibited_nodes or []
        prohibited_set: Set[str] = set(str(n).strip() for n in prohibited_nodes if str(n).strip())

        base_graph = nx.read_graphml(self.mars_map)
        if prohibited_set:
            graph = base_graph.copy()
            # Remove only nodes that actually exist in the graph
            to_remove = [n for n in prohibited_set if n in graph]
            graph.remove_nodes_from(to_remove)
        else:
            graph = base_graph
        weight_fn = (lambda s, t, d: terrain_weight(graph, s, t, d)) if use_terrain_weight else None

        # Sort goals by priority (stable)
        goals_sorted = sorted(goals, key=lambda g: _priority_rank(str(g.get("priority", "")).lower()))
        results: List[GoalCandidates] = []

        for goal in goals_sorted:
            goal_id = str(goal.get("goal_id", "")).strip()
            goal_description = str(goal.get("description", "")).strip()

            terrain = normalize_terrain(goal.get("terrain", "").strip())

            priority = str(goal.get("priority", "")).strip().lower() or "medium"

            # Read targets
            target_nodes = goal.get("target_nodes") or []
            target_nodes = [str(x).strip() for x in target_nodes if str(x).strip()]

            goal_out = GoalCandidates(
                goal_id=goal_id,
                priority=priority, 
                description=goal_description,
                terrain=terrain,
                target_nodes=target_nodes,
                candidates=[],
                no_candidates=[],
            )

            for rover in self.rovers:
                rover_id = str(rover.get("id", "")).strip()
                source = str(rover.get("location", "")).strip()

                # Skip malformed rover without id
                if not rover_id:
                    continue

                if not source:
                    goal_out.no_candidates.append(
                        RoverRejection(rover_id=rover_id, reason="missing rover.location")
                    )
                    continue

                if prohibited_set and source in prohibited_set:
                    goal_out.no_candidates.append(
                        RoverRejection(
                            rover_id=rover_id,
                            reason=f"rover starts on prohibited node {source}"
                        )
                    )
                    continue

                compat = rover.get("terrain_compatibility") or []
                compat = [normalize_terrain(x) for x in compat if x]

                # Terrain compatibility check
                if terrain and terrain not in compat:
                    goal_out.no_candidates.append(
                        RoverRejection(
                            rover_id=rover_id,
                            reason=f"incompatible terrain: rover supports {compat}, goal requires '{terrain}'",
                        )
                    )
                    continue

                if not target_nodes:
                    goal_out.no_candidates.append(
                        RoverRejection(rover_id=rover_id, reason="Goal has no target_nodes. It is not a clear goal.")
                    )
                    continue

                # Compute chained path: source -> target1 -> target2 -> ... -> source
                total_distance = 0.0
                full_path: List[str] = []
                current = source

                try:
                    # Forward legs
                    for idx, tnode in enumerate(target_nodes):
                        leg_path = nx.dijkstra_path(graph, current, tnode, weight=weight_fn)
                        leg_dist = nx.dijkstra_path_length(graph, current, tnode, weight=weight_fn)

                        total_distance += float(leg_dist)

                        if idx == 0:
                            full_path.extend(leg_path)
                        else:
                            full_path.extend(leg_path[1:])

                        current = tnode

                    # Return leg to start
                    ret_path = nx.dijkstra_path(graph, current, source, weight=weight_fn)
                    ret_dist = nx.dijkstra_path_length(graph, current, source, weight=weight_fn)

                    total_distance += float(ret_dist)
                    full_path.extend(ret_path[1:])

                except nx.NetworkXNoPath:
                    goal_out.no_candidates.append(
                        RoverRejection(
                            rover_id=rover_id,
                            reason=f"no path for chained route from {source} to targets {target_nodes} and return",
                        )
                    )
                    continue
                except nx.NodeNotFound as e:
                    goal_out.no_candidates.append(
                        RoverRejection(rover_id=rover_id, reason=f"node not found: {str(e)}")
                    )
                    continue


                # Energy feasibility check
                energy_required = float(total_distance) * float(energy_cost)

                # Infeasible even after recharge to 100
                if (100.0 - energy_required) < float(energy_threshold):
                    goal_out.no_candidates.append(
                        RoverRejection(
                            rover_id=rover_id,
                            reason=(
                                f"energy infeasible even after recharge: "
                                f"100 - {energy_required:.2f} < {energy_threshold} = (full battery - energy cost) < energy threshold. Total distance {total_distance}"
                            ),
                        )
                    )
                    continue

                rover_energy = float(rover.get("energy", 0.0))
                recharge_before = (rover_energy - energy_required) <= float(energy_threshold)

                if not source:
                    goal_out.no_candidates.append(
                        RoverRejection(
                            rover_id=rover_id,
                            reason=f"no path for chained route to targets {target_nodes} and return",
                        )
                    )
                    continue

                goal_out.candidates.append(
                    RoverCandidate(
                        rover_id=rover_id,
                        path=full_path,
                        distance=float(total_distance),
                        energy_required=float(energy_required),
                        recharge_before=bool(recharge_before),
                        speed=float(rover.get("speed", 0.0)),
                        location=source
                    )
                )
            
            if goal_out.candidates:
                goal_out.no_candidates.clear()
            print("Rover TOOL GOOD")

            results.append(goal_out)

        return results
