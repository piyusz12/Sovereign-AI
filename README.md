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
   RAG + Qdrant | Docker sandbox
            |
        local files and outputs
```

The default local services are Ollama for model inference and Qdrant for vector search. LiteLLM, vLLM, and Infinity endpoints are supported through configuration when those services are available.

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
docker compose -f docker/docker-compose.yml up -d ollama qdrant
```

Pull the models configured by the application. The defaults are:

```bash
ollama pull qwen3:14b
ollama pull qwen2.5-coder:7b
ollama pull llama3.2-vision:latest
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

### Docker-only backend

To run the backend and its local dependencies together:

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Configuration

Settings are loaded from environment variables and an optional `.env` file. Defaults are defined in [`backend/settings.py`](backend/settings.py). Common overrides include:

```dotenv
APP_HOST=127.0.0.1
APP_PORT=8080
DEBUG=true
LOG_LEVEL=INFO
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_REASONING_MODEL=qwen3:14b
OLLAMA_CODING_MODEL=qwen2.5-coder:7b
OLLAMA_VISION_MODEL=llama3.2-vision:latest
QDRANT_HOST=localhost
QDRANT_PORT=6333
JWT_SECRET_KEY=replace-this-in-development
SANDBOX_NETWORK=none
```

Do not commit production secrets. In particular, replace the development JWT secret before exposing the API beyond a local machine.

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
- `data/output/` - generated deliverables
- `data/audit/` - audit log files

Back up or clear these directories according to your retention policy. Do not place confidential data in the repository history.

## License

This project is proprietary. Refer to the project owner for licensing and distribution terms.

