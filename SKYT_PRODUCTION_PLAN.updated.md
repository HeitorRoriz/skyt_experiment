# SKYT Production SaaS Platform - Strategic Plan
**Target: skyt.works**

## 1. Executive Summary

SKYT today is a strong research-grade engine for evaluating software repeatability and behavioral contracts against LLMs and other systems. The goal of this plan is to turn SKYT into **Skyt (SKYT) – Software Repeatability as a Service**, a multi-tenant SaaS platform.

Core ideas:

- Provide a **repeatable, contract-based harness** for code, prompts, and systems.
- Make **reproducibility, metrics, and restrictions** first-class, versioned citizens.
- Expose a **simple API + playground UI** that orchestrates the existing SKYT engine.
- Keep the core engine clean, testable, and reusable by following **SOLID** and **clean architecture** principles.

This document describes the architecture, APIs, data model, performance strategy, and roadmap to reach a production-ready SaaS MVP in ~12 weeks.

---

## 2. Current State Analysis

### 2.1 Strengths

- ✅ Solid core design (contracts, canonicalization, metrics, transformations).
- ✅ Modular Python codebase with clear separation of concerns.
- ✅ Good test coverage and validation.
- ✅ Property-based thinking and metrics already baked in.
- ✅ CLI-based workflows work well for research and local experimentation.

### 2.2 Gaps for SaaS

- ❌ No multi-tenant authentication/authorization.
- ❌ No stable HTTP API or web UI for external users.
- ❌ No async job system, queuing, or quota model.
- ❌ No persistence of jobs, configs, metrics, or artifacts.
- ❌ No explicit story for performance, cost control, and observability at scale.
- ❌ Core not yet decoupled from concrete infra (Redis, DB, LLM providers).

The plan below closes these gaps while keeping the core engine clean and testable.

---

## 3. Product Vision & Principles

**Vision:** “SKYT is the reproducibility backbone for any AI or software system that cares about contracts, metrics, and long-term reliability.”

**Primary use cases:**

- LLM application teams validating behavior and regressions over time.
- Safety / compliance teams enforcing restriction sets over responses.
- Engineering teams measuring repeatability across versions, prompts, and providers.

**Guiding principles:**

- **SOLID + DIP**: High-level logic depends on abstractions, not frameworks or providers.
- **Reproducibility**: Every job is replayable via versioned configs.
- **Multi-tenancy & safety**: Strong isolation between tenants and safe defaults.
- **APIs first**: Everything the UI does goes through public APIs.
- **Observability**: Jobs and costs are traceable per user, per provider, per experiment.

---

## 4. Architecture Overview

### 4.1 Logical View

Three main tiers with cross-cutting concerns:

1. **Tier 1 – Core Engine (library)**  
   - Existing SKYT modules (contracts, canon, metrics, transformers, oracles).  
   - New `core/` layer with interfaces and orchestration (`Pipeline`).

2. **Tier 2 – API + Workers (backend services)**  
   - FastAPI HTTP API (REST + WebSockets/SSE).  
   - Celery/RQ workers executing pipeline jobs.  
   - Postgres for metadata, Redis for queues/cache, S3 (or similar) for artifacts.

3. **Tier 3 – Web App (frontend)**  
   - React + TypeScript + Tailwind + shadcn UI.  
   - Playground for contracts/restrictions, history dashboards, organization admin.

**Cross-cutting:** authentication, authorization, billing/quotas, logging, metrics, alerts.

---

## 5. Tier 1 – Core Engine (Keep & Extend)

**Principle: Minimal changes to existing core; extend via SOLID and explicit interfaces.**

### 5.1 Directory Structure

```text
src/
├── core/                          # NEW: Core abstractions and orchestration
│   ├── interfaces.py              # Core protocols/ports (LLM, repos, cache)
│   ├── pipeline.py                # Main SKYT pipeline orchestrator
│   ├── job_executor.py            # Async job execution wrapper
│   └── result_store.py            # Results persistence layer
│
├── contracts/                     # Existing + Extensions
│   ├── contract.py                # Keep as-is
│   ├── restriction_loader.py      # NEW: Load custom restrictions
│   ├── restriction_merger.py      # NEW: Pure merging logic
│   └── restriction_schema.py      # NEW: Restriction validation
│
├── canon_system.py                # Keep (optimize via Cache interface)
├── code_transformer.py            # Keep
├── metrics.py                     # Keep
├── oracle_system.py               # Keep
└── foundational_properties.py     # Keep
```

