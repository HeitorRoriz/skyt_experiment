# src/config.py
"""
Centralized configuration for SKYT experiment
"""

import os

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = "gpt-4"
DEFAULT_TEMPERATURE = 0.0

# Metrics Version
METRICS_VERSION = "simplified_v1"

# Experiment Settings
NUM_RUNS = 5
RESULTS_DIR = "results"

# Anchor Oracle for Fibonacci 20
FIBONACCI_20_EXPECTED = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181] 