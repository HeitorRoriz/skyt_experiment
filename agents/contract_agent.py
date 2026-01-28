#!/usr/bin/env python3
"""
Agentic SKYT: Contract Adherence Agent
Autonomous agent for ensuring LLM-generated code adheres to contracts
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# LangChain imports
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage

# SKYT imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.contract import Contract
from src.oracle_system import OracleSystem
from src.code_transformer import CodeTransformer
from src.canon_system import CanonSystem
from src.foundational_properties import FoundationalProperties


class ViolationType(Enum):
    """Types of contract violations"""
    MULTIPLE_EXIT = "multiple_exit_points"
    NAMING_VIOLATION = "naming_violation"
    MISSING_BOUNDS_CHECK = "missing_bounds_check"
    BEHAVIORAL_MISMATCH = "behavioral_mismatch"
    STRUCTURAL_VIOLATION = "structural_violation"
    COMPLEXITY_VIOLATION = "complexity_violation"


@dataclass
class Violation:
    """Represents a contract violation"""
    type: ViolationType
    severity: str  # "low", "medium", "high", "critical"
    description: str
    location: Optional[str] = None
    suggested_fix: Optional[str] = None


@dataclass
class ComplianceResult:
    """Result of compliance check"""
    compliant: bool
    violations: List[Violation]
    metrics: Dict[str, Any]
    transformed_code: Optional[str] = None
    transformation_success: bool = False


class ContractAdherenceAgent:
    """
    Autonomous agent that ensures LLM-generated code adheres to contracts
    """
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.0):
        self.model = model
        self.temperature = temperature
        
        # Initialize SKYT components
        self.oracle_system = OracleSystem()
        self.canon_system = CanonSystem()
        self.properties_extractor = FoundationalProperties()
        
        # Initialize LLM
        if "gpt" in model:
            self.llm = ChatOpenAI(model=model, temperature=temperature)
        elif "claude" in model:
            self.llm = ChatAnthropic(model=model, temperature=temperature)
        else:
            raise ValueError(f"Unsupported model: {model}")
        
        # Setup tools
        self.tools = self._create_tools()
        
        # Create agent
        self.agent = self._create_agent()
        self.executor = AgentExecutor(
            agent=self.agent, 
            tools=self.tools, 
            verbose=True,
            handle_parsing_errors=True
        )
    
    def _create_tools(self) -> List:
        """Create tools for the agent"""
        
        @tool
        def analyze_code_structure(code: str) -> str:
            """Analyze code structure and identify potential violations"""
            try:
                properties = self.properties_extractor.extract_all_properties(code)
                
                analysis = []
                
                # Check for multiple exit points
                if properties.get("control_flow_signature", {}).get("exit_points", 1) > 1:
                    analysis.append("VIOLATION: Multiple exit points detected")
                
                # Check naming conventions
                if properties.get("normalized_ast_structure", {}).get("variable_naming", "inconsistent") != "consistent":
                    analysis.append("VIOLATION: Inconsistent variable naming")
                
                # Check complexity
                complexity = properties.get("complexity_class", "unknown")
                if complexity in ["high", "very_high"]:
                    analysis.append(f"VIOLATION: High complexity ({complexity})")
                
                return " | ".join(analysis) if analysis else "No structural violations detected"
                
            except Exception as e:
                return f"Error analyzing code: {str(e)}"
        
        @tool
        def run_oracle_tests(code: str, contract_id: str) -> str:
            """Run oracle tests to check behavioral compliance"""
            try:
                # Load contract
                contract = Contract(f"contracts/templates.json", contract_id)
                
                # Run oracle tests
                result = self.oracle_system.validate_code(code, contract.data)
                
                if result.passed:
                    return f"PASS: All oracle tests passed (pass rate: {result.pass_rate:.1%})"
                else:
                    return f"FAIL: Oracle tests failed (pass rate: {result.pass_rate:.1%}) - {result.error}"
                    
            except Exception as e:
                return f"Error running oracle tests: {str(e)}"
        
        @tool
        def calculate_canonical_distance(code: str, contract_id: str) -> str:
            """Calculate distance to canonical anchor"""
            try:
                # Load canon
                canon_data = self.canon_system.load_canon(contract_id)
                if not canon_data:
                    return f"No canonical anchor found for contract: {contract_id}"
                
                # Calculate distance
                canon_properties = canon_data.get("foundational_properties", {})
                code_properties = self.properties_extractor.extract_all_properties(code)
                distance = self.properties_extractor.calculate_distance(canon_properties, code_properties)
                
                return f"Canonical distance: {distance:.3f} (threshold: 0.1)"
                
            except Exception as e:
                return f"Error calculating distance: {str(e)}"
        
        @tool
        def transform_to_canonical(code: str, contract_id: str) -> str:
            """Transform code to match canonical form"""
            try:
                # Load contract
                contract = Contract(f"contracts/templates.json", contract_id)
                
                # Transform
                transformer = CodeTransformer(self.canon_system)
                result = transformer.transform_to_canon(code, contract_id, contract=contract.data)
                
                if result["success"]:
                    return f"TRANSFORM_SUCCESS: Code transformed successfully (final distance: {result['final_distance']:.3f})"
                else:
                    return f"TRANSFORM_FAILED: {result.get('error', 'Unknown error')}"
                    
            except Exception as e:
                return f"Error transforming code: {str(e)}"
        
        return [
            analyze_code_structure,
            run_oracle_tests,
            calculate_canonical_distance,
            transform_to_canonical
        ]
    
    def _create_agent(self):
        """Create the LangChain agent"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Contract Adherence Agent for SKYT (Prompt Contracts for Software Repeatability).

