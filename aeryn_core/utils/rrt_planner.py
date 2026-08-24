import math
import random

class RewardRegularizedTrajectoryPlanner:
    def __init__(self, token_budget: int = 512, step_size: float = 0.1):
        self.token_budget = token_budget
        self.step_size = step_size
        self.nodes = []

    def planning_reasoning_path(self, session_id: str, state_vector: list, reward_matrix: list) -> dict:
        if not state_vector or not reward_matrix:
            return {"path_secured": False, "generated_nodes": 0}
            
        self.nodes = [state_vector]
        budget_depleted = False
        
        for step in range(self.token_budget):
            sampled_state = [random.uniform(-1.0, 1.0) for _ in range(len(state_vector))]
            nearest_node = min(self.nodes, key=lambda n: sum((a - b) ** 2 for a, b in zip(n, sampled_state)))
            
            new_node = []
            for a, b in zip(nearest_node, sampled_state):
                delta = b - a
                distance = math.sqrt(sum((x - y) ** 2 for x, y in zip(nearest_node, sampled_state))) + 1e-15
                new_node.append(a + (delta / distance) * self.step_size)
                
            reward_score = sum(x * w for x, w in zip(new_node, reward_matrix))
            
            if reward_score > 0.0:
                self.nodes.append(new_node)
            else:
                budget_depleted = True
                break
                
        return {
            "path_secured": not budget_depleted,
            "generated_nodes": len(self.nodes),
            "session_id": session_id
        }
