#!/usr/bin/env python3
"""
Simple Agentic SKYT - Working version with current LangChain API
"""

import asyncio
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# LangChain imports
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# SKYT imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.contract import Contract
from src.oracle_system import OracleSystem
from src.code_transformer import CodeTransformer
from src.canon_system import CanonSystem
from src.foundational_properties import FoundationalProperties

# Path to contracts (relative to main repo)
CONTRACTS_PATH = os.path.join(os.path.dirname(__file__), '..', 'contracts', 'templates.json')


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


class SimpleContractAgent:
    """
    Simplified contract adherence agent without complex LangChain agent setup
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
    
    async def analyze_code_structure(self, code: str) -> Dict[str, Any]:
        """Analyze code structure and identify potential violations"""
        try:
            properties = self.properties_extractor.extract_all_properties(code)
            
            violations = []
            
            # Check for multiple exit points
            exit_points = properties.get("control_flow_signature", {}).get("exit_points", 1)
            if exit_points > 1:
                violations.append(Violation(
                    type=ViolationType.MULTIPLE_EXIT,
                    severity="medium",
                    description=f"Multiple exit points detected ({exit_points})"
                ))
            
            # Check naming conventions
            naming = properties.get("normalized_ast_structure", {}).get("variable_naming", "consistent")
            if naming != "consistent":
                violations.append(Violation(
                    type=ViolationType.NAMING_VIOLATION,
                    severity="low",
                    description="Inconsistent variable naming"
                ))
            
            # Check complexity
            complexity = properties.get("complexity_class", "unknown")
            if complexity in ["high", "very_high"]:
                violations.append(Violation(
                    type=ViolationType.COMPLEXITY_VIOLATION,
                    severity="medium",
                    description=f"High complexity ({complexity})"
                ))
            
            return {
                "violations": violations,
                "properties": properties,
                "analysis": f"Found {len(violations)} structural violations"
            }
            
        except Exception as e:
            return {
                "violations": [Violation(
                    type=ViolationType.STRUCTURAL_VIOLATION,
                    severity="critical",
                    description=f"Analysis failed: {str(e)}"
                )],
                "properties": {},
                "analysis": f"Error analyzing code: {str(e)}"
            }
    
    async def run_oracle_tests(self, code: str, contract_id: str) -> Dict[str, Any]:
        """Run oracle tests to check behavioral compliance"""
        try:
            # Load contract
            contract = Contract.from_template(CONTRACTS_PATH, contract_id)
            
            # Run oracle tests
            result = self.oracle_system.run_oracle_tests(code, contract.data)
            
            if not result.get("passed", False):
                return {
                    "passed": False,
                    "pass_rate": result.get("pass_rate", 0.0),
                    "error": result.get("error", "Unknown error"),
                    "violation": Violation(
                        type=ViolationType.BEHAVIORAL_MISMATCH,
                        severity="critical",
                        description=f"Oracle tests failed: {result.get('error', 'Unknown error')}"
                    )
                }
            else:
                return {
                    "passed": True,
                    "pass_rate": result.get("pass_rate", 0.0),
                    "violation": None
                }
                
        except Exception as e:
            return {
                "passed": False,
                "pass_rate": 0.0,
                "error": str(e),
                "violation": Violation(
                    type=ViolationType.BEHAVIORAL_MISMATCH,
                    severity="critical",
                    description=f"Oracle test error: {str(e)}"
                )
            }
    
    async def calculate_canonical_distance(self, code: str, contract_id: str) -> Dict[str, Any]:
        """Calculate distance to canonical anchor"""
        try:
            # Load canon
            canon_data = self.canon_system.load_canon(contract_id)
            if not canon_data:
                return {
                    "distance": None,
                    "error": f"No canonical anchor found for contract: {contract_id}"
                }
            
            # Calculate distance
            canon_properties = canon_data.get("foundational_properties", {})
            code_properties = self.properties_extractor.extract_all_properties(code)
            distance = self.properties_extractor.calculate_distance(canon_properties, code_properties)
            
            return {
                "distance": distance,
                "threshold": 0.1,
                "compliant": distance <= 0.1,
                "analysis": f"Distance: {distance:.3f} (threshold: 0.1)"
            }
            
        except Exception as e:
            return {
                "distance": None,
                "error": f"Error calculating distance: {str(e)}"
            }
    
    async def transform_to_canonical(self, code: str, contract_id: str) -> Dict[str, Any]:
        """Transform code to match canonical form"""
        try:
            # Load contract
            contract = Contract.from_template(CONTRACTS_PATH, contract_id)
            
            # Transform
            transformer = CodeTransformer(self.canon_system)
            result = transformer.transform_to_canon(code, contract_id, contract=contract.data)
            
            if result["success"]:
                return {
                    "success": True,
                    "transformed_code": result.get("transformed_code"),
                    "final_distance": result.get("final_distance"),
                    "transformations": result.get("transformations_applied", []),
                    "analysis": f"Transformed successfully (final distance: {result['final_distance']:.3f})"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "analysis": f"Transformation failed: {result.get('error', 'Unknown error')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "analysis": f"Error transforming code: {str(e)}"
            }
    
    async def get_ai_suggestion(self, code: str, violations: List[Violation], contract_id: str) -> str:
        """Get AI suggestion for fixing violations"""
        
        violation_text = "\n".join([f"- {v.type.value}: {v.description}" for v in violations])
        
        prompt = f"""I'm analyzing code for contract compliance. Here are the violations found:

