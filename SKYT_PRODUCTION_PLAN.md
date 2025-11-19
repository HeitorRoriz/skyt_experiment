# SKYT Production SaaS Platform - Strategic Plan
**Target: skyt.works**

## Executive Summary

Transform SKYT from research artifact to production SaaS platform enabling LLM code repeatability as a service. Users can subscribe, use via CLI/Web, upload custom coding restrictions (NASA, MISRA, etc.), with performance-critical architecture.

---

## Current State Analysis

### Strengths
- ✅ Solid core architecture (contracts, canonicalization, metrics, transformations)
- ✅ Modular design with clear separation of concerns
- ✅ Comprehensive test suite and validation
- ✅ Well-documented property system and metrics
- ✅ CLI already exists (`main.py`)

### Gaps for Production
- ❌ No API layer (HTTP/REST interface)
- ❌ No web frontend
- ❌ No async processing for long-running jobs
- ❌ No user management/authentication
- ❌ No custom restrictions upload mechanism
- ❌ No rate limiting or quota management
- ❌ Performance not optimized for scale

---

## Architecture Plan (3-Tier)

### Tier 1: Core Engine (Current - Keep & Extend)

**Principle: Minimal changes to existing core, extend via SOLID principles**

```
src/
├── core/                          # NEW: Core abstractions
│   ├── pipeline.py                # Main SKYT pipeline orchestrator
│   ├── job_executor.py            # Async job execution wrapper
│   └── result_store.py            # Results persistence layer
│
├── contracts/                     # Existing + Extensions
│   ├── contract.py                # Keep as-is
│   ├── restriction_loader.py      # NEW: Load custom restrictions
│   └── restriction_schema.py      # NEW: Restriction validation
│
├── canon_system.py                # Keep (optimize caching)
├── code_transformer.py            # Keep
├── metrics.py                     # Keep
├── oracle_system.py               # Keep
└── foundational_properties.py     # Keep
```

**Extension Strategy:**
- Create `core/pipeline.py` that orchestrates existing components
- Introduce `RestrictionLoader` to merge custom rules with contracts
- Add caching layer to `canon_system.py` (Redis integration)
- No breaking changes to existing modules

### Tier 2: API Layer (NEW)

```
api/
├── main.py                        # FastAPI app entry point
├── routes/
│   ├── pipeline.py                # POST /api/v1/pipeline/run
│   ├── contracts.py               # GET/POST /api/v1/contracts
│   ├── restrictions.py            # POST /api/v1/restrictions/upload
│   ├── jobs.py                    # GET /api/v1/jobs/{job_id}/status
│   └── health.py                  # GET /api/v1/health
│
├── models/
│   ├── requests.py                # Pydantic request models
│   ├── responses.py               # Pydantic response models
│   └── schemas.py                 # Database schemas
│
├── services/
│   ├── pipeline_service.py        # Business logic wrapper
│   ├── auth_service.py            # JWT authentication
│   └── quota_service.py           # Rate limiting & subscriptions
│
├── middleware/
│   ├── auth.py                    # Authentication middleware
│   ├── rate_limit.py              # Rate limiting
│   └── cors.py                    # CORS configuration
│
└── database/
    ├── models.py                  # SQLAlchemy ORM models
    ├── migrations/                # Alembic migrations
    └── repositories/              # Data access layer
```

### Tier 3: Web Frontend (NEW)

```
web/
├── src/
│   ├── pages/
│   │   ├── Home.tsx               # Landing page with demo
│   │   ├── Dashboard.tsx          # User dashboard
│   │   ├── Playground.tsx         # Interactive demo
│   │   └── Docs.tsx               # Documentation
│   │
│   ├── components/
│   │   ├── CodeEditor.tsx         # Monaco editor integration
│   │   ├── MetricsView.tsx        # Display R_raw, R_anchor, etc.
│   │   ├── PipelineRunner.tsx     # Run pipeline UI
│   │   └── RestrictionUploader.tsx # Upload custom restrictions
│   │
│   ├── hooks/
│   │   ├── usePipeline.ts         # Pipeline API integration
│   │   └── useWebSocket.ts        # Real-time job updates
│   │
│   └── services/
│       └── api.ts                 # API client
```

---

## Core Features

### 1. CLI Enhancement

**Current:** Basic CLI exists in `main.py`

**Enhancement:**
```bash
# Keep existing
skyt run --contract fibonacci_basic --runs 10 --temperature 0.3

# Add new
skyt init                                    # Initialize project
skyt contract create --from-template nasa   # Use preset restrictions
skyt contract validate mycontract.json      # Validate custom contract
skyt restrictions add misra-c.json          # Add restriction set
skyt pipeline run --async --webhook https://... # Async with webhook
skyt results export --format csv/json       # Export results
```

