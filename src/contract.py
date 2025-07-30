# src/contract.py

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import json

@dataclass
class PromptContract:
    function_name: str
    language: str
    output_type: str
    constraints: List[str]
    output_format: str
    required_logic: Optional[str] = None   # e.g., "recursion", "use for loop"
    extra_fields: Dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "function_name": self.function_name,
            "language": self.language,
            "output_type": self.output_type,
            "constraints": self.constraints,
            "output_format": self.output_format,
            "required_logic": self.required_logic,
            **self.extra_fields
        }

    @staticmethod
    def from_dict(d):
        known = {k: d.get(k) for k in [
            "function_name", "language", "output_type", "constraints", "output_format", "required_logic"
        ]}
        extra = {k: v for k, v in d.items() if k not in known}
        return PromptContract(**known, extra_fields=extra)

    def to_json(self, path=None):
        js = json.dumps(self.to_dict(), indent=2)
        if path:
            with open(path, 'w') as f:
                f.write(js)
        return js

    @staticmethod
    def from_json(path):
        with open(path) as f:
            d = json.load(f)
        return PromptContract.from_dict(d)
