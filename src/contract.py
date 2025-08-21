# src/contract.py

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import json

@dataclass
class PromptContract:
    function_name: str
    language: str
    output_type: str
    constraints: List[str]
    output_format: str
    required_logic: Optional[str] = None
    variables: Optional[List[Dict[str, Any]]] = None         # [{"name": "sensor_pin", "type": "uint8_t"}, ...]
    method_signature: Optional[str] = None                   # "int read_sensor(uint8_t sensor_pin, uint16_t timeout_ms);"
    allowed_libraries: Optional[List[str]] = None
    disallowed_libraries: Optional[List[str]] = None
    hardware_constraints: Optional[List[str]] = None
    test_cases: Optional[List[Dict[str, Any]]] = None
    docstring_required: Optional[bool] = False
    safety_critical: Optional[bool] = False
    determinism: Optional[Dict[str, Any]] = None
    canonicalization_policy: Optional[Dict[str, Any]] = None
    environment_pin: Optional[str] = None
    decoder_pin: Optional[str] = None
    
    # Enhanced acceptance testing framework
    acceptance_tests: Optional[Dict[str, Any]] = field(default_factory=lambda: {
        "unit_tests": [],           # Basic input/output validation
        "integration_tests": [],    # Function composition and interaction
        "edge_cases": [],          # Boundary conditions and error handling
        "performance_tests": [],   # Time/space complexity validation
        "property_tests": [],      # Mathematical properties and invariants
        "regression_tests": [],    # Previously failing cases
        "stress_tests": []         # Large inputs and extreme conditions
    })
    
    # Test execution configuration
    test_config: Optional[Dict[str, Any]] = field(default_factory=lambda: {
        "timeout_seconds": 5.0,
        "memory_limit_mb": 100,
        "required_pass_rate": 1.0,  # 100% by default
        "allow_approximate": False,
        "tolerance": 1e-9
    })
    
    extra_fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        # asdict drops default_factory fields only if not set; ensure we keep extra_fields
        base = asdict(self)
        # Remove keys with None values for cleaner JSON
        result = {k: v for k, v in base.items() if v is not None and v != []}
        return result

    @staticmethod
    def from_dict(d):
        # Known fields for this contract
        keys = {
            "function_name", "language", "output_type", "constraints", "output_format",
            "required_logic", "variables", "method_signature", "allowed_libraries",
            "disallowed_libraries", "hardware_constraints", "test_cases",
            "docstring_required", "safety_critical", "determinism", "canonicalization_policy",
            "environment_pin", "decoder_pin", "acceptance_tests", "test_config"
        }
        known = {k: d.get(k) for k in keys if k in d}
        extra = {k: v for k, v in d.items() if k not in keys}
        return PromptContract(**known, extra_fields=extra)

    def to_json(self, path=None):
        js = json.dumps(self.to_dict(), indent=2)
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(js)
        return js

    @staticmethod
    def from_json(path):
        with open(path, encoding='utf-8') as f:
            d = json.load(f)
        return PromptContract.from_dict(d)
