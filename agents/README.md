# Agentic SKYT

Autonomous agents for ensuring LLM-generated code adheres to contracts.

## Overview

This branch explores using AI agents to autonomously handle contract compliance, going beyond the rule-based transformations in the main SKYT system. Agents can:

- **Analyze** code for contract violations
- **Plan** transformation strategies
- **Execute** repairs autonomously
- **Learn** from successful transformations
- **Collaborate** with other specialized agents

## Architecture

```
Contract Adherence Agent
├── Tools
│   ├── analyze_code_structure
│   ├── run_oracle_tests
│   ├── calculate_canonical_distance
│   └── transform_to_canonical
├── Planning Engine
├── Memory System
└── Learning Module
```

## Key Differences from Main SKYT

| Main SKYT | Agentic SKYT |
|-----------|-------------|
| Rule-based transformations | Autonomous planning |
| Fixed repair strategies | Adaptive strategies |
| No learning capability | Learns from experience |
| Single-agent system | Multi-agent collaboration |
| Deterministic workflow | Dynamic decision-making |

## Installation

```bash
# Install agent dependencies
pip install -r agents/requirements.txt

# Set up API keys
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
```

## Quick Start

```python
import asyncio
from agents.contract_agent import ContractAdherenceAgent

async def main():
    # Initialize agent
    agent = ContractAdherenceAgent(model="gpt-4o")
    
    # Check compliance
    code = """
    def fibonacci(n):
        if n < 0:
            raise ValueError("n must be non-negative")
        elif n == 0:
            return 0
        elif n == 1:
            return 1
        else:
            return fibonacci(n-1) + fibonacci(n-2)
    """
    
    result = await agent.ensure_compliance(code, "fibonacci_basic")
    
    print(f"Compliant: {result.compliant}")
    print(f"Violations: {len(result.violations)}")
    
    if result.transformed_code:
        print("Transformed code available!")

asyncio.run(main())
```

## Testing

```bash
cd agents
python test_agent.py
```

## Agent Capabilities

### 1. Violation Detection
- Multiple exit points
- Naming convention violations
- Missing bounds checking
- Behavioral mismatches
- Structural violations
- Complexity violations

### 2. Autonomous Planning
The agent analyzes violations and creates a transformation strategy:

```
ANALYZE → PLAN → EXECUTE → VALIDATE → LEARN
```

### 3. Tool Usage
Agents can dynamically select and combine tools:
- Code structure analysis
- Oracle test execution
- Canonical distance calculation
- Code transformation

### 4. Memory & Learning
- Track successful transformation patterns
- Learn from failed attempts
- Adapt strategies based on contract type

## Future Roadmap

### Phase 1: Single Agent (Current)
- Basic compliance checking
- Simple transformations
- Tool integration

### Phase 2: Enhanced Agent
- Strategic planning
- Memory system
- Learning capabilities

### Phase 3: Multi-Agent System
- Specialized agents (Analyzer, Transformer, Validator)
- Agent collaboration
- Conflict resolution

### Phase 4: Production Integration
- Google ADK integration
- Scalability features
- Enterprise deployment

## Research Questions

1. **Planning vs. Rules**: Can autonomous planning outperform rule-based transformations?
2. **Learning Impact**: How much do agents improve with experience?
3. **Multi-Agent Benefits**: Does specialization improve overall compliance?
4. **Production Readiness**: Can agents handle safety-critical contract enforcement?

## Comparison with Existing Work

| System | Approach | Strengths | Limitations |
|--------|----------|-----------|-------------|
| Main SKYT | Rule-based | Deterministic, predictable | Limited flexibility |
| Agentic SKYT | AI planning | Adaptive, learns | Less predictable |
| Traditional Tools | Static analysis | Fast, reliable | No repair capability |
| Human Review | Manual expertise | High quality | Slow, expensive |

## Papers & Publications

This research could lead to papers on:

1. **"Autonomous Contract Adherence Agents for AI-Generated Code"** - Main contribution
2. **"Comparing Rule-Based vs. Agent-Based Code Transformation"** - Empirical study
3. **"Multi-Agent Systems for Safety-Critical Code Compliance"** - Advanced concepts

## Contributing

This is experimental research code. Key areas for contribution:

- Enhanced tool implementations
- New agent architectures
- Benchmark datasets
- Evaluation methodologies

## License

Same as main SKYT project (MIT for code, CC-BY-4.0 for data).

---

**Note**: This is experimental research building on the main SKYT system. For the published MSR 2026 paper, see the `main` branch.
