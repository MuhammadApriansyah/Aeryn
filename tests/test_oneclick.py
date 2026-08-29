#!/usr/bin/env python3
"""Test One-Click Generate, Post-Guide, Progress."""
import sys
import os
sys.path.insert(0, '/home/sen/aeryn-core-agent')


def test_oneclick_generator():
    from aeryn_core.oneclick import oneclick_generator
    
    # Create temp dir for test
    import tempfile
    tmpdir = tempfile.mkdtemp()
    orig_cwd = os.getcwd()
    os.chdir(tmpdir)
    
    try:
        result = oneclick_generator.generate("test-app", "fullstack")
        assert "error" not in result
        assert result["name"] == "test-app"
        assert result["type"] == "fullstack"
        
        # Check files created
        assert os.path.exists("test-app/api/server.ts")
        assert os.path.exists("test-app/web/src/App.tsx")
        
        print("✓ OneClickGenerator fullstack")
    finally:
        os.chdir(orig_cwd)
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_postguide():
    from aeryn_core.postguide import postguide
    
    project_info = {
        "name": "test-app",
        "path": "/tmp/test-app",
        "type": "fullstack"
    }
    
    guide = postguide.generate_guide(project_info)
    assert "PROJECT BERHASIL" in guide
    assert "cd test-app" in guide
    
    print("✓ PostGuide")


def test_progress_indicator():
    from aeryn_core.progress import progress_indicator
    
    indicator = progress_indicator(3)
    indicator.start("Testing...")
    indicator.step("Step 1")
    indicator.step("Step 2")
    indicator.finish("Done!")
    
    print("✓ ProgressIndicator")


if __name__ == "__main__":
    test_oneclick_generator()
    test_postguide()
    test_progress_indicator()
    print("\n✅ All one-click tests passed!")
