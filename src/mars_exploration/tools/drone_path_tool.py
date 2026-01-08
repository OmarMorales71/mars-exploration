from __future__ import annotations

from typing import Any, Dict, List, Set

import networkx as nx
from crewai.tools import BaseTool

from mars_exploration.models.drone_models import GoalCandidates, DroneCandidate, DroneRejection


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


def _priority_rank(p: str) -> int:
    p = (p or "").strip().lower()
    return {"high": 0, "medium": 1, "low": 2}.get(p, 3)


class DronesPathTool(BaseTool):
    """
    Computes feasibility candidates for each drone goal.

    Assumptions (simple on purpose):
    - Dijkstra distance is treated as "minutes" for time estimation: time_required = distance.
    - Each drone's base node is its initial location.
    - Constraint: drone must complete ROUND TRIP within max_time where:
        max_time = min(25, drone['range'])  (range is treated as time budget)
    - prohibited_nodes can be provided. If provided, those nodes are removed from the graph
      so Dijkstra will try alternative routes.
    - Goals are processed in priority order: high -> medium -> low.
    """

    name: str = "drones_path_tool"
    description: str = (
        "For each goal, evaluates all drones and returns candidates with round-trip route visiting all target_nodes in order and returning to start. "
        "Feasible only if route exists after removing prohibited_nodes and time_required is enough"
    )

    mars_map: str = ""
    drones: List[Dict[str, Any]] = []

    def __init__(self, mars_map, drones, **kwargs):
        super().__init__(**kwargs)
        self.mars_map = mars_map
        self.drones = drones

    def _run(
        self,
        goals: list,
        prohibited_nodes: list = None,
        use_terrain_weight: bool = True,
        flight_time_threshold: float = 240, # 4 hours
        time_cost: float = 1.0,
    ) -> List[Dict[str, Any]]:
        if not time_cost:
            time_cost = 1.0

        if use_terrain_weight and time_cost>0.5: #to have realistic time costs
            time_cost=0.15

        prohibited_nodes = prohibited_nodes or []
        prohibited_set: Set[str] = {str(n).strip() for n in prohibited_nodes if str(n).strip()}

        base_graph = nx.read_graphml(self.mars_map)
        if prohibited_set:
            graph = base_graph.copy()
            to_remove = [n for n in prohibited_set if n in graph]
            graph.remove_nodes_from(to_remove)
        else:
            graph = base_graph

        weight_fn = (lambda s, t, d: terrain_weight(graph, s, t, d)) if use_terrain_weight else None

        goals_sorted = sorted(goals, key=lambda g: _priority_rank(str(g.get("priority", "")).lower()))
        results: List[GoalCandidates] = []

        for goal in goals_sorted:
            goal_id = str(goal.get("goal_id", goal.get("id", ""))).strip()
            description = str(goal.get("description", "")).strip()
            priority = str(goal.get("priority", "")).strip().lower() or "medium"
            terrain = normalize_terrain(str(goal.get("terrain", "")).strip())

            target_nodes = goal.get("target_nodes") or []
            target_nodes = [str(x).strip() for x in target_nodes if str(x).strip()]

            out = GoalCandidates(
                goal_id=goal_id,
                description=description,
                priority=priority,
                terrain=terrain,
                target_nodes=target_nodes,
                candidates=[],
                no_candidates=[],
            )

            for drone in self.drones:
                drone_id = str(drone.get("id", "")).strip()
                start = str(drone.get("location", "")).strip()

                if not drone_id:
                    continue
                if not start:
                    out.no_candidates.append(DroneRejection(drone_id=drone_id, reason="missing drone.location"))
                    continue
                if prohibited_set and start in prohibited_set:
                    out.no_candidates.append(DroneRejection(drone_id=drone_id, reason=f"drone starts on prohibited node {start}"))
                    continue

                try:
                    drone_range = float(drone.get("range", 0))
                except Exception:
                    drone_range = 0.0

                max_time = min(flight_time_threshold, drone_range)
                if not target_nodes:
                    out.no_candidates.append(
                        DroneRejection(drone_id=drone_id, reason="Goal has no target_nodes. It is not a clear goal.")
                    )
                    continue

                total_dist = 0.0
                full_path: List[str] = []
                current = start

                try:
                    for idx, tnode in enumerate(target_nodes):
                        leg_path = nx.dijkstra_path(graph, current, tnode, weight=weight_fn)
                        leg_dist = nx.dijkstra_path_length(graph, current, tnode, weight=weight_fn)
                        total_dist += float(leg_dist)
                        if idx == 0:
                            full_path.extend(leg_path)
                        else:
                            full_path.extend(leg_path[1:])
                        current = tnode

                    # return to start
                    ret_path = nx.dijkstra_path(graph, current, start, weight=weight_fn)
                    ret_dist = nx.dijkstra_path_length(graph, current, start, weight=weight_fn)
                    total_dist += float(ret_dist)
                    full_path.extend(ret_path[1:])

                except nx.NetworkXNoPath:
                    out.no_candidates.append(
                        DroneRejection(
                            drone_id=drone_id,
                            reason=f"no path found to complete goal from {start} to {target_nodes}",
                        )
                    )
                    continue
                except nx.NodeNotFound as e:
                    out.no_candidates.append(DroneRejection(drone_id=drone_id, reason=f"node not found: {str(e)}"))
                    continue

                time_required = float(total_dist)*time_cost

                if time_required > max_time:
                    out.no_candidates.append(
                        DroneRejection(
                            drone_id=drone_id,
                            reason=f"time exceeds limit: {time_required:.2f}. Limit of drone is {max_time:.2f}",
                        )
                    )
                    continue

                out.candidates.append(
                    DroneCandidate(
                        drone_id=drone_id,
                        path=full_path,
                        distance=float(total_dist),
                        time_required=float(time_required),
                        location=start,
                        altitude=float(drone.get("altitude", 0)),
                        camera_resolution=str(drone.get("camera_resolution", "")),
                    )
                )

            results.append(out)

        return results
