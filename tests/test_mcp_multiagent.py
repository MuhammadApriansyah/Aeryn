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
    import asyncio
    from aeryn_core.multi_agent.orchestrator import get_supervisor, ParallelOrchestrator

    supervisor = get_supervisor()

    async def _run():
        # Route tasks to divisions
        creative = await supervisor.route("Write a poem")
        assert creative == "creative"

        reasoning = await supervisor.route("Analyze this logic")
        assert reasoning == "reasoning"

        # Handoff between divisions
        handoff = await supervisor.handoff("creative", "reasoning", "Critique my poem")
        assert handoff.from_agent == "creative"
        assert handoff.to_agent == "reasoning"

        # Broadcast
        recipients = await supervisor.broadcast("supervisor", "Hello all")
        assert len(recipients) == 5

        # Blackboard
        await supervisor.blackboard.write("key", "value")
        val = await supervisor.blackboard.read("key")
        assert val == "value"

        # Metrics
        metrics = supervisor.get_metrics()
        assert "coordination_efficiency" in metrics

    asyncio.run(_run())

    print("✓ MultiAgentOrchestrator (Supervisor)")


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
