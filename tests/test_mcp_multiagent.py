#!/usr/bin/env python3
"""Test MCP, Multi-Agent, and Integration modules."""
import sys
sys.path.insert(0, '/home/sen/aeryn-core-agent')


def test_mcp_server():
    from aeryn_core.mcp.server import MCPServer
    
    server = MCPServer()
    
    # Register tool
    server.register_tool("search", "Search the web", {"type": "object", "properties": {"query": {"type": "string"}}}, "search_handler")
    tools = server.list_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "search"
    
    # Call tool
    result = server.call_tool("search", {"query": "test"})
    assert result["tool"] == "search"
    
    # Register resource
    server.register_resource("db", "Database connection", "database", {"host": "localhost"})
    resources = server.list_resources()
    assert len(resources) == 1
    
    # Register prompt
    server.register_prompt("greet", "Greeting prompt", "Hello {name}!", ["name"])
    prompts = server.list_prompts()
    assert len(prompts) == 1
    
    print("✓ MCPServer")


def test_mcp_client():
    from aeryn_core.mcp.client import MCPClient, MCPRegistry
    
    registry = MCPRegistry()
    client = registry.register("test", "http://localhost:9999")
    
    assert registry.get("test") is not None
    assert "test" in registry.list_servers()
    
    # List tools (will be empty for non-existent server)
    tools = client.list_tools()
    assert isinstance(tools, list)
    
    print("✓ MCPClient")


def test_multi_agent_orchestrator():
    from aeryn_core.multi_agent.orchestrator import MultiAgentOrchestrator, Task, TaskStatus
    
    orch = MultiAgentOrchestrator()
    
    # Register agents
    orch.register_agent("agent_1", "Researcher", ["search", "analyze"])
    orch.register_agent("agent_2", "Writer", ["write", "edit"])
    
    # Create workflow
    workflow = orch.create_workflow("Research & Write", "Research topic and write article")
    
    # Add tasks
    task1 = Task("Research", "Research the topic", "agent_1", {"topic": "AI safety"})
    task2 = Task("Write", "Write the article", "agent_2", {"format": "markdown"}, dependencies=[task1.id])
    
    workflow.add_task(task1)
    workflow.add_task(task2)
    
    assert len(workflow.tasks) == 2
    
    # Execute workflow
    result = orch.execute_workflow(workflow.id)
    assert result["status"] == "completed"
    
    # Get status
    status = orch.get_workflow_status(workflow.id)
    assert status is not None
    assert len(status["tasks"]) == 2
    
    print("✓ MultiAgentOrchestrator")


def test_integration_sdk():
    from aeryn_core.integrations.sdk import IntegrationSDK
    
    sdk = IntegrationSDK()
    
    # Register integration
    sdk.register("slack", "Slack integration", "Aeryn", "1.0.0", "communication", {"type": "object"}, "http://localhost/slack")
    
    integrations = sdk.list_integrations()
    assert len(integrations) == 1
    assert integrations[0]["name"] == "slack"
    
    print("✓ IntegrationSDK")


if __name__ == "__main__":
    test_mcp_server()
    test_mcp_client()
    test_multi_agent_orchestrator()
    test_integration_sdk()
    print("\n✅ All MCP, Multi-Agent, and Integration tests passed!")
