# src/__init__.py
"""
SKYT Experiment Package with Middleware Architecture
Core modules: middleware, runners, contract, llm, normalize
"""

__version__ = "2.0.0"

# Import key components for easy access
from . import middleware
from . import runners
from .contract import create_prompt_contract, load_contract_from_template
from .llm import query_llm
from .normalize import extract_code
