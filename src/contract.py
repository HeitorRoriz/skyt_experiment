# src/contract.py
"""
Comprehensive contract system for SKYT experiments
Implements full contract specification with all required properties
"""

from typing import Dict, Any, Optional, List
import json
import hashlib
from datetime import datetime


class Contract:
    """
    Comprehensive contract specification for SKYT experiments
    Encodes task intent, constraints, oracle requirements, and repeatability anchoring
    """
    
    def __init__(self, contract_data: Dict[str, Any]):
        self.data = contract_data
        self.validate()
    
    @classmethod
    def from_template(cls, template_path: str, contract_id: str) -> 'Contract':
        """Create contract from JSON template"""
        with open(template_path, 'r') as f:
            templates = json.load(f)
        
        if contract_id not in templates:
            raise ValueError(f"Contract template '{contract_id}' not found")
        
        template = templates[contract_id]
        
        # Build full contract from template
        contract_data = {
            # Core Properties
            "id": contract_id,
            "task_intent": template.get("task_intent", template.get("description", "")),
            "prompt": template["prompt"],
            "constraints": template.get("constraints", {}),
            "algorithm_family": template.get("algorithm_family", "fibonacci"),
            "language": template.get("language", "python"),
            "environment": template.get("environment", {}),
            "output_format": template.get("output_format", "raw_code"),
            "oracle_requirements": template.get("oracle_requirements", {}),
            "normalization_rules": template.get("normalization_rules", {}),
            
            # Repeatability-anchoring Properties
            "anchor_signature": None,  # Set when first compliant output is found
            "compliance_flag": False,
            "distance_metric": "foundational_properties",
            "rescue_bounds": template.get("rescue_bounds", {}),
            
            # Meta Properties
            "model_specification": template.get("model_specification", {}),
            "contract_version": "2.0",
            "oracle_version": "1.0",
            "normalization_version": "1.0",
            "created_timestamp": datetime.now().isoformat(),
            "run_id": None,
            "prompt_id": contract_id,
            "sample_id": None
        }
        
        return cls(contract_data)
    
    def validate(self):
        """Validate contract has required properties"""
        required_fields = [
            "id", "task_intent", "prompt", "language", 
            "contract_version", "created_timestamp"
        ]
        
        for field in required_fields:
            if field not in self.data:
                raise ValueError(f"Contract missing required field: {field}")
    
    def set_anchor(self, canonical_code: str, foundational_properties: Dict[str, Any]):
        """Set the canonical anchor for this contract"""
        # Create signature from foundational properties
        properties_str = json.dumps(foundational_properties, sort_keys=True)
        self.data["anchor_signature"] = hashlib.sha256(properties_str.encode()).hexdigest()
        self.data["canonical_code"] = canonical_code
        self.data["foundational_properties"] = foundational_properties
        self.data["compliance_flag"] = True
    
    def get_oracle_tests(self) -> List[Dict[str, Any]]:
        """Get oracle test cases for this contract"""
        return self.data.get("oracle_requirements", {}).get("test_cases", [])
    
    def get_constraints(self) -> Dict[str, Any]:
        """Get contract constraints"""
        return self.data.get("constraints", {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert contract to dictionary"""
        return self.data.copy()
    
    def save(self, filepath: str):
        """Save contract to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.data, f, indent=2)


def validate_contract(contract: Dict[str, Any]) -> bool:
    """
    Validate contract specification
    
    Args:
        contract: Contract dict to validate
    
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["id", "prompt"]
    
    for field in required_fields:
        if field not in contract:
            return False
    
    return True


def is_environment_required(contract: Dict[str, Any]) -> bool:
    """
    Check if environment enforcement is required for this contract
    
    Args:
        contract: Contract specification
    
    Returns:
        True if environment checking is required
    """
    env_enforcement = contract.get("env_enforcement", "off")
    return env_enforcement in ["if_specified", "strict"] and "environment" in contract


def get_contract_environment(contract: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Retrieve environment specification from contract
    
    Args:
        contract: Contract specification
    
    Returns:
        Environment dict or None if not specified
    """
    return contract.get("environment")


def get_env_enforcement_mode(contract: Dict[str, Any]) -> str:
    """
    Get environment enforcement mode from contract
    
    Args:
        contract: Contract specification
    
    Returns:
        Enforcement mode: "off", "if_specified", or "strict"
    """
    return contract.get("env_enforcement", "off")
