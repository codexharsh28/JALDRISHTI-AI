"""
Automated Tests for River Directed Graph Topology and Routing Invariants.
"""

from ml.streamflow.graph_model import RiverGraphStreamflowModel

def test_river_graph_directed_acyclicity():
    model = RiverGraphStreamflowModel()
    topo = model.river_topology

    visited = set()
    rec_stack = set()

    def is_cyclic(node):
        visited.add(node)
        rec_stack.add(node)
        ds = topo.get(node, {}).get("downstream")
        if ds and ds in topo:
            if ds not in visited:
                if is_cyclic(ds):
                    return True
            elif ds in rec_stack:
                return True
        rec_stack.remove(node)
        return False

    for stn in topo:
        if stn not in visited:
            assert not is_cyclic(stn), f"Cycle detected involving station {stn}"

def test_river_reach_travel_time_positive():
    model = RiverGraphStreamflowModel()
    for edge, attrs in model.river_topology.items():
        assert attrs["distance_km"] > 0
        assert attrs["lag_hours"] > 0
