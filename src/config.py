import os

# Core configuration
METRICS_VERSION = "2025-09-26"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = os.environ.get("SKYT_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.environ.get("SKYT_TEMPERATURE", "0.0"))

# Experiment configuration
TARGET_RUNS_PER_PROMPT = 5
OUTPUT_DIR_TEMPLATE = "outputs/{mode}_{temperature}"

# Legacy compatibility (deprecated - use middleware.schema instead)
LOG_TO_CSV = True
USE_REFLECTION = False
