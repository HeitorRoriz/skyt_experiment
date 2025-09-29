import os

# Core configuration
METRICS_VERSION = "2025-09-29"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = os.environ.get("SKYT_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.environ.get("SKYT_TEMPERATURE", "0.0"))

# Experiment configuration
TARGET_RUNS_PER_PROMPT = 5
OUTPUT_DIR_TEMPLATE = "outputs/temp_{temperature}"

# Simplified SKYT - Focus on core metrics
CORE_METRICS = ["R_raw", "R_canon"]
DEFAULT_ALGORITHM = "fibonacci"

# Paths
CONTRACTS_DIR = "contracts"
OUTPUTS_DIR = "outputs"
RESULTS_FILE = "results.csv"
