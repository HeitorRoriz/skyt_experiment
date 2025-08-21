"""
Test configuration system for A/B/C ablation study
A: No-contract (raw LLM only)
B: Contract-only (contract + lint + canonicalization + repair; no cache)  
C: Full Skyt (B + replay/cache)
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
import json
import hashlib

class TestMode(Enum):
    NO_CONTRACT = "A"  # Raw LLM only
    CONTRACT_ONLY = "B"  # Contract + lint + canonicalization + repair; no cache
    FULL_SKYT = "C"  # B + replay/cache

@dataclass
class EnvironmentConfig:
    """Environment pinning configuration"""
    model_identifier: str
    temperature: float
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    seed: Optional[int] = None
    python_version: str = "3.12"
    black_version: str = "23.12.1"
    isort_version: str = "5.13.2"
    os_info: str = "Windows 11"
    contract_version: str = "1.0"
    canonicalization_policy_version: str = "1.0"
    
    def get_cache_key(self) -> str:
        """Generate cache key for environment fingerprint"""
        env_dict = {
            "model": self.model_identifier,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "seed": self.seed,
            "python": self.python_version,
            "black": self.black_version,
            "isort": self.isort_version,
            "os": self.os_info,
            "contract_v": self.contract_version,
            "canon_v": self.canonicalization_policy_version
        }
        return hashlib.sha256(json.dumps(env_dict, sort_keys=True).encode()).hexdigest()[:16]

@dataclass
class TestConfiguration:
    """Complete test configuration"""
    mode: TestMode
    environment: EnvironmentConfig
    enable_caching: bool
    enable_contracts: bool
    enable_canonicalization: bool
    enable_repair: bool
    enable_replay: bool
    
    @classmethod
    def create_mode_a(cls, env: EnvironmentConfig) -> 'TestConfiguration':
        """No-contract mode: Raw LLM only"""
        return cls(
            mode=TestMode.NO_CONTRACT,
            environment=env,
            enable_caching=False,
            enable_contracts=False,
            enable_canonicalization=False,
            enable_repair=False,
            enable_replay=False
        )
    
    @classmethod
    def create_mode_b(cls, env: EnvironmentConfig) -> 'TestConfiguration':
        """Contract-only mode: contract + lint + canonicalization + repair; no cache"""
        return cls(
            mode=TestMode.CONTRACT_ONLY,
            environment=env,
            enable_caching=False,
            enable_contracts=True,
            enable_canonicalization=True,
            enable_repair=True,
            enable_replay=False
        )
    
    @classmethod
    def create_mode_c(cls, env: EnvironmentConfig) -> 'TestConfiguration':
        """Full Skyt mode: B + replay/cache"""
        return cls(
            mode=TestMode.FULL_SKYT,
            environment=env,
            enable_caching=True,
            enable_contracts=True,
            enable_canonicalization=True,
            enable_repair=True,
            enable_replay=True
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "mode": self.mode.value,
            "environment": {
                "model_identifier": self.environment.model_identifier,
                "temperature": self.environment.temperature,
                "top_p": self.environment.top_p,
                "top_k": self.environment.top_k,
                "seed": self.environment.seed,
                "python_version": self.environment.python_version,
                "black_version": self.environment.black_version,
                "isort_version": self.environment.isort_version,
                "os_info": self.environment.os_info,
                "contract_version": self.environment.contract_version,
                "canonicalization_policy_version": self.environment.canonicalization_policy_version,
                "cache_key": self.environment.get_cache_key()
            },
            "capabilities": {
                "enable_caching": self.enable_caching,
                "enable_contracts": self.enable_contracts,
                "enable_canonicalization": self.enable_canonicalization,
                "enable_repair": self.enable_repair,
                "enable_replay": self.enable_replay
            }
        }
