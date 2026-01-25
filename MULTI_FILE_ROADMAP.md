# Multi-File Support Roadmap

**Status:** Planning Phase  
**Priority:** High (production SaaS requirement)  
**Target:** Q1 2026 (post-MSR camera-ready)

---

## Problem Statement

SKYT currently operates on single-file Python programs. Production use cases require:
- Multi-file projects (modules, packages)
- Import resolution across files
- Cross-file canonicalization
- Dependency management

---

## Technical Challenges

### 1. Contract Specification
**Current:** Single function with oracle tests  
**Needed:** Multi-file contract specification

**Challenges:**
- How to specify entry points?
- How to define file structure requirements?
- How to test multi-file behavior?

### 2. Canonicalization Scope
**Current:** Single AST normalization  
**Needed:** Cross-file canonicalization strategy

**Challenges:**
- Which files to canonicalize together?
- How to handle import dependencies?
- How to measure cross-file structural similarity?

### 3. Import Resolution
**Current:** No import handling  
**Needed:** Resolve imports, track dependencies

**Challenges:**
- Relative vs absolute imports
- External dependencies (stdlib, third-party)
- Circular dependencies

### 4. Repeatability Metrics
**Current:** Single-file distance metrics  
**Needed:** Multi-file repeatability measurement

**Challenges:**
- Aggregate distances across files?
- Weight files differently (entry point vs helper)?
- How to handle file count variance?

---

## Proposed Architecture

### Phase 1: Multi-File Contracts (Weeks 1-2)

**Goal:** Extend contract system to specify multi-file projects.

**Contract Schema Extension:**
```json
{
  "contract_id": "web_scraper",
  "type": "multi_file",
  "entry_point": "main.py",
  "required_files": [
    "main.py",
    "scraper.py",
    "parser.py",
    "utils.py"
  ],
  "file_contracts": {
    "main.py": {
      "must_contain": ["def main()", "if __name__ == '__main__'"],
      "imports": ["scraper", "parser"]
    },
    "scraper.py": {
      "must_contain": ["def fetch_page(url)"],
      "imports": ["requests", "utils"]
    }
  },
  "oracle": {
    "test_file": "test_web_scraper.py",
    "test_command": "pytest test_web_scraper.py"
  }
}
```

**Implementation:**
- Extend `Contract` class to support multi-file specs
- Add file structure validation
- Update oracle system to run multi-file tests

**Files to modify:**
- `src/contract.py`
- `src/oracle_system.py`
- `contracts/templates.json`

---

### Phase 2: Import Graph Analysis (Weeks 3-4)

**Goal:** Build dependency graph for import resolution.

**Components:**

1. **Import Parser**
   ```python
   class ImportGraph:
       def __init__(self, project_files: Dict[str, str]):
           self.files = project_files
           self.graph = self._build_graph()
       
       def _build_graph(self) -> nx.DiGraph:
           """Build directed graph of imports"""
           pass
       
       def get_dependencies(self, filename: str) -> List[str]:
           """Get all files that filename depends on"""
           pass
       
       def get_dependents(self, filename: str) -> List[str]:
           """Get all files that depend on filename"""
           pass
       
       def topological_order(self) -> List[str]:
           """Get files in dependency order"""
           pass
   ```

2. **Import Resolution**
   ```python
   class ImportResolver:
       def resolve_import(self, import_stmt: str, current_file: str) -> str:
           """Resolve import to actual file path"""
           pass
       
       def is_external(self, import_stmt: str) -> bool:
           """Check if import is external (stdlib/third-party)"""
           pass
   ```

**Implementation:**
- Use `ast` module to extract imports
- Use `networkx` for dependency graph
- Handle relative imports (`.`, `..`)
- Detect circular dependencies

**New files:**
- `src/import_graph.py`
- `src/import_resolver.py`
- `tests/test_import_graph.py`

---

### Phase 3: Multi-File Canonicalization (Weeks 5-6)

**Goal:** Extend canonicalization to work across files.

**Strategy Options:**

#### Option A: File-by-File (Simple)
- Canonicalize each file independently
- Aggregate distances across files
- **Pros:** Reuses existing code
- **Cons:** Ignores cross-file patterns

#### Option B: Project-Level (Complex)
- Treat entire project as single unit
- Build combined AST representation
- **Pros:** Captures cross-file patterns
- **Cons:** High complexity, unclear metrics

#### Option C: Dependency-Aware (Recommended)
- Canonicalize in topological order
- Use dependency graph to guide transformations
- **Pros:** Respects file relationships
- **Cons:** Medium complexity

**Recommended: Option C**

