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
    hardware_constraints: Optional[Dict[str, Any]] = None    # {"pin": "GPIO17", "max_latency_us": 100}
    test_cases: Optional[List[Dict[str, Any]]] = None        # [{"input": {...}, "expected_output": ...}]
    docstring_required: Optional[bool] = None
    safety_critical: Optional[bool] = None
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
            "docstring_required", "safety_critical"
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
