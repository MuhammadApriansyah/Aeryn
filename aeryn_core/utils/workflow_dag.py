import asyncio

class CognitiveTaskNode:
    def __init__(self, node_id: str, division_code: int, fsm_gate_code: int):  # u8 → int (Rust remnant)
        self.node_id = node_id
        self.division_code = division_code
        self.fsm_gate_code = fsm_gate_code
        self.dependencies = []
        self.execution_status = "PENDING_SATELLITE"

class DirectedAcyclicGraphWorkflowEngine:
    def __init__(self):
        self.nodes = {}
        self.workflow_execution_logs = []

    def register_cognitive_task_node(self, node_id: str, division_code: int, fsm_gate_code: int):
        """Mendaftarkan simpul node divisi kognitif ke dalam peta koordinat DAG."""
        if node_id not in self.nodes:
            self.nodes[node_id] = CognitiveTaskNode(node_id, division_code, fsm_gate_code)

    def bind_task_dependency(self, target_node_id: str, depends_on_node_id: str):
        """Merajut garis arah ketergantungan (Dependency Edge). Target baru bisa jalan jika dependensi sukses."""
        if target_node_id in self.nodes and depends_on_node_id in self.nodes:
            self.nodes[target_node_id].dependencies.append(depends_on_node_id)

    def topological_sort_evaluation_path(self) -> list:
        """Evaluasi Matematika Graf: Mengurutkan jalur eksekusi agar terbebas dari siklus deadlock."""
        visited = set()
        temp_stack = set()
        ordered_path = []

        def traverse_depth_first(node_id):
            if node_id in temp_stack:
                raise RuntimeError("Architectural Cycle Detected: Fatal deadlock in DAG workflow path.")
            if node_id not in visited:
                temp_stack.add(node_id)
                for dep in self.nodes[node_id].dependencies:
                    traverse_depth_first(dep)
                temp_stack.remove(node_id)
                visited.add(node_id)
                ordered_path.append(node_id)

        for node_id in self.nodes:
            if node_id not in visited:
                traverse_depth_first(node_id)

        return ordered_path

