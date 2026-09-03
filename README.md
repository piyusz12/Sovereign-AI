# 🛡️ Sovereign AI Workbench

> Local-first, zero-egress AI system for enterprise document intelligence, code generation, and agentic workflows.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)]()
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

---

## Architecture

```
SOVEREIGN AI WORKBENCH
│
┌─────────────┴─────────────┐
│         WEB UI / API       │
└─────────────┬─────────────┘
              │
         FastAPI
              │
       TASK CLASSIFIER
              │
        MODEL ROUTER
              │
   ┌──────────┼──────────┐
   ▼          ▼          ▼
REASONING   CODING    VISION
Qwen3-14B  Coder-7B  Qwen3-VL-8B
 4-bit      4-bit      4-bit
   │          │          │
   └──────────┼──────────┘
              │
       LANGGRAPH AGENT
              │
   ┌──────────┼──────────┐
   ▼          ▼          ▼
  RAG      SANDBOX     FILES
Qdrant     Docker    DOCX/XLSX/PPTX
   │          │          │
   └──────────┼──────────┘
              ▼
          VERIFIER
              │
              ▼
           OUTPUT
              │
   ┌──────────┴──────────┐
   ▼                     ▼
AUDIT LOG            SECURITY
OpenTelemetry    Zero-Egress Monitor
```

## Hardware Requirements

| Component | Specification | Role |
|-----------|--------------|------|
| GPU | RTX 4060 Laptop 8GB VRAM | LLM inference, vision, embeddings |
| CPU | Ryzen 7 7840HS | FastAPI, LangGraph, OCR, Docling, file processing |
| RAM | 16GB (32GB recommended) | Services, model offload, Qdrant |
| OS | Windows 11 → WSL2 → Ubuntu → Docker | Linux AI stack on Windows |

**Critical Rule**: ONE heavy model active on GPU at a time.

## Model Stack

| Function | Model | Quantization | Priority |
|----------|-------|-------------|----------|
| Reasoning | Qwen3-14B | 4-bit | Essential |
| Coding | Qwen2.5-Coder-7B | 4-bit | Essential |
| Vision | Qwen3-VL-8B | 4-bit | Essential |
| OCR | PaddleOCR | — | Essential |
| Document Parser | Docling | — | Essential |
| Embedding | Qwen3-Embedding-0.6B | — | Essential |
| Reranker | Qwen3-Reranker-0.6B | — | Important |
| Vector DB | Qdrant | — | Essential |
| Agent | LangGraph | — | Essential |
| Gateway | LiteLLM | — | Essential |
| Sandbox | Docker | — | Essential |

## Project Structure

```
sovereign-ai-workbench/
├── backend/
│   ├── api/          # FastAPI application
│   ├── agent/        # LangGraph agent
│   ├── router/       # Model router + task classifier + Ollama client
│   ├── rag/          # RAG pipeline
│   ├── tools/        # Agent tools
│   ├── security/     # Auth, RBAC, policy
│   ├── documents/    # Document processing
│   └── generators/   # DOCX/XLSX/PPTX generation
├── configs/          # YAML configurations
├── docker/           # Docker compose + Dockerfiles
├── scripts/          # Setup, benchmark, and verification scripts
├── tests/            # Test suite
├── monitoring/       # Sovereignty monitor
├── data/             # Documents, embeddings, output
└── frontend/         # React/Next.js UI (later)
```

## Quickstart

### 1. Prerequisites (Windows)
```powershell
# Enable WSL2
wsl --install
wsl --set-default-version 2
# Install Docker Desktop with WSL2 backend + GPU support
```

### 2. Setup (WSL2 Ubuntu)
```bash
cd ~/sovereign-ai-workbench
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run Backend
```bash
python start.py
```

### 4. Verify Phase 4 (Ollama Integration)
```bash
python scripts/verify_phase4.py
```

## Phase Roadmap

| Phase | Goal | Status |
|-------|------|--------|
| 0 | Architecture / Repository | ✅ |
| 1 | WSL2 + Ubuntu | ✅ |
| 2 | NVIDIA + CUDA + Docker GPU | ✅ |
| 3 | Python Backend | ✅ |
| 4 | Qwen3-14B via Ollama & Router | ✅ |
| 5 | Local Model API | ⬜ |
| 6 | Task Router | ⬜ |
| 7 | Coder Model | ⬜ |
| 8 | Vision Model | ⬜ |
| 9 | Tool Framework | ⬜ |
| 10 | Docker Sandbox | ⬜ |
| 11 | LangGraph Agent | ⬜ |
| 12-13 | Docling + PaddleOCR | ⬜ |
| 14-16 | Qdrant + Embeddings + Reranker | ⬜ |
| 17 | Hybrid RAG | ⬜ |
| 18 | RBAC | ⬜ |
| 19 | Adaptive RAG | ⬜ |
| 20 | DOCX/XLSX/PPTX Generation | ⬜ |
| 21-23 | SIH Demo Workflows | ⬜ |
| 24-26 | LiteLLM + vLLM + Infinity | ⬜ |
| 27-29 | Audit + Security + Zero-Egress | ⬜ |
| 30 | Frontend | ⬜ |
| 31-32 | Optimization + SIH Demo | ⬜ |

## Key Principles

1. **Zero Egress** — No data leaves the local machine. Ever.
2. **Single GPU Discipline** — One heavy model loaded at a time on 8GB VRAM.
3. **Fail-Closed RAG** — Refuse to answer when evidence is insufficient.
4. **Pre-Retrieval RBAC** — Filter documents before retrieval, not after.
5. **Sandboxed Execution** — All generated code runs in isolated Docker containers.
6. **Verifiable Sovereignty** — Network monitoring proves no external calls.

---

*Built for Smart India Hackathon — Demonstrating sovereign AI on consumer hardware.*
