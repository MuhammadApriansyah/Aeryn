#!/usr/bin/env python3
"""Test V50 features: Template Preview, Success Anim, Debug Mode, Custom Template, Diff Preview."""
import sys
sys.path.insert(0, '/home/sen/aeryn-core-agent')


def test_template_preview():
    from aeryn_core.template_preview import template_preview
    
    templates = template_preview.list_templates()
    assert len(templates) >= 3
    
    card = template_preview.display_card("react")
    assert "React" in card
    
    print("✓ TemplatePreview")


def test_success_animator():
    from aeryn_core.success_anim import success_animator
    # Just ensure it doesn't crash
    success_animator.complete("test-app", "/tmp/test-app")
    print("✓ SuccessAnimator")


def test_debug_mode():
    from aeryn_core.debug_mode import debug_mode
    
    debug_mode.enable()
    debug_mode.debug("Test debug message")
    debug_mode.info("Test info message")
    logs = debug_mode.get_logs()
    assert len(logs) >= 2
    debug_mode.disable()
    
    print("✓ DebugMode")


def test_custom_template():
    from aeryn_core.custom_template import template_editor
    
    # Create template
    template_editor.create_template("my-template", "Custom template", {
        "files": ["src/main.ts"],
        "dependencies": ["fastify"]
    })
    
    # Load template
    loaded = template_editor.load_template("my-template")
    assert loaded["name"] == "my-template"
    
    # List templates
    templates = template_editor.list_templates()
    assert "my-template" in templates
    
    print("✓ TemplateEditor")


def test_diff_preview():
    from aeryn_core.diff_preview import diff_preview
    
    old = {"file1.ts": "old content", "file2.ts": "same"}
    new = {"file1.ts": "new content", "file3.ts": "new file"}
    
    diffs = diff_preview.generate_diff(old, new)
    assert len(diffs) >= 2
    
    display = diff_preview.display_diff(diffs)
    assert "CHANGES" in display
    
    print("✓ DiffPreview")


if __name__ == "__main__":
    test_template_preview()
    test_success_animator()
    test_debug_mode()
    test_custom_template()
    test_diff_preview()
    print("\n✅ All V50 feature tests passed!")