**Implementation:**
- Use `typer` for better CLI UX
- Add progress bars with `rich`
- Support config files (`.skytrc`)
- Enable piping

### 2. Web Demo/Playground

**Goal:** Showcase SKYT capabilities without sign-up

**Features:**
- Monaco editor with syntax highlighting
- Live execution on sample prompts
- Real-time metrics visualization
- Side-by-side diff viewer (canonical vs variants)
- Example gallery (fibonacci, slugify, etc.)

**Tech Stack:**
- Frontend: React + TypeScript + Vite
- Editor: Monaco Editor
- Charts: Recharts or D3.js
- Styling: Tailwind CSS + shadcn/ui

**Free Tier Limitations:**
- Max 5 runs per request
- Temperature locked to [0.0, 0.5]
- No custom restrictions
- Results expire in 24 hours

### 3. Custom Restrictions Upload

**User Flow:**
1. User uploads restriction file (JSON/YAML)
2. System validates against schema
3. Restriction rules merge with base contract
4. Pipeline applies combined constraints

**Restriction Schema:**
```json
{
  "restriction_set": {
    "id": "nasa_power_of_ten",
    "version": "1.0",
    "rules": [
      {
        "id": "no_recursion",
        "description": "Avoid recursion (NASA Rule #1)",
        "enforcement": "strict",
        "detector": {
          "type": "ast_pattern",
          "pattern": "FunctionDef[calls_self=true]"
        },
        "severity": "error"
      },
      {
        "id": "max_loop_bound",
        "description": "Loop bounds must be statically verifiable",
        "enforcement": "strict",
        "detector": {
          "type": "ast_pattern",
          "pattern": "While[condition_not_bounded=true]"
        },
        "severity": "error"
      }
    ]
  }
}
```

**Preset Libraries:**
- NASA Power of Ten
- MISRA C (adapted for Python)
- Google Python Style Guide constraints
- PEP 8 strict mode
- Embedded systems (no dynamic allocation, bounded loops)

**Implementation:**
```python
# src/contracts/restriction_loader.py
class RestrictionLoader:
    def load(self, restriction_file: Path) -> RestrictionSet:
        """Load and validate restriction set"""
        
    def merge_with_contract(self, 
                          contract: Contract, 
                          restrictions: RestrictionSet) -> Contract:
        """Merge restrictions into contract constraints"""
```

### 4. Performance Optimization

**Current Bottlenecks:**
- LLM API calls (sequential)
- AST parsing repeated multiple times
- Canonical comparison in-memory only
- No caching layer

**Optimizations:**

**a) Async LLM Calls**
```python
# src/core/job_executor.py
class AsyncPipelineExecutor:
    async def run_parallel(self, contract, num_runs, temperature):
        """Run N LLM calls in parallel"""
        tasks = [
            self.llm_client.generate_async(...) 
            for _ in range(num_runs)
        ]
        return await asyncio.gather(*tasks)
```

**b) Caching Strategy**
- **Redis:** Cache canonical anchors, property computations
- **Database:** Store contract templates, restriction sets
- **CDN:** Static assets, documentation

**c) Lazy Computation**
- Only compute metrics that are requested
- Don't compute bell curve analysis unless explicitly asked

**d) Database Indexing**
```sql
CREATE INDEX idx_experiments 
ON experiments(contract_id, temperature, created_at);
```

**e) Background Jobs**
- Use **Celery** or **RQ** for long-running tasks
- WebSocket for real-time progress updates

---

## API Design

### RESTful Endpoints

**Submit Pipeline Job**
```http
POST /api/v1/pipeline/run
Content-Type: application/json
Authorization: Bearer <token>

{
  "contract_id": "fibonacci_basic",
  "num_runs": 10,
  "temperature": 0.3,
  "restrictions": ["nasa_power_of_ten"],
  "webhook_url": "https://..."
}

Response 202:
{
  "job_id": "uuid-v4",
  "status": "queued",
  "estimated_completion": "2024-01-01T12:00:00Z"
}
```

**Get Job Status**
```http
GET /api/v1/pipeline/jobs/{job_id}
Authorization: Bearer <token>

Response 200:
{
  "job_id": "uuid-v4",
  "status": "completed",
  "progress": "10/10",
  "metrics": {
    "R_raw": 0.38,
    "R_anchor_pre": 0.44,
    "R_anchor_post": 0.92,
    "Delta_rescue": 0.48
  },
  "outputs": [...]
}
```

**WebSocket for Real-time Updates**
```
WS /api/v1/pipeline/jobs/{job_id}/stream

Events:
- run_started: {run_id: 1}
- run_completed: {run_id: 1, passed: true}
- job_completed: {metrics: {...}}
```

**Authentication**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "..."
}

