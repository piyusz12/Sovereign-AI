#!/bin/bash
# ============================================
# Sovereign AI Workbench — Ollama Setup
# ============================================
# 8GB Lite Profile — RTX 4060 Laptop (8GB VRAM)
# Run inside WSL2 Ubuntu

set -e

echo "🛡️  Sovereign AI Workbench — Ollama Setup (8GB Lite Profile)"

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

# Pull models (8GB Lite Profile — smaller models for 8GB VRAM)
echo -e "\n[4/4] Pulling models..."

echo "Pulling Qwen2.5-Coder-7B (primary reasoning + coding model, ~4.7GB)..."
ollama pull qwen2.5-coder:7b

echo "Pulling Qwen2-VL-2B (vision model, ~1.5GB)..."
ollama pull qwen2-vl:2b

echo -e "\n✅ Ollama setup complete!"
echo ""
echo "Available models:"
ollama list

echo ""
echo "VRAM Budget (8GB Lite Profile):"
echo "  Qwen2.5-Coder-7B (Q4_K_M):  ~4.7 GB"
echo "  Qwen2-VL-2B (Q4_K_M):       ~1.5 GB (loaded on demand)"
echo "  KV Cache (8K context):       ~1.5 GB"
echo "  OS / Display:                ~1.0 GB"
echo ""
echo "Quick test:"
echo "  ollama run qwen2.5-coder:7b 'Explain what a P&ID is.'"
echo ""
echo "Benchmark:"
echo "  python scripts/benchmark_model.py --runs 3"