**Implementation:**
```python
class MultiFileCanonicalizer:
    def __init__(self, import_graph: ImportGraph):
        self.graph = import_graph
        self.single_file_canon = CodeTransformer()
    
    def canonicalize_project(self, files: Dict[str, str], 
                            anchor_files: Dict[str, str]) -> Dict[str, str]:
        """
        Canonicalize multi-file project
        
        Args:
            files: {filename: code} for current project
            anchor_files: {filename: code} for anchor project
            
        Returns:
            {filename: canonicalized_code}
        """
        # Get topological order
        order = self.graph.topological_order()
        
        canonicalized = {}
        for filename in order:
            # Canonicalize with awareness of dependencies
            canonicalized[filename] = self._canonicalize_file(
                filename, 
                files[filename],
                anchor_files[filename],
                canonicalized  # Already processed dependencies
            )
        
        return canonicalized
    
    def _canonicalize_file(self, filename: str, code: str, 
                          anchor_code: str, 
                          processed_deps: Dict[str, str]) -> str:
        """Canonicalize single file with dependency context"""
        # Use existing single-file canonicalizer
        # But consider import statements from processed dependencies
        pass
```

**New files:**
- `src/multi_file_canonicalizer.py`
- `tests/test_multi_file_canonicalizer.py`

---

### Phase 4: Multi-File Metrics (Weeks 7-8)

**Goal:** Define repeatability metrics for multi-file projects.

**Proposed Metrics:**

#### 1. Per-File Repeatability
```python
R_file[i] = repeatability of file i
```

#### 2. Weighted Project Repeatability
```python
R_project = Σ(w_i × R_file[i])

where w_i = importance weight of file i
```

**Weight Options:**
- **Uniform:** All files equal weight
- **LOC-based:** Weight by lines of code
- **Dependency-based:** Weight by number of dependents
- **Entry-point-based:** Higher weight for entry points

#### 3. Import Stability
```python
I_stability = proportion of runs with same import structure
```

**Implementation:**
```python
class MultiFileMetrics:
    def calculate_project_repeatability(
        self, 
        runs: List[Dict[str, str]],  # List of {filename: code} dicts
        weighting: str = "dependency"
    ) -> Dict[str, Any]:
        """
        Calculate multi-file repeatability
        
        Returns:
            {
                "r_project": float,
                "r_per_file": Dict[str, float],
                "import_stability": float,
                "file_count_variance": float
            }
        """
        pass
```

**New files:**
- `src/multi_file_metrics.py`
- `tests/test_multi_file_metrics.py`

---

### Phase 5: LLM Multi-File Generation (Weeks 9-10)

**Goal:** Prompt LLMs to generate multi-file projects.

**Challenges:**
- LLMs tend to generate single-file solutions
- Need explicit prompting for file structure
- File boundaries may vary across runs

**Prompt Strategy:**

```python
MULTI_FILE_PROMPT = """
Generate a Python project with the following structure:

Files required:
{file_list}

For each file, provide:
1. Complete, working code
2. Proper imports
3. Clear separation of concerns

Contract requirements:
{contract_requirements}

Output format:
```filename: main.py
[code for main.py]
```

```filename: utils.py
[code for utils.py]
```

Important: Generate ALL required files. Each file must be complete and runnable.
"""
```

**Implementation:**
- Extend `LLMClient` to parse multi-file responses
- Add file extraction logic
- Handle missing files (retry or fail)

**Files to modify:**
- `src/llm_client.py`
- `src/prompt_builder.py`

---

### Phase 6: Integration & Testing (Weeks 11-12)

**Goal:** Integrate all components and test end-to-end.

**Test Projects:**

1. **Simple:** Two-file calculator
   - `calculator.py` (main logic)
   - `operations.py` (helper functions)

2. **Medium:** Web scraper
   - `main.py` (entry point)
   - `scraper.py` (fetch logic)
   - `parser.py` (HTML parsing)
   - `utils.py` (helpers)

3. **Complex:** REST API
   - `app.py` (Flask app)
   - `routes.py` (endpoints)
   - `models.py` (data models)
   - `database.py` (DB connection)
   - `utils.py` (helpers)

**Validation:**
- Run 20 generations per project
- Measure R_project, R_per_file, I_stability
- Compare single-file vs multi-file repeatability
- Document findings

**New files:**
- `contracts/multi_file/calculator.json`
- `contracts/multi_file/web_scraper.json`
- `contracts/multi_file/rest_api.json`
- `experiments/multi_file_validation.py`

---

## API Design for Production SaaS

### Endpoint: Create Multi-File Job

```http
POST /api/v1/jobs/multi-file
Content-Type: application/json

{
  "contract": {
    "type": "multi_file",
    "entry_point": "main.py",
    "required_files": ["main.py", "utils.py"],
    "file_contracts": { ... },
    "oracle": { ... }
  },
  "model": "gpt-4",
  "temperature": 0.7,
  "num_runs": 20
}
```

**Response:**
```json
{
  "job_id": "mf_abc123",
  "status": "queued",
  "estimated_time": "15 minutes"
}
```

### Endpoint: Get Multi-File Results

```http
GET /api/v1/jobs/mf_abc123/results
```

