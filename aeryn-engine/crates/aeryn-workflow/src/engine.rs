//! Workflow engine for orchestrating multi-step processes.

use std::collections::{HashMap, HashSet, VecDeque};

use serde::{Deserialize, Serialize};
use tracing::{debug, info, instrument};

use aeryn_core::error::{AerynError, AerynResult};
use aeryn_core::types::{Id, WorkflowDefinition, WorkflowEdge, WorkflowNode, WorkflowNodeType, Value};

/// Workflow configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowConfig {
    /// Maximum number of nodes.
    pub max_nodes: usize,
    /// Maximum execution depth.
    pub max_depth: usize,
    /// Timeout per node in milliseconds.
    pub node_timeout_ms: u64,
    /// Whether to enable parallel execution.
    pub enable_parallel: bool,
    /// Maximum concurrent nodes.
    pub max_concurrent: usize,
}

impl Default for WorkflowConfig {
    fn default() -> Self {
        Self {
            max_nodes: 1000,
            max_depth: 100,
            node_timeout_ms: 30000,
            enable_parallel: true,
            max_concurrent: 4,
        }
    }
}

/// Workflow execution statistics.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowStats {
    pub total_executions: u64,
    pub successful_executions: u64,
    pub failed_executions: u64,
    pub avg_execution_time_ms: f64,
    pub total_nodes_executed: u64,
}

/// Workflow engine for executing workflow definitions.
pub struct WorkflowEngine {
    config: WorkflowConfig,
    stats: WorkflowStats,
}

impl WorkflowEngine {
    pub fn new(config: WorkflowConfig) -> Self {
        Self {
            config,
            stats: WorkflowStats {
                total_executions: 0,
                successful_executions: 0,
                failed_executions: 0,
                avg_execution_time_ms: 0.0,
                total_nodes_executed: 0,
            },
        }
    }

    pub fn with_default_config() -> Self {
        Self::new(WorkflowConfig::default())
    }

    #[instrument(skip(self, workflow, inputs))]
    pub fn execute(
        &mut self,
        workflow: &WorkflowDefinition,
        inputs: HashMap<String, Value>,
    ) -> AerynResult<HashMap<String, Value>> {
        if workflow.nodes.is_empty() {
            return Err(AerynError::Validation("Workflow has no nodes".to_string()));
        }

        if workflow.nodes.len() > self.config.max_nodes {
            return Err(AerynError::Validation("Too many nodes".to_string()));
        }

        // Build adjacency list
        let mut adjacency: HashMap<String, Vec<String>> = HashMap::new();
        let mut in_degree: HashMap<String, usize> = HashMap::new();

        for node in &workflow.nodes {
            adjacency.entry(node.id.clone()).or_insert_with(Vec::new);
            in_degree.entry(node.id.clone()).or_insert(0);
        }

        for edge in &workflow.edges {
            adjacency.entry(edge.source.clone()).or_insert_with(Vec::new).push(edge.target.clone());
            *in_degree.entry(edge.target.clone()).or_insert(0) += 1;
        }

        // Find start nodes (no incoming edges)
        let mut queue: VecDeque<String> = in_degree
            .iter()
            .filter(|(_, &deg)| deg == 0)
            .map(|(id, _)| id.clone())
            .collect();

        let mut results: HashMap<String, Value> = inputs.clone();
        let mut executed: HashSet<String> = HashSet::new();
        let mut depth: HashMap<String, usize> = HashMap::new();

        while let Some(node_id) = queue.pop_front() {
            if executed.contains(&node_id) {
                continue;
            }

            let node_depth = *depth.get(&node_id).unwrap_or(&0);
            if node_depth > self.config.max_depth {
                return Err(AerynError::Validation("Max depth exceeded".to_string()));
            }

            // Find the node
            let node = workflow.nodes.iter().find(|n| n.id == node_id).unwrap();

            // Execute node
            debug!("Executing node: {} (type: {})", node_id, node.node_type);
            self.stats.total_nodes_executed += 1;

            let output = self.execute_node(node, &results)?;
            results.insert(node_id.clone(), output);
            executed.insert(node_id.clone());

            // Add neighbors to queue
            if let Some(neighbors) = adjacency.get(&node_id) {
                for neighbor in neighbors {
                    let neighbor_degree = in_degree.get_mut(neighbor).unwrap();
                    *neighbor_degree -= 1;
                    if *neighbor_degree == 0 {
                        depth.insert(neighbor.clone(), node_depth + 1);
                        queue.push_back(neighbor.clone());
                    }
                }
            }
        }

        self.stats.total_executions += 1;
        self.stats.successful_executions += 1;

        Ok(results)
    }

    fn execute_node(
        &self,
        node: &WorkflowNode,
        inputs: &HashMap<String, Value>,
    ) -> AerynResult<Value> {
        match node.node_type {
            WorkflowNodeType::Input => {
                // Input nodes just pass through their config as value
                Ok(node.config.get("value").cloned().unwrap_or(Value::Null))
            }
            WorkflowNodeType::Output => {
                // Output nodes return the first input value
                Ok(inputs.values().next().cloned().unwrap_or(Value::Null))
            }
            WorkflowNodeType::Llm => {
                // LLM nodes would call an LLM (placeholder)
                Ok(Value::String(format!("LLM output for node {}", node.id)))
            }
            WorkflowNodeType::Retrieval => {
                // Retrieval nodes would search a vector store (placeholder)
                Ok(Value::Array(vec![
                    Value::String("Document 1".to_string()),
                    Value::String("Document 2".to_string()),
                ]))
            }
            WorkflowNodeType::Tool => {
                // Tool nodes would call a tool (placeholder)
                Ok(Value::String(format!("Tool output for node {}", node.id)))
            }
            WorkflowNodeType::Condition => {
                // Condition nodes evaluate a condition
                let condition = node.config.get("condition").and_then(|v| v.as_str()).unwrap_or("true");
                Ok(Value::Bool(condition == "true"))
            }
            WorkflowNodeType::Transform => {
                // Transform nodes apply a transformation
                Ok(inputs.values().next().cloned().unwrap_or(Value::Null))
            }
        }
    }

    pub fn stats(&self) -> &WorkflowStats {
        &self.stats
    }

    pub fn config(&self) -> &WorkflowConfig {
        &self.config
    }
}