Response 200:
{
  "access_token": "jwt-token",
  "refresh_token": "...",
  "expires_in": 3600
}
```

**Rate Limiting:**
- Free tier: 10 jobs/day, max 5 runs/job
- Pro tier: 100 jobs/day, max 50 runs/job
- Enterprise: Unlimited

---

## Database Schema

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

-- Custom restriction sets
CREATE TABLE restriction_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rules JSONB NOT NULL,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Pipeline jobs
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    contract_id VARCHAR(255) NOT NULL,
    num_runs INT NOT NULL,
    temperature FLOAT NOT NULL,
    restriction_ids UUID[] DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'queued',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_jobs_user ON jobs(user_id, created_at DESC);
CREATE INDEX idx_jobs_status ON jobs(status, created_at);

-- Job results
CREATE TABLE job_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    metrics JSONB NOT NULL,
    outputs JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Quotas
CREATE TABLE quotas (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    jobs_used_today INT DEFAULT 0,
    runs_used_today INT DEFAULT 0,
    reset_at TIMESTAMP DEFAULT NOW()
);
```

---

## Security & Compliance

1. **Authentication:** JWT with refresh tokens
2. **Code Sandboxing:** Execute generated code in Docker containers (gVisor)
3. **Input Validation:** Strict Pydantic models, max prompt length (10KB)
4. **Rate Limiting:** Per-user, per-IP (sliding window)
5. **Secrets Management:** AWS Secrets Manager / HashiCorp Vault
6. **Audit Logging:** Log all API calls, pipeline executions
7. **HTTPS Only:** Enforce TLS 1.3+
8. **SQL Injection Prevention:** Parameterized queries via SQLAlchemy

---

## Deployment Architecture

```
┌─────────────────┐
│   CloudFlare    │  CDN + DDoS protection
│   (skyt.works)  │
└────────┬────────┘
         │
┌────────▼────────┐
│  Load Balancer  │  AWS ALB / NGINX
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│ API   │ │ API   │  FastAPI (Auto-scaling)
│ Node1 │ │ Node2 │  Docker + ECS/K8s
└───┬───┘ └──┬────┘
    │        │
┌───▼────────▼───┐
│  Job Queue     │  Redis / RabbitMQ
└───┬────────────┘
    │
┌───▼───────┐
│  Workers  │  Celery workers (SKYT core)
│ (Auto)    │  Auto-scaling 1-10 instances
└───┬───────┘
    │
┌───▼───────┐
│ Database  │  PostgreSQL (RDS)
│           │  Multi-AZ, automated backups
└───────────┘
```

**Infrastructure:**
- **Cloud:** AWS (ALB, ECS, RDS, S3, CloudFront)
- **CDN:** CloudFlare
- **Monitoring:** Sentry + DataDog
- **CI/CD:** GitHub Actions
- **Container Registry:** AWS ECR

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Refactor core pipeline into `src/core/pipeline.py`
- [ ] Create `RestrictionLoader` system with schema validation
- [ ] Setup FastAPI project structure
- [ ] Implement basic auth (JWT) with refresh tokens
- [ ] Database schema + Alembic migrations
- [ ] Setup Redis for caching

### Phase 2: API (Weeks 3-4)
- [ ] Pipeline API endpoints (POST /run, GET /jobs/:id)
- [ ] Restriction upload endpoints with validation
- [ ] WebSocket support for real-time updates
- [ ] Rate limiting & quota system
- [ ] Contract CRUD endpoints
- [ ] Background job processing (Celery)

### Phase 3: CLI Enhancement (Week 5)
- [ ] Rewrite CLI with `typer`
- [ ] Add `skyt init`, `contract create`, `restrictions add`
- [ ] Progress bars with `rich`
- [ ] Config file support (`.skytrc`)
- [ ] Authentication integration with API

### Phase 4: Web Frontend (Weeks 6-8)
- [ ] Landing page + documentation
- [ ] Interactive playground (no auth required)
- [ ] User dashboard (auth required)
- [ ] Real-time job monitoring with WebSocket
- [ ] Metrics visualization (charts, diffs)
- [ ] Restriction uploader UI

### Phase 5: Performance (Weeks 9-10)
- [ ] Async LLM calls (parallel execution)
- [ ] Redis caching layer integration
- [ ] Database query optimization
- [ ] Load testing (100 concurrent jobs)
- [ ] Profiling & bottleneck elimination
- [ ] CDN integration for static assets

### Phase 6: Polish & Launch (Weeks 11-12)
- [ ] E2E testing suite
- [ ] Security audit & penetration testing
- [ ] Documentation (API docs, tutorials)
- [ ] Pricing page & Stripe integration
- [ ] Launch preparation (Product Hunt, HN)

---

## Monetization Strategy

