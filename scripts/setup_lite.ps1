# ============================================
# Sovereign AI Workbench — 8GB Lite Profile Setup
# ============================================
# PowerShell setup for RTX 4060 Laptop (8GB VRAM)
# Pulls Ollama models, installs Python deps, starts LiteLLM gateway

$ErrorActionPreference = "Stop"

Write-Host "`n🛡️  Sovereign AI Workbench — 8GB Lite Profile Setup" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# ── Step 1: Check Ollama ──────────────────────────────────────────────────────
Write-Host "`n[1/5] Checking Ollama installation..." -ForegroundColor Yellow

try {
    $ollamaVersion = ollama --version 2>&1
    Write-Host "  ✓ Ollama found: $ollamaVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Ollama not found. Please install from https://ollama.com/download" -ForegroundColor Red
    Write-Host "  After installing, restart this script." -ForegroundColor Red
    exit 1
}

# ── Step 2: Pull models ──────────────────────────────────────────────────────
Write-Host "`n[2/5] Pulling 8GB Lite models..." -ForegroundColor Yellow

Write-Host "  Pulling Qwen2.5-Coder-7B (primary reasoning + coding, ~4.7GB VRAM)..."
ollama pull qwen2.5-coder:7b

Write-Host "  Pulling Qwen2-VL-2B (vision parser, ~1.5GB VRAM)..."
ollama pull qwen2-vl:2b

Write-Host "  ✓ Models pulled successfully" -ForegroundColor Green

# ── Step 3: Verify Python venv ────────────────────────────────────────────────
Write-Host "`n[3/5] Checking Python environment..." -ForegroundColor Yellow

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "  ✓ Virtual environment found at .venv\" -ForegroundColor Green
    .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "  Creating virtual environment..."
    py -3.11 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
}

# ── Step 4: Install dependencies ──────────────────────────────────────────────
Write-Host "`n[4/5] Installing Python dependencies..." -ForegroundColor Yellow

pip install -r requirements.txt
Write-Host "  ✓ Dependencies installed" -ForegroundColor Green

# ── Step 5: Verify setup ─────────────────────────────────────────────────────
Write-Host "`n[5/5] Verifying setup..." -ForegroundColor Yellow

# Check Ollama models
Write-Host "`n  Available Ollama models:"
ollama list

# Quick import check
python -c "import lancedb; print('  ✓ LanceDB:', lancedb.__version__)" 2>&1
python -c "from sentence_transformers import SentenceTransformer; print('  ✓ sentence-transformers loaded')" 2>&1

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host "`n=================================================" -ForegroundColor Cyan
Write-Host "✅ 8GB Lite Profile setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "VRAM Budget:" -ForegroundColor White
Write-Host "  Qwen2.5-Coder-7B (Q4_K_M):  ~4.7 GB" -ForegroundColor Gray
Write-Host "  KV Cache (8K context):       ~1.5 GB" -ForegroundColor Gray
Write-Host "  OS / Display:                ~1.0 GB" -ForegroundColor Gray
Write-Host "  Embeddings (CPU):              0 GB" -ForegroundColor Gray
Write-Host "  LanceDB (CPU/RAM):             0 GB" -ForegroundColor Gray
Write-Host "  ────────────────────────────────────" -ForegroundColor Gray
Write-Host "  Total:                       ~7.2 GB ✓" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Start the backend:   python start.py" -ForegroundColor Gray
Write-Host "  2. Start LiteLLM:       litellm --config configs/litellm_config.yaml --port 4000" -ForegroundColor Gray
Write-Host "  3. Start the frontend:  cd frontend && npm run dev" -ForegroundColor Gray
Write-Host "  4. Open browser:        http://127.0.0.1:3000" -ForegroundColor Gray
Write-Host ""
