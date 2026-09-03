#!/bin/bash
# ============================================
# Sovereign AI Workbench — Start Services
# ============================================
# Start all services in correct order

set -e

echo "🛡️  Starting Sovereign AI Workbench..."

# 1. Start Qdrant
echo "[1/3] Starting Qdrant..."
docker run -d \
    --name sovereign-qdrant \
    -p 127.0.0.1:6333:6333 \
    -p 127.0.0.1:6334:6334 \
    qdrant/qdrant \
    2>/dev/null || echo "Qdrant already running"

# 2. Start Ollama (if not already running)
echo "[2/3] Checking Ollama..."
if ! pgrep -x "ollama" > /dev/null; then
    ollama serve &
    sleep 3
fi
echo "Ollama running at http://localhost:11434"

# 3. Start FastAPI backend
echo "[3/3] Starting backend..."
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true
uvicorn backend.api.main:app --host 127.0.0.1 --port 8080 --reload &

echo ""
echo "✅ All services started!"
echo ""
echo "Endpoints:"
echo "  API:    http://127.0.0.1:8080"
echo "  Docs:   http://127.0.0.1:8080/docs"
echo "  Qdrant: http://127.0.0.1:6333"
echo "  Ollama: http://127.0.0.1:11434"
echo ""
echo "Health check:"
echo "  curl http://127.0.0.1:8080/health"
