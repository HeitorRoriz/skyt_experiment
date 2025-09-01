import os
from .canon import CanonPolicy

METRICS_VERSION = "2025-08-26"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = os.environ.get("SKYT_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.environ.get("SKYT_TEMPERATURE", "0.0"))

# Canonicalization policy
CANON_POLICY = CanonPolicy(
    strip_fences=True,
    strip_docstrings=True,
    strip_comments=True,
    normalize_ws=True,
    format_black=False,
    sort_imports=False,
    ident_normalize=True
)

# Logging configuration
LOG_TO_CSV = True
OUTPUT_DIR_TEMPLATE = "outputs/{mode}_{temperature}"
USE_REFLECTION = False

# Experiment configuration
TARGET_RUNS_PER_PROMPT = 5

# Anchor canonicalization configuration
ANCHOR_MODE = True  # Enable anchor-based canonicalization
DISTANCE_WEIGHTS = {
    "w_struct": 0.4,  # Structural similarity weight
    "w_sem": 0.3,     # Semantic similarity weight  
    "w_effect": 0.2,  # Effect signature weight
    "w_env": 0.1      # Environment weight
}

# Environment enforcement defaults
DEFAULT_ENV_ENFORCEMENT = "off"  # Options: "off", "if_specified", "strict"
ENABLE_BEHAVIORAL_MICROFIX = True  # Enable deterministic micro-repair system
MINIMAL_ENV_KEYS = ["python_version", "platform", "arch"]  # Keys to compare when environment is specified
