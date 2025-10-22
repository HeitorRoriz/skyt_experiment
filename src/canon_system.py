# src/canon_system.py
"""
Canon creation and comparison system for SKYT experiments
Manages canonical anchors and distance calculations using foundational properties
"""

import json
import os
from typing import Dict, Any, Optional, List
from .foundational_properties import FoundationalProperties
from .contract import Contract


class CanonSystem:
    """
    Manages canonical anchors and code comparison using foundational properties
    """
    
    def __init__(self, canon_storage_dir: str = "outputs/canon"):
        self.properties_extractor = FoundationalProperties()
        self.canon_storage_dir = canon_storage_dir
        os.makedirs(canon_storage_dir, exist_ok=True)
    
    def create_canon(self, contract: Contract, code: str, 
                    oracle_result: Optional[Dict[str, Any]] = None,
                    require_oracle_pass: bool = True) -> Dict[str, Any]:
        """
        Create canonical anchor from first compliant code output
        
        Args:
            contract: Contract specification
            code: First compliant code output
            oracle_result: Optional oracle test results for validation
            require_oracle_pass: If True, only create canon from oracle-passing code
            
        Returns:
            Canon data with foundational properties
            
        Raises:
            ValueError: If require_oracle_pass is True and code fails oracle
        """
        # CRITICAL: Validate code passes oracle tests before anchoring
        if require_oracle_pass:
            if oracle_result is None:
                raise ValueError("Oracle result required when require_oracle_pass=True")
            
            if not oracle_result.get("passed", False):
                error_msg = oracle_result.get("error", "Unknown error")
                pass_rate = oracle_result.get("pass_rate", 0.0)
                raise ValueError(
                    f"Cannot create canon from failing code. "
                    f"Oracle pass rate: {pass_rate:.1%}. Error: {error_msg}"
                )
        
        # Extract foundational properties
        properties = self.properties_extractor.extract_all_properties(code)
        
        # Create canon data (store contract for variable naming enforcement)
        canon_data = {
            "contract_id": contract.data["id"],
            "canonical_code": code,
            "foundational_properties": properties,
            "contract_data": contract.data,  # Store full contract for variable naming
            "created_timestamp": contract.data.get("created_timestamp"),
            "canon_version": "1.0",
            "oracle_validated": oracle_result is not None and oracle_result.get("passed", False),
            "oracle_pass_rate": oracle_result.get("pass_rate", None) if oracle_result else None
        }
        
        # Set anchor in contract
        contract.set_anchor(code, properties)
        
        # Save canon to disk
        self._save_canon(contract.data["id"], canon_data)
        
        return canon_data
    
    def load_canon(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """
        Load existing canon for a contract
        
        Args:
            contract_id: Contract identifier
            
        Returns:
            Canon data or None if not found
        """
        canon_path = os.path.join(self.canon_storage_dir, f"{contract_id}_canon.json")
        
        if os.path.exists(canon_path):
            with open(canon_path, 'r') as f:
                return json.load(f)
        
        return None
    
    def compare_to_canon(self, contract_id: str, code: str,
                        contract: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Compare code to canonical anchor
        
        Args:
            contract_id: Contract identifier
            code: Code to compare
            contract: Optional contract data for variable naming constraints
            
        Returns:
            Comparison results with distance and property differences
        """
        canon_data = self.load_canon(contract_id)
        
        if not canon_data:
            return {
                "error": "No canon found for contract",
                "distance": 1.0,
                "is_identical": False
            }
        
        # Extract properties from new code
        new_properties = self.properties_extractor.extract_all_properties(code)
        canon_properties = canon_data["foundational_properties"]
        
        # Get contract from canon data if not provided
        if contract is None and "contract_data" in canon_data:
            contract = canon_data["contract_data"]
        
        # Calculate distance (pass contract for variable naming enforcement)
        distance = self.properties_extractor.calculate_distance(
            canon_properties, new_properties, contract
        )
        
        # Check if identical
        is_identical = (distance == 0.0)
        
        # Find property differences
        differences = self._find_property_differences(canon_properties, new_properties)
        
        return {
            "distance": distance,
            "is_identical": is_identical,
            "canon_code": canon_data["canonical_code"],
            "new_code": code,
            "property_differences": differences,
            "canon_properties": canon_properties,
            "new_properties": new_properties
        }
    
    def _save_canon(self, contract_id: str, canon_data: Dict[str, Any]):
        """Save canon data to disk"""
        canon_path = os.path.join(self.canon_storage_dir, f"{contract_id}_canon.json")
        
        with open(canon_path, 'w') as f:
            json.dump(canon_data, f, indent=2)
    
    def _find_property_differences(self, canon_props: Dict[str, Any], 
                                 new_props: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find specific differences between property sets
        
        Args:
            canon_props: Canonical properties
            new_props: New code properties
            
        Returns:
            List of property differences
        """
        differences = []
        
        for prop_name in self.properties_extractor.properties:
            canon_val = canon_props.get(prop_name)
            new_val = new_props.get(prop_name)
            
            if canon_val != new_val:
                prop_distance = self.properties_extractor._calculate_property_distance(
                    canon_val, new_val, prop_name
                )
                
                differences.append({
                    "property": prop_name,
                    "canon_value": canon_val,
                    "new_value": new_val,
                    "distance": prop_distance,
                    "severity": self._classify_difference_severity(prop_distance)
                })
        
        return differences
    
    def _classify_difference_severity(self, distance: float) -> str:
        """Classify difference severity based on distance"""
        if distance == 0.0:
            return "none"
        elif distance < 0.3:
            return "minor"
        elif distance < 0.7:
            return "moderate"
        else:
            return "major"
    
    def get_canon_statistics(self, contract_id: str) -> Dict[str, Any]:
        """
        Get statistics about canon usage
        
        Args:
            contract_id: Contract identifier
            
        Returns:
            Canon usage statistics
        """
        canon_data = self.load_canon(contract_id)
        
        if not canon_data:
            return {"error": "No canon found"}
        
        # Count property types
        properties = canon_data["foundational_properties"]
        property_stats = {}
        
        for prop_name, prop_value in properties.items():
            if prop_value is not None:
                if isinstance(prop_value, dict):
                    property_stats[prop_name] = {
                        "type": "dict",
                        "keys": len(prop_value),
                        "complexity": sum(1 for v in prop_value.values() if v)
                    }
                elif isinstance(prop_value, list):
                    property_stats[prop_name] = {
                        "type": "list", 
                        "length": len(prop_value),
                        "unique_items": len(set(str(item) for item in prop_value))
                    }
                else:
                    property_stats[prop_name] = {
                        "type": type(prop_value).__name__,
                        "value": prop_value
                    }
        
        return {
            "contract_id": contract_id,
            "canon_created": canon_data.get("created_timestamp"),
            "property_statistics": property_stats,
            "total_properties": len([p for p in properties.values() if p is not None])
        }