### 5.2 Core Interfaces & Dependency Inversion

Define small, focused interfaces so pipeline logic depends on abstractions, not concrete infra:

```python
# src/core/interfaces.py
from typing import Protocol, List
from uuid import UUID

class ContractRepository(Protocol):
    def get(self, user_id: UUID, contract_id: str) -> "Contract": ...

class RestrictionRepository(Protocol):
    def get_many(self, user_id: UUID, restriction_ids: list[UUID]) -> list["RestrictionSet"]: ...

class LlmClient(Protocol):
    async def generate(self, *, prompt: str, pins: "ModelPins") -> "LlmOutput": ...

class ResultStore(Protocol):
    def save_job_result(self, job_id: UUID, result: "JobResult") -> None: ...
    def get_job_result(self, job_id: UUID) -> "JobResult | None": ...

class Cache(Protocol):
    def get(self, key: str) -> bytes | None: ...
    def set(self, key: str, value: bytes, ttl_seconds: int | None = None) -> None: ...
    def invalidate(self, key: str) -> None: ...
```

### 5.3 Pipeline Orchestration

`Pipeline` uses these interfaces, keeping orchestration logic independent of FastAPI, Redis, Postgres, or specific LLM providers:

```python
# src/core/pipeline.py
from uuid import UUID
from .interfaces import ContractRepository, RestrictionRepository, LlmClient, ResultStore

class Pipeline:
    def __init__(
        self,
        contracts: ContractRepository,
        restrictions: RestrictionRepository,
        llm: LlmClient,
        results: ResultStore,
    ) -> None:
        self._contracts = contracts
        self._restrictions = restrictions
        self._llm = llm
        self._results = results

    async def run_job(self, job_id: UUID, user_id: UUID, spec: "JobSpec") -> "JobResult":
        """
        High-level orchestration only:
        - load contract + restrictions
        - build experiment config
        - fan out LLM calls
        - canonicalize + compute metrics
        - persist JobResult via ResultStore
        """
        ...
```

`JobExecutor` wraps pipeline calls and provides a clean interface for workers:

```python
# src/core/job_executor.py
class JobExecutor:
    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline

    async def execute(self, job_id: UUID, user_id: UUID, spec: "JobSpec") -> "JobResult":
        return await self.pipeline.run_job(job_id, user_id, spec)
```

### 5.4 Experiment & Result Models

Define clear domain objects to support reproducibility:

```python
# src/core/models.py
from dataclasses import dataclass
from uuid import UUID
from typing import List, Dict, Any

@dataclass
class ExperimentConfig:
    contract_id: str
    contract_version: str
    restriction_ids: list[UUID]
    restriction_versions: list[str]
    pins: "ModelPins"  # model, temp, seed, decoding, etc.

@dataclass
class RunResult:
    run_index: int
    raw_output: str
    canonical_output: str
    metrics: Dict[str, Any]

@dataclass
class JobResult:
    job_id: UUID
    config: ExperimentConfig
    runs: List[RunResult]
    metrics_summary: Dict[str, Any]
```

This keeps the core engine domain-rich and independent from persistence details.

---

## 6. Restriction System

Restrictions are a key differentiator: they let users define behavioral and structural constraints (e.g., NASA Power of 10 rules, internal safety policies).

### 6.1 Concepts

- **RestrictionSet:** Versioned collection of rules defined by a user or provided as presets.
- **RestrictionLoader:** IO + validation layer that fetches and validates restriction sets.
- **RestrictionMerger:** Pure function combining contract and restrictions into a single, enriched contract.
- **Detectors/Evaluators:** Pluggable components that apply restriction rules to outputs or ASTs.

### 6.2 Loader & Merger

```python
# src/contracts/restriction_loader.py
from pathlib import Path
from uuid import UUID

class RestrictionLoader:
    def load_from_file(self, restriction_file: Path) -> "RestrictionSet":
        """Load and validate restriction set from JSON/YAML"""

    def load_by_id(self, user_id: UUID, restriction_id: UUID) -> "RestrictionSet":
        """Load and validate a stored restriction set from the DB"""
```

