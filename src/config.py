import os
METRICS_VERSION = "2025-08-26"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = os.environ.get("SKYT_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.environ.get("SKYT_TEMPERATURE", "0.0"))
