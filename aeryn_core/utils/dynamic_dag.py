class DynamicTopologicalTaskEngine:
    def __init__(self):
        self.adj_matrix = {}
        self.node_metadata = {}

    def insert_runtime_task_node(self, node_id: str, upstream_dependency_id: str, downstream_target_id: str) -> bool:
        if upstream_dependency_id not in self.adj_matrix or downstream_target_id not in self.adj_matrix:
            return False
            
        if node_id not in self.adj_matrix:
            self.adj_matrix[node_id] = []
            
        if node_id in self.adj_matrix[upstream_dependency_id]:
            return True
            
        if downstream_target_id in self.adj_matrix[upstream_dependency_id]:
            self.adj_matrix[upstream_dependency_id].remove(downstream_target_id)
            
        self.adj_matrix[upstream_dependency_id].append(node_id)
        self.adj_matrix[node_id].append(downstream_target_id)
        return True

    def reset_topology_to_static_baseline(self, baseline_adj_matrix_dict: dict) -> None:
        self.adj_matrix = {k: list(v) for k, v in baseline_adj_matrix_dict.items()}
