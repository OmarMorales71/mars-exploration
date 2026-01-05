from __future__ import annotations

from crewai.tools import BaseTool
import networkx as nx
from typing import Dict, Any, List, Optional

# Terrain traversal multipliers (same as your current tool)
TERRAIN_MULTIPLIERS = {
    "plain": 1.0,
    "rocky": 1.3,
    "sandy": 1.6,
    "icy": 2.0,
    "crater": 2.5
}


def terrain_weight(graph: nx.Graph, s: str, t: str, data: dict) -> float:
    terrain_s = graph.nodes[s].get("terrain", "plain")
    terrain_t = graph.nodes[t].get("terrain", "plain")
    base_weight = 10.0
    multiplier = (TERRAIN_MULTIPLIERS.get(terrain_s, 1.0) + TERRAIN_MULTIPLIERS.get(terrain_t, 1.0)) / 2.0
    return base_weight * multiplier


def _edge_length(graph: nx.Graph, u: str, v: str, default: float = 10.0) -> float:
    """
    Prefer edge attribute 'length' if present; fallback to default.
    Supports GraphML that loads into Graph or MultiGraph-like structures.
    """
    ed = graph.get_edge_data(u, v)
    if ed is None:
        return default

    if isinstance(ed, dict) and "length" in ed:
        return float(ed["length"])

    # Multi-edge case
    if isinstance(ed, dict):
        for _, attrs in ed.items():
            if isinstance(attrs, dict) and "length" in attrs:
                return float(attrs["length"])

    return default


class RoverRouteTool(BaseTool):
    """
    Tool that computes rover route + time + energy feasibility in one call.
    """
    name: str = "rover_route_tool"
    description: str = (
        "Computes the best route for a rover from its current location to a target node, "
        "returning the path, terrain-weighted distance, travel time using rover speed, and "
        "energy consumption. If rover energy is below the recharge threshold, it recharges "
        "first. Marks feasibility if energy is insufficient."
    )

    def _run(
        self,
        graphml_path: str,
        rover: Dict[str, Any],
        target_node: str,
        use_terrain_weight: bool = True,
        recharge_threshold: float = 30.0,
        recharge_to: float = 100.0,
        energy_per_unit_distance: float = 0.4,
        default_edge_length: float = 10.0,
    ) -> Dict[str, Any]:

        graph = nx.read_graphml(graphml_path)

        rover_id = rover.get("id", "")
        source = rover.get("location")
        energy_before = float(rover.get("energy", 0.0))
        speed = float(rover.get("speed", 0.0))

        if not source:
            return {"feasible": False, "reason": "missing_rover_location", "rover_id": rover_id}

        if speed <= 0:
            return {"feasible": False, "reason": "invalid_rover_speed", "rover_id": rover_id}

        # Compute route
        try:
            if use_terrain_weight:
                w = lambda s, t, d: terrain_weight(graph, s, t, d)
                distance = float(nx.dijkstra_path_length(graph, source, target_node, weight=w))
                path: List[str] = nx.dijkstra_path(graph, source, target_node, weight=w)
            else:
                distance = float(nx.dijkstra_path_length(graph, source, target_node))
                path = nx.dijkstra_path(graph, source, target_node)
        except nx.NetworkXNoPath:
            return {"feasible": False, "reason": "no_path", "rover_id": rover_id, "source": source, "target": target_node}
        except Exception as e:
            return {"feasible": False, "reason": f"routing_error: {e}", "rover_id": rover_id, "source": source, "target": target_node}

        # Recharge logic (before moving)
        recharge_before = energy_before < recharge_threshold
        energy = recharge_to if recharge_before else energy_before

        # Simulate energy + time over the path
        total_time_min = 0.0
        total_energy_cost = 0.0

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            length = _edge_length(graph, u, v, default=default_edge_length)

            terrain = graph.nodes[u].get("terrain", "plain")
            mult = TERRAIN_MULTIPLIERS.get(terrain, 1.0)

            step_time = length / speed
            step_energy = length * energy_per_unit_distance * mult

            total_time_min += step_time
            total_energy_cost += step_energy
            energy -= step_energy

            if energy <= 0:
                return {
                    "feasible": False,
                    "reason": "energy_depleted_mid_route",
                    "rover_id": rover_id,
                    "source": source,
                    "target": target_node,
                    "path": path,
                    "distance": distance,
                    "time_min": round(total_time_min, 3),
                    "energy_before": energy_before,
                    "recharge_before": recharge_before,
                    "energy_cost": round(total_energy_cost, 3),
                    "energy_after": 0.0,
                }

        return {
            "feasible": True,
            "rover_id": rover_id,
            "source": source,
            "target": target_node,
            "path": path,
            "distance": distance,
            "time_min": round(total_time_min, 3),
            "energy_before": energy_before,
            "recharge_before": recharge_before,
            "energy_cost": round(total_energy_cost, 3),
            "energy_after": round(max(0.0, energy), 3),
        }
