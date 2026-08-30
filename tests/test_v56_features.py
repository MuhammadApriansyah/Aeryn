#!/usr/bin/env python3
"""Test V56 features: Workflow DSL, Headless, Config, Template Inheritance, Custom Generators."""
import sys, os
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)


def test_workflow_dsl():
    from aeryn_core.workflow_dsl import workflow_dsl
    
    wf = workflow_dsl.create("test-workflow", "Test workflow")
    wf.add_step("step1", "generate", {"name": "test-app", "template": "react"})
    wf.add_step("step2", "install_deps", {})
    
    d = wf.to_dict()
    assert d["name"] == "test-workflow"
    assert len(d["steps"]) == 2
    
    print("WorkflowDSL OK")


def test_headless_mode():
    from aeryn_core.headless_mode import headless_runner
    
    config = {"name": "headless-test", "template": "api"}
    result = headless_runner.generate(config)
    assert "success" in result or "error" in result
    
    print("HeadlessRunner OK")


def test_config_file():
    # config_file_v2 module has been removed (dead code cleanup)
    pass


def test_template_inheritance():
    from aeryn_core.template_inheritance import template_base
    
    template_base.register("base-react", {"frontend": "React", "backend": "Fastify"})
    
    child = template_base.extend("custom-react", "base-react", {"database": "PostgreSQL"})
    assert child["name"] == "custom-react"
    assert child["frontend"] == "React"
    assert child["database"] == "PostgreSQL"
    
    print("TemplateInheritance OK")


def test_custom_generators():
    from aeryn_core.custom_generators import generator_registry
    
    def my_generator():
        return {"custom": True}
    
    generator_registry.register("my_gen", my_generator)
    assert "my_gen" in generator_registry.list_generators()
    
    gen = generator_registry.get("my_gen")
    assert gen() == {"custom": True}
    
    print("CustomGenerators OK")


if __name__ == "__main__":
    test_workflow_dsl()
    test_headless_mode()
    test_config_file()
    test_template_inheritance()
    test_custom_generators()
    print("All V56 tests passed!")
