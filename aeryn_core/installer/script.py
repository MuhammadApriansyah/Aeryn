#!/usr/bin/env python3
"""One-Click Installer Script Generator."""
import os
import stat
from typing import Optional

INSTALL_SCRIPT = '''#!/bin/bash
# Aeryn One-Click Installer
# Generated: {timestamp}

set -e

echo "╔══════════════════════════════════════════════════╗"
echo "║           Aeryn Installer                        ║"
echo "║   AI Personal Assistant Platform                 ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m'

echo_step() {{
    echo -e "${{GREEN}}✓${{NC}} $1"
}}

echo_warn() {{
    echo -e "${{YELLOW}}⚠${{NC}} $1"
}}

echo_error() {{
    echo -e "${{RED}}✗${{NC}} $1"
}}

# Check OS
OS="$(uname -s)"
ARCH="$(uname -m)"

echo "Detected: $OS $ARCH"

# Install Python if needed
if command -v python3 &>/dev/null; then
    echo_step "Python3 already installed"
else
    echo "Installing Python3..."
    if [ "$OS" = "Linux" ]; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-venv python3-pip
    elif [ "$OS" = "Darwin" ]; then
        brew install python3
    fi
    echo_step "Python3 installed"
fi

# Install Node.js if needed
if command -v node &>/dev/null; then
    echo_step "Node.js already installed"
else
    echo "Installing Node.js..."
    curl -fsSL https://fnm.vercel.app/install | bash
    export PATH="$HOME/.local/share/fnm:$PATH"
    eval "$(fnm env)"
    fnm install 20
    echo_step "Node.js installed"
fi

# Install Rust if needed
if command -v cargo &>/dev/null; then
    echo_step "Rust already installed"
else
    echo "Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    export PATH="$HOME/.cargo/bin:$PATH"
    echo_step "Rust installed"
fi

# Install uv (Python package manager)
if command -v uv &>/dev/null; then
    echo_step "uv already installed"
else
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo_step "uv installed"
fi

# Install maturin
if pip3 show maturin &>/dev/null; then
    echo_step "maturin already installed"
else
    echo "Installing maturin..."
    uv pip install maturin
    echo_step "maturin installed"
fi

# Install PM2
if command -v pm2 &>/dev/null; then
    echo_step "PM2 already installed"
else
    echo "Installing PM2..."
    npm install -g pm2
    echo_step "PM2 installed"
fi

# Install Bubblewrap (optional)
if command -v bwrap &>/dev/null; then
    echo_step "Bubblewrap already installed"
else
    echo_warn "Bubblewrap not found (optional, for better sandboxing)"
    echo "  Install with: sudo apt install bubblewrap"
fi

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║           Installation Complete!                 ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Clone Aeryn: git clone https://github.com/MuhammadApriansyah/Aeryn.git"
echo "  2. cd Aeryn"
echo "  3. ./aeryn-installer.sh  # or run this script again in the project dir"
echo "  4. aeryn start"
echo ""
'''

def generate_installer_script(output_path: str = "aeryn-installer.sh"):
    """Generate installer script."""
    from datetime import datetime
    script = INSTALL_SCRIPT.format(timestamp=datetime.now().isoformat())
    
    with open(output_path, 'w') as f:
        f.write(script)
    
    # Make executable
    st = os.stat(output_path)
    os.chmod(output_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    
    return output_path
