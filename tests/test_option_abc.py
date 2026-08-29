#!/usr/bin/env python3
"""Test Option A, B, C modules."""
import sys
sys.path.insert(0, '/home/sen/aeryn-core-agent')


def test_proactive_engine():
    from aeryn_core.personal import proactive_engine
    
    proactive_engine.record_action("user_1", "search", "query=test")
    proactive_engine.record_action("user_1", "search", "query=ai")
    proactive_engine.record_action("user_1", "search", "query=ml")
    
    frequent = proactive_engine.get_frequent_actions("user_1", days=1)
    assert len(frequent) >= 1
    assert frequent[0]["action"] == "search"
    
    suggestions = proactive_engine.generate_suggestions("user_1")
    assert len(suggestions) >= 1
    
    print("✓ ProactiveEngine")


def test_personalization():
    from aeryn_core.personal import personalization_engine
    
    personalization_engine.set_preference("user_1", "tone", "casual")
    personalization_engine.set_preference("user_1", "language", "Indonesian")
    
    assert personalization_engine.get_preference("user_1", "tone") == "casual"
    assert personalization_engine.get_preference("user_1", "language") == "Indonesian"
    
    prefs = personalization_engine.get_all_preferences("user_1")
    assert "tone" in prefs
    assert "language" in prefs
    
    personalized = personalization_engine.personalize_prompt("user_1", "Hello")
    assert "Indonesian" in personalized
    
    print("✓ PersonalizationEngine")


def test_personal_context():
    from aeryn_core.personal import personal_context
    
    personal_context.set_context("user_1", "Sen", "AI Engineer",
                               goals=["Build AI agents", "Learn Rust"],
                               interests=["AI", "Python"])
    
    ctx = personal_context.get_context("user_1")
    assert ctx["name"] == "Sen"
    assert ctx["role"] == "AI Engineer"
    
    prompt = personal_context.build_system_prompt("user_1", "Base prompt")
    assert "Sen" in prompt
    
    print("✓ PersonalContext")


def test_agent_templates():
    from aeryn_core.infra import template_registry
    
    templates = template_registry.list_templates()
    assert len(templates) >= 5
    
    researcher = template_registry.get("researcher")
    assert researcher is not None
    assert researcher.name == "researcher"
    
    categories = template_registry.get_categories()
    assert len(categories) >= 3
    
    print("✓ AgentTemplates")


def test_agent_cli():
    from aeryn_core.infra import agent_cli
    
    # Test help
    agent_cli.cmd_help()
    
    # Test templates
    agent_cli.cmd_templates([])
    
    # Test status
    agent_cli.cmd_status([])
    
    print("✓ AgentCLI")


def test_security_dashboard():
    from aeryn_core.security.dashboard import security_dashboard
    
    security_dashboard.log_event("test", "low", "test_source", "Test event")
    events = security_dashboard.get_events()
    assert len(events) >= 1
    
    security_dashboard.create_alert("prompt_injection", "high", "Suspicious input detected", "Input blocked")
    alerts = security_dashboard.get_alerts()
    assert len(alerts) >= 1
    
    stats = security_dashboard.get_stats()
    assert "events_by_severity" in stats
    
    print("✓ SecurityDashboard")


def test_compliance():
    from aeryn_core.security.dashboard import compliance_module
    
    compliance_module.add_check("soc2", "CC6.1", "Logical access controls", "pass", "Test evidence")
    compliance_module.add_check("gdpr", "Article 17", "Right to erasure", "pending", "")
    
    checks = compliance_module.get_checks()
    assert len(checks) >= 2
    
    report = compliance_module.generate_report("soc2")
    assert "score" in report
    
    print("✓ ComplianceModule")


if __name__ == "__main__":
    test_proactive_engine()
    test_personalization()
    test_personal_context()
    test_agent_templates()
    test_agent_cli()
    test_security_dashboard()
    test_compliance()
    print("\n✅ All Option A, B, C tests passed!")