```python
# src/contracts/restriction_merger.py
class RestrictionMerger:
    def merge(
        self,
        contract: "Contract",
        restrictions: list["RestrictionSet"],
    ) -> "Contract":
        """
        Pure function: combine base contract with one or more restriction sets
        and return a new, enriched Contract instance.
        """
```

Loader = IO + validation; Merger = pure combination logic used by the pipeline.

### 6.3 Versioning

- Each `RestrictionSet` has `(id, version, source)` where `source ∈ {user, preset}`.
- Jobs store both `restriction_ids` and `restriction_versions` so experiments are fully replayable.
- Preset libraries (e.g., `nasa_power_of_ten`, `misra_c`) are versioned and treated as read-only templates.

### 6.4 Future: Sandbox & Safe Execution

- Dynamic restriction logic (e.g., user Python snippets) runs in a sandboxed process/container.
- Fail-closed behavior: if a restriction evaluator fails, the system reports an internal error rather than silently ignoring rules.

---

## 7. Tier 2 – API, Workers, and Infrastructure

### 7.1 Backend Stack

- **FastAPI** for HTTP/JSON APIs, WebSockets and/or Server-Sent Events.
- **Celery or RQ** workers for async job execution.
- **Postgres** for metadata and metrics summaries (hot data).
- **Redis** for queues and caching (via the `Cache` interface).
- **S3-compatible object storage** for large artifacts (cold data).

### 7.2 API Design

All endpoints are versioned under `/api/v1`.

#### Authentication & Authorization

- JWT-based auth, integrated with a minimal user system.
- Later: organization support, roles (admin, member), and API keys per project.

#### Core Endpoints (MVP)

- `POST /api/v1/pipeline/run`  
  Submit a new job:
  - `contract_id`, `num_runs`, `temperature`, `model`, `restriction_ids`, etc.
  - Optional `client_job_id` for idempotency.
  - Returns `{ job_id, status }`.

- `GET /api/v1/jobs/{job_id}`  
  Returns job metadata + current status.

- `GET /api/v1/jobs/{job_id}/results`  
  Returns metrics summary and optional link to artifacts.

- `GET /api/v1/contracts` / `GET /api/v1/restrictions`  
  List available contracts and restriction sets (including presets).

- `POST /api/v1/restrictions`  
  Upload a new restriction set (JSON/YAML) with validation.

- `GET /api/v1/jobs/stream/{job_id}` (WebSocket or SSE)  
  Stream updates on job progress and partial results.

#### Rate Limiting & Quotas

- Enforce per-user rate limits and concurrency limits using Redis.
- Subscription tiers:
  - **Free**: small number of runs/day, limited parallelism.
  - **Pro**: higher limits, more parallelism, maybe longer retention.
  - **Enterprise**: customizable limits, SLAs, and dedicated queues.

### 7.3 Job Lifecycle & Idempotency

**Lifecycle:**

- `queued` → `running` → `completed`
- `queued`/`running` → `failed` (unrecoverable error)
- `queued`/`running` → `cancelled` (future feature)
- `queued` → `expired` (TTL exceeded before processing)

`jobs` table includes a `retry_count` to track worker retries and support backoff.

**Idempotent job creation:**

- `POST /api/v1/pipeline/run` accepts an optional `"client_job_id"`.
- Server behavior:
  - If `(user_id, client_job_id)` is new → create job, return `202` + `job_id`.
  - If `(user_id, client_job_id)` already exists → return existing job (`200`) instead of creating a duplicate.
- Avoids duplicate jobs caused by client retries or network glitches.

**Multi-tenant safety:**

- Every query into `jobs`, `restriction_sets`, etc., is filtered by `user_id` in repositories.
- Repository methods require `user_id` explicitly (no “get by id only” in multi-tenant code paths).
- Public/preset data lives in a separate, read-only namespace.

---

## 8. Tier 3 – Frontend (Web App)

### 8.1 Stack

- **React + TypeScript**
- **Vite** for bundling and dev.
- **TailwindCSS** for styling.
- **shadcn/ui** for common components (cards, modals, tables).
- **TanStack Query (React Query)** for data fetching and caching.

### 8.2 Structure

