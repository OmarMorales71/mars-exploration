from crewai.tools import BaseTool
import networkx as nx
from typing import Dict


# Terrain traversal multipliers
TERRAIN_MULTIPLIERS = {
    "plain": 1.0,
    "rocky": 1.3,
    "sandy": 1.6,
    "icy": 2.0,
    "crater": 2.5
}


def terrain_weight(graph, s, t, data):
    """
    Computes a terrain-dependent traversal cost between two nodes.
    """
    terrain_s = graph.nodes[s].get("terrain", "plain")
    terrain_t = graph.nodes[t].get("terrain", "plain")

    base_weight = 10
    multiplier = (
        TERRAIN_MULTIPLIERS.get(terrain_s, 1.0)
        + TERRAIN_MULTIPLIERS.get(terrain_t, 1.0)
    ) / 2

    return base_weight * multiplier


class ShortestPathTool(BaseTool):
    """
    CrewAI tool to compute shortest distance and path in the Mars terrain graph.
    """

    name: str = "shortest_path_tool"
    description: str = (
        "Computes the shortest distance and path between two locations in the Mars "
        "terrain graph using Dijkstra's algorithm. Supports optional terrain-based "
        "cost weighting."
    )

    def _run(
        self,
        graphml_path: str,
        source: str,
        target: str,
        use_terrain_weight: bool = True
    ) -> Dict:
        """
        Compute shortest path and distance.
        """

        graph = nx.read_graphml(graphml_path)

        try:
            if use_terrain_weight:
                distance = nx.dijkstra_path_length(
                    graph,
                    source,
                    target,
                    weight=lambda s, t, d: terrain_weight(graph, s, t, d)
                )
                path = nx.dijkstra_path(
                    graph,
                    source,
                    target,
                    weight=lambda s, t, d: terrain_weight(graph, s, t, d)
                )
            else:
                distance = nx.dijkstra_path_length(graph, source, target)
                path = nx.dijkstra_path(graph, source, target)

            return {
                "source": source,
                "target": target,
                "distance": distance,
                "path": path
            }

        except nx.NetworkXNoPath:
            return {
                "error": f"No path found between {source} and {target}"
            }
