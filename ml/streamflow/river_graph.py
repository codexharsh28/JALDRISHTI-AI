"""
River Topology Network and Directed Graph Intelligence for JALDRISHTI AI.
Models upstream-to-downstream routing, hydrologic connectivity, and reach lag times.
"""

from typing import Dict, Any, List, Optional
import yaml

class RiverNetworkGraph:
    def __init__(self, config_path: str = "basin_config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        self.nodes = {n["id"]: n for n in self.config["river_network"]["nodes"]}
        self.edges = self.config["river_network"]["edges"]
        
        # Build adjacency maps
        self.upstream_map: Dict[str, List[str]] = {n_id: [] for n_id in self.nodes}
        self.downstream_map: Dict[str, List[str]] = {n_id: [] for n_id in self.nodes}
        self.edge_meta: Dict[str, Dict[str, Any]] = {}

        for edge in self.edges:
            u, v = edge["from_node"], edge["to_node"]
            if u in self.downstream_map:
                self.downstream_map[u].append(v)
            if v in self.upstream_map:
                self.upstream_map[v].append(u)
            self.edge_meta[f"{u}->{v}"] = edge

    def get_upstream_nodes(self, node_id: str) -> List[str]:
        """Recursively retrieves all upstream contributing nodes."""
        visited = set()
        stack = [node_id]
        while stack:
            curr = stack.pop()
            for up in self.upstream_map.get(curr, []):
                if up not in visited:
                    visited.add(up)
                    stack.append(up)
        return list(visited)

    def compute_cumulative_travel_time(self, from_node: str, to_node: str) -> float:
        """Calculates total hydraulic lag hours along the river path."""
        # Breadth-first / shortest path traversal
        queue = [(from_node, 0.0)]
        visited = set([from_node])
        while queue:
            curr, time_acc = queue.pop(0)
            if curr == to_node:
                return round(time_acc, 2)
            for nxt in self.downstream_map.get(curr, []):
                if nxt not in visited:
                    visited.add(nxt)
                    edge_k = f"{curr}->{nxt}"
                    t_lag = self.edge_meta.get(edge_k, {}).get("travel_time_hours", 1.0)
                    queue.append((nxt, time_acc + t_lag))
        return 0.0