```text
web/
├── src/
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Playground.tsx
│   │   ├── Jobs.tsx
│   │   └── Settings.tsx
│   ├── components/
│   │   ├── JobTable.tsx
│   │   ├── ContractSelector.tsx
│   │   ├── RestrictionEditor.tsx
│   │   └── MetricsChart.tsx
│   ├── hooks/
│   │   ├── useJobs.ts
│   │   ├── useContracts.ts
│   │   └── useRestrictions.ts
│   └── services/
│       └── api.ts            # Fetch wrapper around /api/v1
```

### 8.3 Key Screens

- **Playground**
  - Choose contract, model, and restriction sets.
  - Configure runs, temperature, seeds.
  - See metrics summaries and canonical outputs.
- **Jobs / History**
  - List jobs with status, filters, and pagination.
  - Drill into a specific job for metrics and artifacts.
- **Restrictions**
  - List presets and user-defined restriction sets.
  - Upload / edit restriction JSON/YAML with validation feedback.
- **Settings / Account**
  - API keys, subscription tier, and usage summary.

Front-end talks only to public APIs; no direct DB or worker knowledge in the UI.

---

## 9. Data Model & Database Schema

### 9.1 Principles

- **Hot data** (jobs, metrics summaries, configs) live in Postgres.
- **Cold data** (full outputs, logs, traces) live in object storage.
- Everything important for reproducibility is versioned and snapshotted.

### 9.2 Schema

```sql
-- Users and subscriptions
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Custom restriction sets (versioned)
CREATE TABLE restriction_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) NOT NULL DEFAULT '1.0',
    source VARCHAR(50) NOT NULL DEFAULT 'user', -- 'user' | 'preset'
    rules JSONB NOT NULL,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Pipeline jobs (multi-tenant, idempotent, versioned)
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    client_job_id VARCHAR(255), -- optional, for idempotency
    contract_id VARCHAR(255) NOT NULL,
    contract_version VARCHAR(50) NOT NULL DEFAULT '1.0',

    num_runs INT NOT NULL,
    temperature FLOAT NOT NULL,

    restriction_ids UUID[] DEFAULT '{}',
    restriction_versions VARCHAR(50)[] DEFAULT '{}',

    config JSONB NOT NULL, -- full ExperimentConfig (pins, seeds, etc.)

    status VARCHAR(50) NOT NULL DEFAULT 'queued', -- queued|running|completed|failed|cancelled|expired
    retry_count INT NOT NULL DEFAULT 0,
    error_message TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE UNIQUE INDEX idx_jobs_user_client_job
    ON jobs(user_id, client_job_id)
    WHERE client_job_id IS NOT NULL;

CREATE INDEX idx_jobs_user_created
    ON jobs(user_id, created_at DESC);

CREATE INDEX idx_jobs_status_created
    ON jobs(status, created_at);

-- Job results (hot metrics + pointer to cold artifacts)
CREATE TABLE job_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,

    metrics JSONB NOT NULL,         -- R_raw, R_anchor, etc.
    config_snapshot JSONB NOT NULL, -- ExperimentConfig persisted at run time
    artifacts_url TEXT,             -- optional S3/object-storage URL

    created_at TIMESTAMP DEFAULT NOW()
);

-- Quotas (simple per-user limits)
CREATE TABLE quotas (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    daily_run_limit INT NOT NULL DEFAULT 100,
    monthly_run_limit INT NOT NULL DEFAULT 3000,
    current_day_count INT NOT NULL DEFAULT 0,
    current_month_count INT NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 10. Performance Optimization

### 10.1 Current Bottlenecks

- LLM API calls are often sequential and slow.
- AST parsing and canonicalization can be repeated unnecessarily.
- Canonical comparison is in-memory only, with no caching.
- No centralized job queue or backpressure strategy.
- No separation between hot and cold data in storage.

### 10.2 Optimizations

**a) Async LLM Calls**

```python
# src/core/job_executor.py
import asyncio

class AsyncPipelineExecutor:
    def __init__(self, llm_client: "LlmClient"):
        self.llm_client = llm_client

    async def run_parallel(self, contract, num_runs: int, pins: "ModelPins"):
        """Run N LLM calls in parallel via injected LlmClient"""
        tasks = [
            self.llm_client.generate(prompt=contract.prompt, pins=pins)
            for _ in range(num_runs)
        ]
        return await asyncio.gather(*tasks)
