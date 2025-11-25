# SKYT: Software Repeatability as a Service

> **Same prompt, different code** is the default for LLMs; **SKYT** makes **same prompt, same code** a measurable, enforceable pipeline property.

**Domain:** skyt.works  
**Target Market:** Embedded/firmware engineers at aerospace & defense companies (EMBRAER, BOEING, etc.)  
**Status:** MVP Development

---

## Table of Contents

1. [Overview](#1-overview)
2. [Business Model](#2-business-model)
3. [Architecture](#3-architecture)
4. [Core Engine](#4-core-engine)
5. [API Reference](#5-api-reference)
6. [Contracts & Restrictions](#6-contracts--restrictions)
7. [Metrics](#7-metrics)
8. [Quick Start](#8-quick-start)
9. [Development](#9-development)

---

## 1. Overview

### What is SKYT?

SKYT is a **contract-based middleware** that transforms stochastic LLM code generation into an auditable, quality-controlled process suitable for:

- CI/CD pipelines
- Compliance contexts (DO-178C, MISRA, NASA Power of 10)
- Production deployment in safety-critical systems

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Versioned Contracts** | Schema-bound prompts with acceptance oracles |
| **Canonical Anchoring** | Immutable reference fixed at first compliant output |
| **Monotonic Repair** | AST-level transformations that preserve correctness |
| **Comprehensive Metrics** | R_raw, R_anchor, Δ_rescue, R_behavioral, R_structural |
| **Certification Presets** | NASA Power of 10, MISRA-C, DO-178C |

### Key Results

Across 250 generations (5 contracts × 5 temperatures × 10 runs):
- **Anchored repeatability gains**: 0.00 to 0.48 (Δ_rescue)
- **Behavioral correctness maintained**: R_behavioral = 1.00 throughout
- **Monotonicity validated**: All repairs satisfy d_post ≤ d_pre

---

## 2. Business Model

### Open Source + SaaS

SKYT follows the **Open Core** model:

| Component | License | Access |
|-----------|---------|--------|
| Core Engine | Apache 2.0 / MIT | Open Source |
| Contracts Repository | CC-BY-4.0 | Open Source |
| SaaS Platform | Proprietary | Paid |
| Enterprise Features | Proprietary | Paid |

### Why This Works

- **Academic Publication** requires open source core (MSR 2026)
- **Trust & Adoption** from auditable code
- **Enterprise Sales** from managed infrastructure + compliance features

### Pricing Tiers

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | CLI tool, community support |
| **Developer** | $29/mo | 1000 runs/mo, basic presets |
| **Team** | $99/mo | 10K runs, collaboration, custom restrictions |
| **Enterprise** | Custom | Unlimited, SSO, audit logs, SLA |

### What Customers Pay For

| Free (Open Source) | Paid (SaaS) |
|--------------------|-------------|
| Core engine | Hosted infrastructure |
| CLI tool | Web UI & collaboration |
| Contract schema | Pre-built certification presets |
| Metrics calculation | Historical dashboards |
| Local execution | Multi-tenant isolation |
| | SLAs & support |
| | Audit logs & compliance reports |
| | Enterprise SSO (SAML, OIDC) |

---

## 3. Architecture

### Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TIER 3: Web App                              │
│                     React + TypeScript + Tailwind                   │
│                              │                                      │
│                              │ HTTP/WebSocket                       │
│                              ▼                                      │
├─────────────────────────────────────────────────────────────────────┤
│                        TIER 2: API + Workers                        │
│                                                                     │
│   FastAPI ────► Pipeline ◄──── Celery Worker                       │
│                    │                                                │
│         ┌─────────┴─────────┐                                      │
│         ▼                   ▼                                       │
│   LlmClient(Protocol)  ResultStore(Protocol)                       │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                        TIER 1: Core Engine                          │
│                                                                     │
│   Pipeline, JobExecutor, Metrics, Canon, Transformers              │
│   (Pure business logic - NO infrastructure dependencies)            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React + TypeScript + Tailwind + Lucide |
| API | FastAPI + Pydantic |
| Queue | Redis + Celery |
| Database | PostgreSQL |
| Cache | Redis |
| Storage | S3-compatible |

### Repository Structure

```
skyt_experiment/
├── src/                      # Core engine
│   ├── core/                 # Interfaces & models
│   │   ├── interfaces.py     # Protocol definitions
│   │   ├── models.py         # Domain dataclasses
│   │   ├── progress.py       # Job progress tracking
│   │   └── observable_llm.py # LLM wrapper with observability
│   ├── llm_client.py         # LLM provider implementations
│   ├── canon_system.py       # Canonical anchoring
│   ├── oracle_system.py      # Behavioral testing
│   ├── code_transformer.py   # AST transformations
│   └── metrics.py            # Repeatability metrics
│
├── api/                      # FastAPI application
│   ├── main.py               # App factory
│   ├── config.py             # Settings
│   └── routes/               # API endpoints
│       ├── auth.py           # JWT authentication
│       ├── pipeline.py       # Job submission
│       ├── jobs.py           # Job management
│       └── contracts.py      # Contracts & restrictions
│
├── workers/                  # Celery workers
│   ├── celery_app.py         # Celery configuration
│   └── tasks.py              # Background tasks
│
├── web/                      # React frontend
│   └── src/
│       ├── App.tsx           # Main component
│       └── services/api.ts   # API client
│
├── skyt-contracts/           # Contracts repository
│   ├── schema/               # JSON schemas
│   ├── contracts/            # Code generation contracts
│   └── restrictions/         # Certification standards
│       └── presets/
│           └── nasa_power_of_10.json
│
└── contracts/                # Legacy contracts
    └── templates.json
```

---

## 4. Core Engine

### Core Interfaces (Dependency Inversion)

The core engine depends on **abstractions, not concretions**:

```python
from src.core import LlmClient, ContractRepository, ResultStore, Cache

class LlmClient(Protocol):
    async def generate(self, prompt: str, pins: ModelPins) -> LlmOutput: ...

class ContractRepository(Protocol):
    def get(self, user_id: UUID, contract_id: str) -> Contract: ...

class ResultStore(Protocol):
    def save(self, job_id: UUID, result: JobResult) -> None: ...
    def get(self, job_id: UUID) -> JobResult | None: ...

class Cache(Protocol):
    def get(self, key: str) -> bytes | None: ...
    def set(self, key: str, value: bytes, ttl: int = None) -> None: ...
```

### Adapters by Context

| Context | LLM | Storage | Cache |
|---------|-----|---------|-------|
| Production | OpenAI/Anthropic | PostgreSQL | Redis |
| CLI | OpenAI | File system | In-memory |
| Tests | Mock | In-memory | In-memory |

### Observable LLM Client

Every LLM call is wrapped with observability:

```python
from src.core import ObservableLLMClient, LLMCallMetrics

client = ObservableLLMClient(
    base_client=openai_provider,
    on_call_start=lambda i: reporter.update_llm_call(i, "in_progress"),
    on_call_end=lambda i, m: reporter.update_llm_call(i, m.status,
        duration_ms=m.duration_ms,
        tokens_used=m.tokens_total),
)
```

### Job Progress Tracking

```python
from src.core import JobPhase, JobProgress, LLMCallStatus

class JobPhase(Enum):
    QUEUED = "queued"
    LOADING_CONTRACT = "loading_contract"
    GENERATING_OUTPUTS = "generating_outputs"
    CANONICALIZING = "canonicalizing"
    COMPUTING_METRICS = "computing_metrics"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

---

## 5. API Reference

### Authentication

```bash
# Get token
curl -X POST http://localhost:8000/api/v1/auth/token \
  -d "username=demo@skyt.works&password=demo123"

# Use token
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/...
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/auth/token` | Get JWT token |
| `POST` | `/api/v1/auth/register` | Register user |
| `GET` | `/api/v1/auth/me` | Current user info |
| `POST` | `/api/v1/pipeline/run` | Submit job |
| `GET` | `/api/v1/pipeline/jobs` | List jobs |
| `GET` | `/api/v1/jobs/{id}` | Get job details |
| `GET` | `/api/v1/jobs/{id}/results` | Get job results |
| `POST` | `/api/v1/jobs/{id}/cancel` | Cancel job |
| `WS` | `/api/v1/jobs/{id}/stream` | Real-time progress |
| `GET` | `/api/v1/contracts` | List contracts |
| `GET` | `/api/v1/contracts/{id}` | Get contract |
| `GET` | `/api/v1/restrictions/presets` | List presets |

### Submit Job

```bash
curl -X POST http://localhost:8000/api/v1/pipeline/run \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "contract_id": "fibonacci_basic",
    "num_runs": 10,
    "temperature": 0.3,
    "model": "gpt-4o-mini"
  }'
```

Response:
```json
{
  "job_id": "abc123...",
  "status": "queued",
  "estimated_duration_seconds": 30
}
```

---

## 6. Contracts & Restrictions

### Contract Schema

```json
{
  "id": "fibonacci_basic",
  "version": "1.0.0",
  "task_intent": "Generate nth Fibonacci number using iteration",
  "prompt": "Write a Python function called 'fibonacci'...",
  "constraints": {
    "function_name": "fibonacci",
    "implementation_style": "iterative",
    "variable_naming": {
      "fixed_variables": ["n"],
      "naming_policy": "strict"
    }
  },
  "oracle_requirements": {
    "test_cases": [
      {"input": 0, "expected": 0},
      {"input": 10, "expected": 55}
    ]
  }
}
```

### Available Contracts

| Contract | Algorithm | Key Properties |
|----------|-----------|----------------|
| `fibonacci_basic` | Iterative Fibonacci | Numerical sequences |
| `binary_search` | Binary search | Boundary conditions |
| `slugify` | URL slugification | String transformation |
| `balanced_brackets` | Bracket validation | Stack discipline |
| `gcd` | Euclidean GCD | Loop invariants |
| `lru_cache` | LRU Cache | State management |

### NASA Power of 10 Rules

| Rule | Name | Severity |
|------|------|----------|
| P10-R1 | Simple Control Flow | Mandatory |
| P10-R2 | Fixed Loop Bounds | Mandatory |
| P10-R3 | No Dynamic Memory After Init | Mandatory |
| P10-R4 | Short Functions (≤60 lines) | Required |
| P10-R5 | Assertion Density (≥2/function) | Required |
| P10-R6 | Minimal Variable Scope | Required |
| P10-R7 | Check Return Values | Mandatory |
| P10-R8 | Limited Preprocessor Use | Mandatory |
| P10-R9 | Limited Pointer Use | Mandatory |
| P10-R10 | Compile with All Warnings | Mandatory |

---

## 7. Metrics

### Core Repeatability Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **R_raw** | Mode(outputs) / total | Byte-identical before processing |
| **R_anchor_pre** | Σ(d=0) / total | Match canon before repair |
| **R_anchor_post** | Σ(d=0 after repair) / total | Match canon after repair |
| **Δ_rescue** | R_post - R_pre | Improvement from repair |
| **R_behavioral** | Σ(oracle_pass) / total | Pass oracle tests |
| **R_structural** | Σ(structure_match) / total | Structural compliance |

### Distributional Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **Δμ** | E[d_pre] - E[d_post] | Mean distance reduction |
| **ΔP_τ** | Pr[d_post ≤ τ] - Pr[d_pre ≤ τ] | Probability mass shift |

### Expected Results

| Contract | R_raw | R_anchor_pre | R_anchor_post | Δ_rescue |
|----------|-------|--------------|---------------|----------|
| Balanced Brackets | 0.38 | 0.44 | 0.92 | **0.48** |
| Binary Search | 0.44 | 0.70 | 0.70 | 0.00 |
| Fibonacci | 0.62 | 0.98 | 1.00 | 0.02 |
| Euclid-GCD | 1.00 | 1.00 | 1.00 | 0.00 |
| Slugify | 0.72 | 0.68 | 0.84 | **0.16** |

---

## 8. Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Redis (for workers)
- OpenAI API key

### Installation

```bash
# Clone
git clone <repo>
cd skyt_experiment

# Python dependencies
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend dependencies
cd web && npm install && cd ..
```

### Run CLI Experiment

```bash
# Set API key
export OPENAI_API_KEY=your_key

# Run single experiment
python main.py --contract fibonacci_basic --runs 10 --temperature 0.3

# Temperature sweep
python main.py --contract fibonacci_basic --sweep --temperatures 0.0 0.3 0.5 0.7
```

### Run SaaS Stack

```bash
# Terminal 1: API server
uvicorn api.main:app --reload

# Terminal 2: Frontend
cd web && npm run dev

# Terminal 3: Celery worker (optional, for background jobs)
celery -A workers.celery_app worker --loglevel=info
```

### Demo Credentials

```
Email: demo@skyt.works
Password: demo123
```

---

## 9. Development

### Project Status

| Phase | Status | Description |
|-------|--------|-------------|
| Core Engine | ✅ Complete | Contracts, canon, metrics, transformers |
| Multi-LLM Support | ✅ Complete | OpenAI, Anthropic, OpenRouter |
| Core Interfaces | ✅ Complete | Protocol-based dependency inversion |
| Contracts Repo | ✅ Complete | Schema, contracts, NASA preset |
| API Server | ✅ Complete | FastAPI with auth, jobs, contracts |
| Workers | ✅ Complete | Celery tasks with progress reporting |
| Frontend | ✅ Complete | React playground UI |
| Database | 🔧 Pending | PostgreSQL integration |
| Production | 🔧 Pending | Deployment, monitoring |

### Next Steps

1. **Database Integration**: Connect API to PostgreSQL
2. **Real Job Execution**: Wire Celery to actual SKYT pipeline
3. **Production Deployment**: Docker, Kubernetes, monitoring
4. **Enterprise Features**: SSO, audit logs, team management

### File Counts

| Directory | Files | Description |
|-----------|-------|-------------|
| `src/` | ~25 | Core engine |
| `src/core/` | 5 | Interfaces layer |
| `api/` | 7 | FastAPI application |
| `workers/` | 3 | Celery workers |
| `web/src/` | 3 | React frontend |
| `skyt-contracts/` | 9 | Contracts repository |

---

## License

- **Core Engine**: Apache 2.0 / MIT (for academic publication)
- **Contracts**: CC-BY-4.0
- **SaaS Code**: Proprietary

---

## Contact

- **Website**: skyt.works (coming soon)
- **Paper**: MSR 2026 submission
- **Issues**: GitHub Issues

---

*Document Version: 3.0 | Last Updated: 2025-11-25*
