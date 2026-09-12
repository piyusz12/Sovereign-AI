# Sovereign AI Workbench

Local-first AI infrastructure for enterprise document intelligence, code generation, multimodal analysis, and agentic workflows. The workbench keeps inference and data processing on local services, applies RBAC before retrieval, records an audit trail, and exposes a FastAPI API with a React frontend.

## Capabilities

- Task classification and model routing for reasoning, coding, and vision requests
- Chat and streaming chat through the REST API
- Document upload, parsing, OCR, semantic search, embeddings, and reranking
- Pre-retrieval RBAC so restricted documents are excluded before they reach the model
- Sandboxed code execution with configurable CPU, memory, timeout, and network limits
- DOCX, XLSX, PPTX, and code-package generation
- LangGraph agents, workflow orchestration, and self-repair loops
- JWT authentication, policy enforcement, audit events, and sovereignty monitoring
- OpenAI-compatible endpoints under `/v1`

## Architecture

```text
React + Vite frontend
            |
        FastAPI API
            |
   auth / RBAC / audit / policy
            |
   task classifier + model router
       /          |          \
  reasoning    coding       vision
       \          |          /
        agents + workflow registry
            |
   RAG + LanceDB | Docker sandbox
            |
        local files and outputs
```

The default local services are Ollama for model inference and LanceDB for vector search. Embeddings run on CPU via `sentence-transformers` to save VRAM. LiteLLM, vLLM, and Infinity endpoints are supported through configuration when those services are available. Qdrant can be used instead of LanceDB by setting `VECTOR_DB_BACKEND=qdrant`.

## Requirements

- Python 3.11 or newer
- Node.js 20 or newer and npm
- Docker Desktop with the WSL2 backend on Windows
- NVIDIA GPU and compatible Docker GPU support for local model inference
- 16 GB RAM minimum; 32 GB is recommended
- Approximately 8 GB of VRAM for the default single-model workflow

The system is designed around a single heavy model active on the GPU at a time. Model downloads require network access during setup; runtime services can then be operated locally.

## Quick Start

### 1. Create the Python environment

PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Linux or WSL2:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Start local dependencies

From the repository root:

```bash
docker compose -f docker/docker-compose.yml up -d ollama
```

Pull the models configured by the application. The defaults are:

```bash
ollama pull qwen2.5-coder:7b
ollama pull qwen2-vl:2b
```

### 3. Start the backend

```bash
python start.py
```

The API listens on `http://127.0.0.1:8080` by default. Interactive API documentation is available at `/docs`; the ReDoc view is available at `/redoc`.

### 4. Start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 3000
```

Open `http://127.0.0.1:3000`. The backend CORS configuration currently allows the local frontend on port `3000`.

### 5. (Optional) Start the LiteLLM gateway

LiteLLM provides an OpenAI-compatible API gateway so your agent orchestration code doesn't need to know it's running locally:

```bash
pip install litellm
litellm --config configs/litellm_config.yaml --port 4000
```

Your local models are now accessible at `http://localhost:4000` just like a cloud API.

### Docker-only backend

To run the backend and its local dependencies together:

```bash
docker compose -f docker/docker-compose.yml up --build
```

### Windows one-liner setup

For new setups on Windows, run the Lite Profile setup script:

```powershell
.\scripts\setup_lite.ps1
```

## Configuration

Settings are loaded from environment variables and an optional `.env` file. Defaults are defined in [`backend/settings.py`](backend/settings.py). Common overrides include:

```dotenv
APP_HOST=127.0.0.1
APP_PORT=8080
DEBUG=true
LOG_LEVEL=INFO
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_REASONING_MODEL=qwen2.5-coder:7b
OLLAMA_CODING_MODEL=qwen2.5-coder:7b
OLLAMA_VISION_MODEL=qwen2-vl:2b
VECTOR_DB_BACKEND=lancedb
LANCEDB_PATH=./data/lancedb
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
EMBEDDING_DEVICE=cpu
JWT_SECRET_KEY=replace-this-in-development
SANDBOX_NETWORK=none
```

Do not commit production secrets. In particular, replace the development JWT secret before exposing the API beyond a local machine.

## 8 GB Lite Performance Profile

The default serving path is direct local Ollama (which uses llama.cpp), with one
heavy model active at once. It is tuned for interactive latency on an RTX 4060
Laptop instead of high concurrency.

### VRAM Budget

| Component | VRAM |
|---|---|
| OS / Display | ~1.0 – 1.5 GB |
| Qwen2.5-Coder-7B (Q4_K_M) | ~4.7 GB |
| KV Cache (8K context) | ~1.5 GB |
| Embeddings (CPU) | 0 GB |
| LanceDB (CPU/RAM) | 0 GB |
| **Total** | **~7.2 – 7.7 GB** ✓ |

### Model Stack

| Component | Model | Footprint |
|---|---|---|
| Reasoning + Coding | Qwen2.5-Coder-7B (Q4_K_M) | ~4.7 GB VRAM |
| Vision | Qwen2-VL-2B (Q4_K_M) | ~1.5 GB VRAM (loaded on demand) |
| Embeddings | all-MiniLM-L6-v2 | ~80 MB RAM (CPU) |
| Vector DB | LanceDB (embedded) | System RAM only |
| API Gateway | LiteLLM | Lightweight proxy |