| Tier | Price | Jobs/Day | Runs/Job | Restrictions | Support | SLA |
|------|-------|----------|----------|--------------|---------|-----|
| **Free** | $0 | 10 | 5 | Presets only | Community | None |
| **Pro** | $29/mo | 100 | 50 | Custom upload | Email | 99% |
| **Enterprise** | Custom | Unlimited | Unlimited | Custom + consulting | Dedicated | 99.9% |

**Additional Revenue:**
- Pay-per-use: $0.10 per job (no subscription)
- Custom restrictions as marketplace items
- Consulting services for enterprise integration

---

## Tech Stack

### Backend
- **API:** FastAPI (async, auto-docs, Pydantic)
- **Queue:** Redis + Celery
- **Database:** PostgreSQL + SQLAlchemy
- **Auth:** PyJWT + bcrypt
- **Caching:** Redis
- **Deployment:** Docker + AWS ECS / Kubernetes

### Frontend
- **Framework:** React + TypeScript + Vite
- **UI:** Tailwind CSS + shadcn/ui
- **State:** Zustand / TanStack Query
- **Editor:** Monaco Editor (VS Code engine)
- **Charts:** Recharts
- **WebSocket:** Socket.io-client

### Infrastructure
- **Cloud:** AWS (ALB, ECS, RDS, S3, CloudFront, ElastiCache)
- **CDN:** CloudFlare
- **Monitoring:** Sentry (errors) + DataDog (metrics)
- **CI/CD:** GitHub Actions
- **Secrets:** AWS Secrets Manager

---

## Success Metrics

**Performance:**
- < 500ms API response time (excluding LLM calls)
- < 5s average pipeline completion (5 runs @ temp 0.3)
- 100 concurrent jobs supported

**Uptime:**
- 99.9% SLA for Pro/Enterprise
- < 1 hour MTTR for critical issues

**User Growth:**
- 1000 signups in first month
- 5% free → pro conversion rate
- 50% month-over-month growth

**Quality:**
- < 1% error rate on pipeline executions
- > 95% user satisfaction (NPS)

---

## Critical Design Decisions

### 1. LLM Provider Strategy
**Options:**
- A) OpenAI only (simplest, current setup)
- B) Multi-provider (OpenAI, Anthropic, local models)
- C) User brings their own API key

**Recommendation:** Start with A, evolve to C for Pro/Enterprise

### 2. Open Source Strategy
**Options:**
- A) Fully open source (MIT), monetize hosted service
- B) Open core (free tier OSS, Pro/Enterprise proprietary)
- C) Fully proprietary

**Recommendation:** A - aligns with research background, builds trust

### 3. Restriction Library Strategy
**Options:**
- A) Curated presets only
- B) User-generated marketplace
- C) Hybrid (curated + community)

**Recommendation:** C - start with A, evolve to C

### 4. Code Execution Strategy
**Options:**
- A) Don't execute (only analyze AST)
- B) Execute in sandboxed Docker containers
- C) Use existing sandbox services (e.g., Judge0)

**Recommendation:** B for control, C for faster MVP

---

## Risk Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM API costs exceed revenue | High | Medium | Implement aggressive caching, quota limits |
| Security breach (code injection) | Critical | Low | Sandboxing, input validation, security audit |
| Poor UX adoption | High | Medium | Extensive user testing, iterate on playground |
| Scaling bottlenecks | Medium | Medium | Load testing early, auto-scaling from day 1 |
| Competition (OpenAI/Anthropic builds similar) | High | Low | Focus on niche (embedded, compliance), move fast |

---

## Open Questions for Validation

1. **Pricing:** Is $29/mo competitive for the value provided?
2. **Target Market:** Focus on embedded/safety-critical first, or broader?
3. **Enterprise Features:** On-premise deployment? SSO? Custom SLAs?
4. **Free Tier:** How generous to be without abuse?
5. **LLM Models:** Support GPT-3.5 for cheaper tier?
6. **Restrictions:** Should we certify certain restriction sets (e.g., "NASA-compliant")?

---

## Appendix: Key SOLID Principles Applied

**Single Responsibility:**
- Each module does one thing (pipeline orchestration, restriction loading, caching)

**Open/Closed:**
- Core SKYT modules unchanged, extended via composition

**Liskov Substitution:**
- `RestrictionLoader` can swap different restriction formats

**Interface Segregation:**
- API endpoints segregated by concern (pipeline, auth, restrictions)

**Dependency Inversion:**
- High-level pipeline doesn't depend on low-level LLM client details

---

## Next Steps

1. **Review this plan** with stakeholders/advisors
2. **Validate** market demand (interviews with 10 potential users)
3. **Prototype** Phase 1 (Foundation) in 2 weeks
4. **User test** playground with 20 beta users
5. **Iterate** based on feedback
6. **Launch** MVP in 12 weeks

---

**Document Version:** 1.0  
**Date:** 2025-11-19  
**Author:** SKYT Team  
**Status:** Draft for Review
