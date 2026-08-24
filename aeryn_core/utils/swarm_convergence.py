class SwarmConvergenceConsensusHandler:
    def __init__(self, agreement_floor: float = 0.60):
        self.agreement_floor = agreement_floor
        self.swarm_registry = {}

    def register_trajectory_simulation(self, convergence_pool_id: str, path_id: str, proposed_action_payload: dict, structural_fitness: float) -> dict:
        if convergence_pool_id not in self.swarm_registry:
            self.swarm_registry[convergence_pool_id] = []
            
        pool = self.swarm_registry[convergence_pool_id]
        
        serialized_action = str(sorted(proposed_action_payload.items())) if proposed_action_payload else "EMPTY_ACTION"
        
        pool.append({
            "path_id": path_id,
            "action_signature": serialized_action,
            "action_raw": proposed_action_payload,
            "fitness": structural_fitness
        })
        
        total_simulations = len(pool)
        signature_votes = {}
        
        for sim in pool:
            sig = sim["action_signature"]
            signature_votes[sig] = signature_votes.get(sig, 0) + 1
            
        winning_signature = max(signature_votes, key=signature_votes.get)
        max_votes = signature_votes[winning_signature]
        consensus_ratio = float(max_votes / total_simulations)
        
        consensus_secured = consensus_ratio >= self.agreement_floor
        
        selected_action = {}
        highest_fitness = -1.0
        for sim in pool:
            if sim["action_signature"] == winning_signature:
                if sim["fitness"] > highest_fitness:
                    highest_fitness = sim["fitness"]
                    selected_action = sim["action_raw"]
                    
        return {
            "consensus_secured": consensus_secured,
            "consensus_ratio": round(consensus_ratio, 4),
            "resolved_consensus_action": selected_action,
            "metrics": {
                "total_swarm_paths_evaluated": total_simulations,
                "distinct_trajectories_detected": len(signature_votes)
            }
        }
