#!/bin/bash
# ============================================
# Sovereign AI Workbench — Ubuntu Setup
# ============================================
# Run inside WSL2 Ubuntu

set -e

echo "🛡️  Sovereign AI Workbench — Ubuntu Setup"

# System update
echo -e "\n[1/5] Updating system..."
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo -e "\n[2/5] Installing dependencies..."
sudo apt install -y \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    htop \
    tree

# Verify installations
echo -e "\n[3/5] Verifying installations..."
python3 --version
git --version

# Check NVIDIA GPU
echo -e "\n[4/5] Checking GPU..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi
    echo "✅ GPU detected"
else
    echo "⚠️  nvidia-smi not found. Install NVIDIA drivers on Windows first."
fi

# Setup Python environment
echo -e "\n[5/5] Setting up Python environment..."
cd ~/
if [ ! -d "sovereign-ai-workbench" ]; then
    echo "Clone or symlink your project to ~/sovereign-ai-workbench"
fi

echo -e "\n✅ Ubuntu setup complete!"
echo "Next steps:"
echo "  1. Clone or symlink your project"
echo "  2. Create venv: python3 -m venv .venv"
echo "  3. Install deps: pip install -r requirements.txt"
echo "  4. Run scripts/setup_ollama.sh"
