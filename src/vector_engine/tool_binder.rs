use std::collections::HashMap;

#[derive(Clone, Debug)]
pub struct SovereignToolDefinition {
    pub tool_name: String,
    pub description: String,
    pub json_schema_parameters: String,
    pub execution_clearance_level: u8,
}

pub struct CoreEnvironmentToolBinder {
    pub registered_tools: std::sync::Mutex<HashMap<String, Vec<SovereignToolDefinition>>>,
}

impl CoreEnvironmentToolBinder {
    pub fn new() -> Self {
        Self {
            registered_tools: std::sync::Mutex::new(HashMap::new()),
        }
    }

    pub fn bind_external_environment_tool(&self, session_id: &str, name: &str, desc: &str, schema: &str, clearance: u8) -> Result<(), String> {
        let mut tools_guard = self.registered_tools.lock().map_err(|e| e.to_string())?;
        let session_bucket = tools_guard.entry(session_id.to_string()).or_insert_with(Vec::new);
        
        session_bucket.retain(|t| t.tool_name != name);
        
        session_bucket.push(SovereignToolDefinition {
            tool_name: name.to_string(),
            description: desc.to_string(),
            json_schema_parameters: schema.to_string(),
            execution_clearance_level: clearance,
        });
        Ok(())
    }

    pub fn compile_available_tools_manifest(&self, session_id: &str) -> String {
        let mut manifest_string = String::new();
        if let Ok(tools_guard) = self.registered_tools.lock() {
            if let Some(session_bucket) = tools_guard.get(session_id) {
                for (idx, tool) in session_bucket.iter().enumerate() {
                    manifest_string.push_str(&format!(
                        "Tool #{}:\n- Name: {}\n- Description: {}\n- Schema: {}\n- Clearance: {}\n\n",
                        idx + 1, tool.tool_name, tool.description, tool.json_schema_parameters, tool.execution_clearance_level
                    ));
                }
            }
        }
        manifest_string
    }
}