{violation_text}

Contract ID: {contract_id}

Please suggest specific fixes for these violations. Focus on:
1. How to fix multiple exit points
2. How to improve naming consistency
3. How to reduce complexity
4. Any other structural improvements needed

Provide concrete code suggestions."""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            return f"AI suggestion failed: {str(e)}"
    
    async def ensure_compliance(self, code: str, contract_id: str) -> ComplianceResult:
        """
        Ensure code adheres to contract specifications
        """
        
        print(f"🔍 Analyzing code for contract: {contract_id}")
        
        # Step 1: Analyze code structure
        structure_result = await self.analyze_code_structure(code)
        violations = structure_result["violations"]
        
        print(f"📊 Found {len(violations)} structural violations")
        
        # Step 2: Run oracle tests
        oracle_result = await self.run_oracle_tests(code, contract_id)
        if oracle_result["violation"]:
            violations.append(oracle_result["violation"])
        
        print(f"🧪 Oracle tests: {'PASS' if oracle_result['passed'] else 'FAIL'}")
        
        # Step 3: Calculate canonical distance
        distance_result = await self.calculate_canonical_distance(code, contract_id)
        if distance_result.get("distance") and distance_result["distance"] > 0.1:
            violations.append(Violation(
                type=ViolationType.STRUCTURAL_VIOLATION,
                severity="medium",
                description=f"Too far from canonical ({distance_result['distance']:.3f})"
            ))
        
        print(f"📏 Canonical distance: {distance_result.get('distance', 'N/A')}")
        
        # Step 4: Get AI suggestions if there are violations
        ai_suggestion = None
        if violations:
            print("🤖 Getting AI suggestions for fixes...")
            ai_suggestion = await self.get_ai_suggestion(code, violations, contract_id)
        
        # Step 5: Attempt transformation if needed
        transformed_code = None
        transformation_success = False
        
        if len([v for v in violations if v.severity in ["medium", "high", "critical"]]) > 0:
            print("🔧 Attempting code transformation...")
            transform_result = await self.transform_to_canonical(code, contract_id)
            if transform_result["success"]:
                transformed_code = transform_result["transformed_code"]
                transformation_success = True
                print(f"✅ Transformation successful")
            else:
                print(f"❌ Transformation failed: {transform_result['error']}")
        
        # Step 6: Calculate final metrics
        metrics = {
            "original_violations": len(violations),
            "oracle_pass_rate": oracle_result.get("pass_rate", 0.0),
            "canonical_distance": distance_result.get("distance"),
            "transformation_attempted": transformed_code is not None,
            "transformation_success": transformation_success,
            "ai_suggestion_provided": ai_suggestion is not None
        }
        
        # Step 7: Determine compliance status
        critical_violations = [v for v in violations if v.severity == "critical"]
        compliant = len(critical_violations) == 0
        
        print(f"✅ Final compliance status: {'COMPLIANT' if compliant else 'NON-COMPLIANT'}")
        
        return ComplianceResult(
            compliant=compliant,
            violations=violations,
            metrics=metrics,
            transformed_code=transformed_code,
            transformation_success=transformation_success
        )


# Test function
async def test_simple_agent():
    """Test the simple contract agent"""
    
    print("🤖 Initializing Simple Contract Agent...")
    agent = SimpleContractAgent(model="gpt-4o", temperature=0.0)
    
    # Test case: Non-compliant fibonacci
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
    
    print("\n🔍 Testing Fibonacci Code")
    print("Code:")
    print(test_code)
    
    result = await agent.ensure_compliance(test_code, "fibonacci_basic")
    
    print(f"\n📊 Results:")
    print(f"✅ Compliant: {result.compliant}")
    print(f"🚨 Violations: {len(result.violations)}")
    
    for violation in result.violations:
        print(f"   • {violation.type.value} ({violation.severity}): {violation.description}")
    
    print(f"\n📈 Metrics:")
    for key, value in result.metrics.items():
        print(f"   • {key}: {value}")
    
    if result.transformed_code:
        print(f"\n🔧 Transformed Code:")
        print(result.transformed_code)


if __name__ == "__main__":
    asyncio.run(test_simple_agent())