**Response:**
```json
{
  "job_id": "mf_abc123",
  "status": "completed",
  "metrics": {
    "r_project": 0.72,
    "r_per_file": {
      "main.py": 0.68,
      "utils.py": 0.85
    },
    "import_stability": 0.95,
    "file_count_variance": 0.0
  },
  "runs": [
    {
      "run_id": 1,
      "files": {
        "main.py": "...",
        "utils.py": "..."
      },
      "passed_oracle": true
    }
  ]
}
```

---

## Database Schema Extensions

### New Tables

**`multi_file_jobs`:**
```sql
CREATE TABLE multi_file_jobs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES profiles(id),
    contract JSONB NOT NULL,
    model VARCHAR(100) NOT NULL,
    temperature FLOAT NOT NULL,
    num_runs INT NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**`multi_file_outputs`:**
```sql
CREATE TABLE multi_file_outputs (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES multi_file_jobs(id),
    run_number INT NOT NULL,
    files JSONB NOT NULL,  -- {filename: code}
    passed_oracle BOOLEAN NOT NULL,
    import_graph JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**`multi_file_metrics`:**
```sql
CREATE TABLE multi_file_metrics (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES multi_file_jobs(id),
    r_project FLOAT NOT NULL,
    r_per_file JSONB NOT NULL,  -- {filename: repeatability}
    import_stability FLOAT NOT NULL,
    file_count_variance FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Research Questions (Future Papers)

1. **How does repeatability scale with project size?**
   - Hypothesis: R_project decreases as file count increases
   - Experiment: Measure R for 1, 2, 5, 10 file projects

2. **Which files are most/least repeatable?**
   - Hypothesis: Entry points less repeatable than utilities
   - Experiment: Analyze R_per_file across file types

3. **Does import structure stabilize faster than code?**
   - Hypothesis: I_stability > R_project
   - Experiment: Compare import vs code repeatability

4. **Can cross-file canonicalization improve R_project?**
   - Hypothesis: Dependency-aware canonicalization > file-by-file
   - Experiment: Compare Option A vs Option C

---

## Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 1. Multi-File Contracts | 2 weeks | Extended contract schema |
| 2. Import Graph Analysis | 2 weeks | Dependency resolution |
| 3. Multi-File Canonicalization | 2 weeks | Cross-file transformer |
| 4. Multi-File Metrics | 2 weeks | R_project calculation |
| 5. LLM Multi-File Generation | 2 weeks | Multi-file prompting |
| 6. Integration & Testing | 2 weeks | End-to-end validation |
| **Total** | **12 weeks** | **Production-ready multi-file support** |

**Start Date:** February 2026 (post-MSR camera-ready)  
**Target Completion:** May 2026

---

## Dependencies

**Python Libraries:**
- `networkx` - Dependency graph analysis
- `ast` - Import extraction (already used)
- `pathlib` - File path handling (already used)

**Infrastructure:**
- Database schema migrations (Supabase)
- API endpoint updates (FastAPI)
- Worker task updates (Celery)

---

## Success Criteria

**Minimum Viable Product (MVP):**
- ✅ Support 2-5 file projects
- ✅ Resolve imports correctly
- ✅ Calculate R_project metric
- ✅ API endpoints functional
- ✅ 3 test contracts validated

**Full Production:**
- ✅ Support up to 20 files
- ✅ Handle circular dependencies
- ✅ Cross-file canonicalization working
- ✅ All metrics implemented
- ✅ 10+ multi-file contracts

---

## Risk Mitigation

**Risk 1: LLMs generate inconsistent file structures**
- Mitigation: Strict prompting, file structure validation, retry logic

**Risk 2: Cross-file canonicalization too complex**
- Mitigation: Start with Option A (file-by-file), upgrade to Option C later

**Risk 3: Import resolution edge cases**
- Mitigation: Focus on common patterns first, document limitations

**Risk 4: Performance degradation with many files**
- Mitigation: Optimize AST processing, add caching, limit file count

---

## Next Steps

1. **Immediate (Post-MSR):**
   - Review this roadmap with team
   - Prioritize phases based on user needs
   - Set up project tracking (GitHub issues)

2. **Week 1:**
   - Start Phase 1 (Multi-File Contracts)
   - Create first multi-file contract (calculator)
   - Update database schema

3. **Ongoing:**
   - Weekly progress reviews
   - User feedback integration
   - Documentation updates

---

## Questions for Discussion

1. Should we support arbitrary file counts or cap at N files?
2. How to handle external dependencies (requirements.txt)?
3. Should we support languages beyond Python initially?
4. What's the pricing model for multi-file jobs (more expensive)?
5. Do we need file-level canonicalization controls (per-file enable/disable)?

---

**Document Version:** 1.0  
**Last Updated:** January 13, 2026  
**Owner:** Heitor Roriz Filho  
**Status:** Draft - Awaiting Team Review