```

**b) Caching Strategy**

- **Redis via Cache interface:** Cache canonical anchors and property computations keyed by `(contract_id, contract_version, restriction_ids, pins)`.
- **Database:** Store contract templates and restriction sets once; share across jobs.
- **CDN:** Serve static frontend assets and documentation via a CDN edge.

**c) Lazy Computation**

- Only compute metrics requested by the caller (e.g., a “summary only” flag for MVP).
- Heavy analyses (e.g., per-run histograms or bell curves) are optional and can be run asynchronously.

**d) Database Indexing**

```sql
CREATE INDEX idx_jobs_user_created
    ON jobs(user_id, created_at DESC);

CREATE INDEX idx_jobs_status_created
    ON jobs(status, created_at);

CREATE INDEX idx_job_results_job_id
    ON job_results(job_id);
```

**e) Background Jobs & Backpressure**

- Use **Celery** or **RQ** for long-running tasks (pipeline jobs).
- Use queue priorities or rate-limiting tokens per tenant to avoid noisy-neighbor issues.
- Handle provider 429s via exponential backoff + jitter in workers.

**f) Storage Strategy (Hot vs Cold)**

- Keep **hot data** (job metadata, metrics summaries, configuration snapshots) in Postgres.
- Store **cold artifacts** (full outputs, debug traces, logs) in S3/object storage, referenced by `artifacts_url`.
- This keeps the DB lean and improves query performance at scale.

**g) Observability**

- Use correlation IDs: propagate `job_id` across logs and traces.
- Capture metrics per tenant, per provider, and per contract.
- Set up alerts on queue backlog, worker failures, and provider error rates.

---

## 11. Security, Multi-tenancy & Compliance

- **Auth**: JWT-based, HTTPS everywhere.
- **Multi-tenancy**: All DB queries scoped by `user_id` (and later `org_id`).
- **RBAC** (later): per-organization roles for admin, maintainer, viewer.
- **Data isolation**: No cross-tenant references in jobs or results; presets live in a global, read-only namespace.
- **Secrets management**: LLM API keys and other secrets stored in a secret manager or encrypted at rest.
- **Auditability**: Store who ran what jobs, when, with which configurations.

---

## 12. Roadmap (High-Level)

**Phase 1 – Foundation (Weeks 1–3)**  
- Extract `core/` layer and interfaces (`LlmClient`, `ResultStore`, `ContractRepository`, `RestrictionRepository`, `Cache`).  
- Implement `Pipeline`, `JobExecutor`, and `ExperimentConfig` / `JobResult` domain models.  
- Add basic Redis cache implementation and Postgres repositories.

**Phase 2 – API & Workers (Weeks 4–6)**  
- Implement FastAPI HTTP endpoints and authentication.  
- Set up Celery/RQ workers and queues.  
- Implement job lifecycle (queued → running → completed/failed) and idempotent creation.  
- Persist configs, results, and minimal metrics.

**Phase 3 – Frontend Playground (Weeks 7–9)**  
- Build minimal React playground for contracts/restrictions.  
- Implement basic history, job details, and streaming progress.  
- Add preset restriction libraries.

**Phase 4 – Performance & Observability (Weeks 8–10, overlapping)**  
- Add caching and async fan-out for LLM calls.  
- Add metrics, logging, and dashboards.  
- Implement backpressure and rate limits.

**Phase 5 – Beta Hardening (Weeks 10–12)**  
- Security review, quota tuning, and UX polish.  
- Add basic billing hooks or align tiers with manual invoicing.  
- Onboard first design partners / early adopters.

---

## 13. Next Steps

1. Review this plan and finalize any architectural decisions (Celery vs RQ, exact provider abstractions).  
2. Start Phase 1 by extracting `core/` interfaces and `Pipeline`.  
3. Define a tiny, end-to-end “walking skeleton”:
   - One contract,
   - One preset restriction set,
   - One API endpoint,
   - One worker,
   - One minimal UI path to run and see metrics.
4. Iterate fast with early users and refine contracts/restrictions UX.

---

**Document Version:** 2.0  
**Date:** 2025-11-19  
**Author:** SKYT Team  
**Status:** Draft for Implementation