### How it works

- Qwen2.5-Coder-7B serves as the primary brain for both reasoning and code tasks;
  switching between these categories does not require a model swap.
- Qwen2-VL-2B is loaded only when a vision task arrives, after the 7B model is
  unloaded — leaving ~5 GB of VRAM headroom.
- Prompts have a deterministic static prefix and a bounded dynamic suffix. The
  default 8,192-token window reserves 1,024 tokens for generation.
- If the KV cache exceeds available VRAM, Ollama (llama.cpp) seamlessly offloads
  the oldest tokens to system RAM. Generation slows but does not crash.
- Embeddings run entirely on CPU via `sentence-transformers`, using zero VRAM.
- LanceDB stores vectors on disk and searches in CPU/RAM — no server container
  needed.
- GPU work is serialized, with interactive inference ahead of background work.
- `/api/v1/models/metrics` reports local TTFT, ITL, token-rate, and scheduler
  queue telemetry without storing prompts or document text.

Tune the profile with `INFERENCE_CONTEXT_TOKENS`,
`INFERENCE_OUTPUT_RESERVE_TOKENS`, and `INFERENCE_KEEP_ALIVE`. Benchmark a
change before retaining it: `python scripts/benchmark_model.py --runs 3`.

## API Surface

| Area | Representative endpoints |
|---|---|
| Health and sovereignty | `GET /health`, `GET /sovereignty`, `GET /api/v1/sovereignty/status` |
| Authentication | `POST /api/v1/auth/login`, `GET /api/v1/auth/me` |
| Chat and routing | `POST /api/v1/chat`, `POST /api/v1/chat/stream`, `POST /api/v1/classify` |
| Coding and vision | `POST /api/v1/code/generate`, `POST /api/v1/vision/analyze`, `POST /api/v1/execute` |
| Documents and RAG | `POST /api/v1/upload`, `POST /api/v1/search` |
| Generation and workflows | `POST /api/v1/generate`, `POST /api/v1/workflows/run` |
| Models | `GET /api/v1/models`, `GET /api/v1/models/status`, `POST /api/v1/models/route` |
| Audit and monitoring | `GET /api/v1/audit/events`, `GET /api/v1/sovereignty/status` |
| OpenAI compatibility | `/v1` |

Endpoint schemas and live request examples are available in the Swagger UI at `http://127.0.0.1:8080/docs`.

## Security Model

- **Local-first execution:** model inference, document processing, and generated outputs use local services by default.
- **Pre-retrieval authorization:** RBAC filters are applied to vector searches before context is assembled for a model.
- **Sandboxed execution:** generated code runs with configurable resource limits and a disabled network by default.
- **Auditability:** requests and workflow activity are recorded through the audit middleware and audit API.
- **Sovereignty signals:** responses include sovereignty headers, and the sovereignty service tracks external network activity.

This is an actively developed workbench, not a turnkey production security boundary. Review secrets, container permissions, network policy, model provenance, and persistence before deployment in a regulated environment.

## Project Layout

```text
backend/
  api/             FastAPI application, schemas, routes, health checks
  agent/           LangGraph agent and reasoning loops
  coding_agent/    Repository-aware code generation and repair
  documents/       Ingestion, parsing, OCR, chunking, and metadata
  generators/      DOCX, XLSX, PPTX, and code-package generation
  model_gateway/   Local model gateway integrations
  models/          Model registry and loading
  rag/             Retrieval, embeddings, reranking, and context assembly
  router/          Task classification and model routing
  security/        Authentication, RBAC, policy, and enforcement
  sovereignty/     Network sovereignty monitoring
  tools/           Tool implementations and registries
  workflows/       End-to-end workflow orchestration
configs/           YAML model, policy, RBAC, and service configuration
data/              Documents, processed files, embeddings, outputs, and audit data
docker/            Compose file and backend/sandbox Dockerfiles
frontend/          React 19 + TypeScript + Vite application
monitoring/        Sovereignty and observability helpers
scripts/           Setup, benchmark, packaging, and verification utilities

```

## Testing and Quality Checks

Run the Python test suite from the repository root:

```bash
pytest
```

Useful focused checks include:

```bash
pytest tests/test_api.py tests/test_rbac.py tests/test_sovereignty.py
python test_rbac_endpoints.py
python test_generators.py
python test_sih_workflows.py
```

Validate the frontend with:

```bash
cd frontend
npm run lint
npm run build
```

## Data and Generated Files

Runtime data is stored under `data/` and is intentionally excluded from the application source layout:

- `data/documents/` - uploaded source documents
- `data/processed/` - parsed and chunked document data
- `data/embeddings/` - embedding artifacts
- `data/lancedb/` - LanceDB vector store (Lite profile)
- `data/output/` - generated deliverables
- `data/audit/` - audit log files

Back up or clear these directories according to your retention policy. Do not place confidential data in the repository history.

## License

This project is proprietary. Refer to the project owner for licensing and distribution terms.
