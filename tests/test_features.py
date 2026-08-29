#!/usr/bin/env python3
"""Test Preview, Help, Gallery, Undo, Proactive."""
import sys
sys.path.insert(0, '/home/sen/aeryn-core-agent')


def test_preview():
    from aeryn_core.preview import project_preview
    
    plan = {
        "name": "test-app",
        "database": {
            "models": [{"name": "User", "fields": [{"name": "id", "type": "INTEGER"}]}]
        },
        "api": {
            "endpoints": [{"method": "GET", "path": "/users", "description": "List"}]
        },
        "backend": {"dependencies": ["fastify"]},
    }
    
    preview = project_preview.generate_preview(plan)
    assert preview["project_name"] == "test-app"
    assert len(preview["database"]) == 1
    assert len(preview["api_endpoints"]) == 1
    
    display = project_preview.display_preview(preview)
    assert "PROJECT PREVIEW" in display
    
    print("✓ ProjectPreview")


def test_help():
    from aeryn_core.help import help_helper
    
    help_text = help_helper.format_help("project_type")
    assert "Tipe Project" in help_text
    
    topics = help_helper.get_all_topics()
    assert len(topics) >= 4
    
    print("✓ HelpHelper")


def test_gallery():
    from aeryn_core.gallery import example_gallery
    
    examples = example_gallery.list_examples()
    assert len(examples) >= 3
    
    example = example_gallery.get_example("todo-app")
    assert example["name"] == "Todo App"
    
    display = example_gallery.display_gallery()
    assert "CONTOH PROJECT" in display
    
    print("✓ ExampleGallery")


def test_undo():
    from aeryn_core.undo import undo_manager
    
    # Record action
    undo_manager.record("create", ["/tmp/test_file.txt"], ["/tmp/test_dir"])
    
    # Check can undo
    assert undo_manager.can_undo() is True
    
    # Get last action
    last = undo_manager.get_last_action()
    assert last["action"] == "create"
    
    print("✓ UndoManager")


def test_proactive():
    from aeryn_core.proactive import proactive_warnings
    
    # Check port
    port_check = proactive_warnings.check_port(9999)
    assert port_check["available"] is True
    
    # Check dependencies
    deps = proactive_warnings.check_dependencies()
    assert "python3" in deps
    
    # Check disk
    disk = proactive_warnings.check_disk_space()
    assert "free_mb" in disk
    
    print("✓ ProactiveWarnings")


if __name__ == "__main__":
    test_preview()
    test_help()
    test_gallery()
    test_undo()
    test_proactive()
    print("\n✅ All feature tests passed!")