Your job is to ensure LLM-generated code adheres to contract specifications. You have access to tools that can:

1. analyze_code_structure: Check for structural violations (multiple exits, naming, complexity)
2. run_oracle_tests: Validate behavioral compliance against contract tests
3. calculate_canonical_distance: Measure distance to canonical anchor
4. transform_to_canonical: Transform code to match canonical form

WORKFLOW:
1. First analyze the code structure for violations
2. Run oracle tests to check behavioral compliance
3. Calculate canonical distance to see how close it is to the anchor
4. If needed, transform the code to make it compliant
5. Provide a final compliance assessment

Be thorough and systematic. If you find violations, explain them clearly and attempt to fix them."""),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        return create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
    
    async def ensure_compliance(self, code: str, contract_id: str) -> ComplianceResult:
        """
        Ensure code adheres to contract specifications
        
        Args:
            code: The code to check and potentially transform
            contract_id: ID of the contract to check against
            
        Returns:
            ComplianceResult with violations, metrics, and transformed code if applicable
        """
        
        # Prepare the prompt for the agent
        prompt = f"""
Please analyze and ensure compliance for the following code:

CONTRACT ID: {contract_id}
CODE:
```python
{code}
```

Please:
1. Analyze the code structure for violations
2. Run oracle tests to check behavioral compliance  
3. Calculate canonical distance
4. Transform the code if needed to make it compliant
5. Provide a final assessment of compliance status
"""
        
        try:
            # Execute agent
            result = await self.executor.ainvoke({"input": prompt})
            
            # Parse result to extract compliance information
            violations = self._parse_violations(result["output"])
            transformed_code = self._extract_transformed_code(result["output"])
            
            # Calculate final metrics
            metrics = await self._calculate_metrics(code, contract_id, transformed_code)
            
            # Determine compliance status
            compliant = len([v for v in violations if v.severity == "critical"]) == 0
            
            return ComplianceResult(
                compliant=compliant,
                violations=violations,
                metrics=metrics,
                transformed_code=transformed_code,
                transformation_success=transformed_code is not None
            )
            
        except Exception as e:
            # Fallback to basic analysis if agent fails
            return await self._fallback_analysis(code, contract_id, str(e))
    
    def _parse_violations(self, agent_output: str) -> List[Violation]:
        """Parse violations from agent output"""
        violations = []
        
        # Simple parsing - can be made more sophisticated
        if "VIOLATION:" in agent_output:
            lines = agent_output.split('\n')
            for line in lines:
                if "VIOLATION:" in line:
                    parts = line.split("VIOLATION:", 1)[1].strip()
                    violations.append(Violation(
                        type=ViolationType.STRUCTURAL_VIOLATION,
                        severity="medium",
                        description=parts
                    ))
        
        return violations
    
    def _extract_transformed_code(self, agent_output: str) -> Optional[str]:
        """Extract transformed code from agent output"""
        # Look for code blocks in the output
        if "```python" in agent_output:
            start = agent_output.find("```python") + 9
            end = agent_output.find("```", start)
            if end > start:
                return agent_output[start:end].strip()
        
        return None
    
    async def _calculate_metrics(self, original_code: str, contract_id: str, transformed_code: Optional[str]) -> Dict[str, Any]:
        """Calculate compliance metrics"""
        metrics = {}
        
        try:
            # Original code metrics
            original_properties = self.properties_extractor.extract_all_properties(original_code)
            metrics["original_complexity"] = original_properties.get("complexity_class", "unknown")
            
            # Transformed code metrics (if available)
            if transformed_code:
                transformed_properties = self.properties_extractor.extract_all_properties(transformed_code)
                metrics["transformed_complexity"] = transformed_properties.get("complexity_class", "unknown")
                
                # Distance to canon
                canon_data = self.canon_system.load_canon(contract_id)
                if canon_data:
                    canon_properties = canon_data.get("foundational_properties", {})
                    metrics["canon_distance"] = self.properties_extractor.calculate_distance(
                        canon_properties, transformed_properties
                    )
            
            # Oracle test results
            contract = Contract(f"contracts/templates.json", contract_id)
            oracle_result = self.oracle_system.validate_code(original_code, contract.data)
            metrics["oracle_pass_rate"] = oracle_result.pass_rate
            
        except Exception as e:
            metrics["error"] = str(e)
        
        return metrics
    
    async def _fallback_analysis(self, code: str, contract_id: str, error: str) -> ComplianceResult:
        """Fallback analysis if agent fails"""
        return ComplianceResult(
            compliant=False,
            violations=[Violation(
                type=ViolationType.BEHAVIORAL_MISMATCH,
                severity="critical",
                description=f"Agent analysis failed: {error}"
            )],
            metrics={"error": error},
            transformed_code=None,
            transformation_success=False
        )


# Example usage
async def main():
    """Test the contract adherence agent"""
    
    # Initialize agent
    agent = ContractAdherenceAgent(model="gpt-4o", temperature=0.0)
    
    # Test code
    test_code = """
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
    
    # Check compliance
    result = await agent.ensure_compliance(test_code, "fibonacci_basic")
    
    print(f"Compliant: {result.compliant}")
    print(f"Violations: {len(result.violations)}")
    for violation in result.violations:
        print(f"  - {violation.type.value}: {violation.description}")
    
    if result.transformed_code:
        print("Transformed code available")
        print(result.transformed_code)


if __name__ == "__main__":
    asyncio.run(main())
