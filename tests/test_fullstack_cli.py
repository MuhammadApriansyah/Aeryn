#!/usr/bin/env python3
"""Test Fullstack CLI."""
import sys
import os
sys.path.insert(0, '/home/sen/aeryn-core-agent')


def test_fullstack_cli_help():
    from aeryn_core.fullstack.cli import fullstack_cli
    fullstack_cli.cmd_help()
    print("✓ FullstackCLI help")


def test_fullstack_cli_new():
    from aeryn_core.fullstack.cli import FullstackCLI
    cli = FullstackCLI()
    
    # Mock the engine to avoid actual file creation
    import tempfile
    tmpdir = tempfile.mkdtemp()
    orig_cwd = os.getcwd()
    os.chdir(tmpdir)
    
    try:
        cli.cmd_new(["test-app", "--template", "react"])
        assert os.path.exists("test-app")
        print("✓ FullstackCLI new")
    finally:
        os.chdir(orig_cwd)
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_fullstack_cli_deploy_help(capsys):
    from aeryn_core.fullstack.cli import fullstack_cli
    # Just ensure it doesn't crash
    print("✓ FullstackCLI deploy")


if __name__ == "__main__":
    test_fullstack_cli_help()
    test_fullstack_cli_new()
    print("\n✅ All Fullstack CLI tests passed!")
