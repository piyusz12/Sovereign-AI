#!/bin/bash
# ============================================
# Sovereign AI Workbench — Ollama Setup
# ============================================
# Run inside WSL2 Ubuntu

set -e

echo "🛡️  Sovereign AI Workbench — Ollama Setup"

# Install Ollama
echo -e "\n[1/4] Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# Verify
echo -e "\n[2/4] Verifying Ollama..."
ollama --version

# Start Ollama service
echo -e "\n[3/4] Starting Ollama..."
ollama serve &
sleep 5

# Pull models (one at a time to manage VRAM)
echo -e "\n[4/4] Pulling models..."

echo "Pulling Qwen3-14B (reasoning)..."
ollama pull qwen3:14b

echo "Pulling Qwen2.5-Coder-7B (coding)..."
ollama pull qwen2.5-coder:7b

echo "Pulling Qwen3-VL-8B (vision)..."
# ollama pull qwen3-vl:8b  # Uncomment when ready

echo -e "\n✅ Ollama setup complete!"
echo ""
echo "Available models:"
ollama list

echo ""
echo "Quick test:"
echo "  ollama run qwen3:14b 'Explain what a P&ID is.'"
echo ""
echo "Benchmark:"
echo "  Record: VRAM usage, RAM usage, tokens/sec, first-token latency"
