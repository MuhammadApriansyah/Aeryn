use std::collections::HashMap;

#[derive(Clone, Debug)]
pub struct GraphEdge {
    pub target_node_id: String,
    pub predicate_relation: String,
    pub structural_weight: f32,
}

#[derive(Clone, Debug)]
pub struct GraphNode {
    pub node_id: String,
    pub entity_class: String,
    pub associated_edges: Vec<GraphEdge>,
}

pub struct EpistemicWorldGraph {
    pub adjacency_list: std::sync::Mutex<HashMap<String, HashMap<String, GraphNode>>>,
}

impl EpistemicWorldGraph {
    pub fn new() -> Self {
        Self {
            adjacency_list: std::sync::Mutex::new(HashMap::new()),
        }
    }

    pub fn upsert_memory_node_isolated(&self, session_id: &str, id: &str, class: &str) -> Result<(), String> {
        let mut list_guard = self.adjacency_list.lock().map_err(|e| e.to_string())?;
        
        // PERBAIKAN CLOSURE: Gunakan dekorator || agar memenuhi bound trait FnOnce() dari kompilator
        let session_graph = list_guard.entry(session_id.to_string()).or_insert_with(|| HashMap::new());
        
        session_graph.entry(id.to_string()).or_insert_with(|| GraphNode {
            node_id: id.to_string(),
            entity_class: class.to_string(),
            associated_edges: Vec::new(),
        });
        
        Ok(())
    }

    pub fn connect_semantic_edge_isolated(&self, session_id: &str, source_id: &str, target_id: &str, relation: &str, weight: f32) -> Result<(), String> {
        let mut list_guard = self.adjacency_list.lock().map_err(|e| e.to_string())?;
        
        let session_graph = list_guard.get_mut(session_id).ok_or_else(|| {
            "Multi-Session Graph Exception: Active session context timeline registry not found.".to_string()
        })?;

        if !session_graph.contains_key(source_id) || !session_graph.contains_key(target_id) {
            return Err("Multi-Session Graph Exception: Outbound link nodes must exist within session boundary.".to_string());
        }

        if let Some(node) = session_graph.get_mut(source_id) {
            node.associated_edges.retain(|e| !(e.target_node_id == target_id && e.predicate_relation == relation));
            node.associated_edges.push(GraphEdge {
                target_node_id: target_id.to_string(),
                predicate_relation: relation.to_string(),
                structural_weight: weight,
            });
        }
        
        Ok(())
    }

    pub fn traverse_associated_neighbors_isolated(&self, session_id: &str, start_node_id: &str) -> Vec<(String, String, f32)> {
        let mut connected_sub_memories = Vec::new();
        
        if let Ok(list_guard) = self.adjacency_list.lock() {
            if let Some(session_graph) = list_guard.get(session_id) {
                if let Some(node) = session_graph.get(start_node_id) {
                    for edge in node.associated_edges.iter() {
                        connected_sub_memories.push((
                            edge.target_node_id.clone(),
                            edge.predicate_relation.clone(),
                            edge.structural_weight
                        ));
                    }
                }
            }
        }
        
        connected_sub_memories
    }

    pub fn flush_session_graph_memory(&self, session_id: &str) {
        if let Ok(mut list_guard) = self.adjacency_list.lock() {
            if let Some(session_graph) = list_guard.get_mut(session_id) {
                session_graph.clear();
            }
        }
    }
}

